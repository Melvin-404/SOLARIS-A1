"""Model-driven real-time and batch inference engine for SOLARIS-A1.

Loads the trained champion model, training-fitted preprocessor, and calibration parameters.
Strictly ensures zero feature leakage and consistent scaling between training and inference.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union
import joblib
import numpy as np
import pandas as pd

from solar_flare.paths import project_root
from solar_flare.features.registry import FeatureRegistry

logger = logging.getLogger("solaris_a1.inference")

_DEFAULT_PIPELINE: Optional[InferencePipeline] = None


def classify_risk(prob: float) -> str:
    """Classify flare risk into standardized operational space-weather tiers.
    
    Tiers:
    - LOW: prob < 0.20 (Quiet Sun / background conditions)
    - MODERATE: 0.20 <= prob < 0.50 (Elevated flux variance, pre-flare warning)
    - HIGH: 0.50 <= prob < 0.80 (Active flaring probable within horizon)
    - SEVERE: prob >= 0.80 (Major flare underway or imminent)
    """
    if prob < 0.20:
        return "LOW"
    elif prob < 0.50:
        return "MODERATE"
    elif prob < 0.80:
        return "HIGH"
    else:
        return "SEVERE"


def estimate_flare_class(peak_counts: float = 0.0, is_flare: bool = False) -> str:
    """Return explicit unavailable indicator for flare classification.
    
    SOLARIS-A1 champion models are strictly binary detectors (Task A: flare presence
    within a 60-second observation window). Multi-class flare categorization (C-, M-,
    or X-class) is NOT evaluated or supported by these binary estimators.
    """
    return "NOT_EVALUATED_BINARY_DETECTOR_ONLY"


@dataclass(frozen=True)
class ExperimentProfile:
    """Specification of a trained and frozen experiment profile."""
    profile_id: str
    experiment_id: str
    display_name: str
    dataset_cohort: str
    protocol_id: str
    task: str
    governance_status: str
    is_default: bool
    production_ready: bool
    evaluation_window: str
    description: str
    limitations: str
    false_alarm_rate_summary: Dict[str, Any]


EXPERIMENT_PROFILES: Dict[str, ExperimentProfile] = {
    "pilot_20261018": ExperimentProfile(
        profile_id="pilot_20261018",
        experiment_id="exp_PROTO_STAGE10_PILOT_001_20261023_141429",
        display_name="October 2026 Pilot Baseline (Decision D-15)",
        dataset_cohort="pilot_october2026",
        protocol_id="training_protocol.yaml",
        task="window_flare_detection",
        governance_status="PILOT_FROZEN",
        is_default=True,
        production_ready=False,
        evaluation_window="2026-10-18 (single observation orbit)",
        description="Original pilot experiment trained on single-orbit SoLEXS observation from 2026-10-18.",
        limitations="Trained and evaluated on limited single-day observation; not representative of varied solar cycle dynamics; research baseline only.",
        false_alarm_rate_summary={
            "xgboost": {"window_fp_per_hour": 0.0, "episodes_fp_per_hour": 0.0, "exposure_hours": 3.75},
            "random_forest": {"window_fp_per_hour": 0.0, "episodes_fp_per_hour": 0.0, "exposure_hours": 3.75},
            "logistic_regression": {"window_fp_per_hour": 0.0, "episodes_fp_per_hour": 0.0, "exposure_hours": 3.75},
        },
    ),
    "expanded_july2024": ExperimentProfile(
        profile_id="expanded_july2024",
        experiment_id="exp_PROTO_STAGE10_EXPANDED_002_20261023_162431",
        display_name="July 2024 Expanded Benchmark (Gate G7/G8)",
        dataset_cohort="july2024_benchmark",
        protocol_id="training_protocol_july2024.yaml",
        task="window_flare_detection",
        governance_status="BENCHMARK_FROZEN",
        is_default=False,
        production_ready=False,
        evaluation_window="July 13–14, 2024 (15,872 windows; 44.77 science hours)",
        description="Expanded multi-orbit benchmark trained on July 1–12 and evaluated on held-out July 13–14.",
        limitations=(
            "Held-out test set covers strictly July 13–14, 2024; dominated by active region AR3738; "
            "contains only a single X-class event (X1.2 at 02:34 UTC); high false alarm rate under active solar conditions "
            "(XGBoost: 118.85 window FP/hr; 2.97 macro episodes/hr); does not generalize to all solar cycle conditions."
        ),
        false_alarm_rate_summary={
            "xgboost": {"window_fp_per_hour": 118.85, "episodes_fp_per_hour": 2.97, "exposure_hours": 44.77},
            "random_forest": {"window_fp_per_hour": 55.13, "episodes_fp_per_hour": 1.03, "exposure_hours": 44.77},
            "logistic_regression": {"window_fp_per_hour": 43.74, "episodes_fp_per_hour": 0.96, "exposure_hours": 44.77},
        },
    ),
    "expanded_2024_2026": ExperimentProfile(
        profile_id="expanded_2024_2026",
        experiment_id="exp_PROTO_STAGE16_EXPANDED_2024_2026",
        display_name="Multi-Year Expanded Cohort (2024–2026)",
        dataset_cohort="multi_year_2024_2026",
        protocol_id="training_protocol_stage16.yaml",
        task="window_flare_detection",
        governance_status="EXPERIMENTAL_MULTI_YEAR",
        is_default=False,
        production_ready=False,
        evaluation_window="2024–2026 Multi-Year Archive",
        description="Expanded multi-year experiment integrating 2024 observations and October 2026 pilot.",
        limitations="Experimental research cohort; evaluation under active investigation.",
        false_alarm_rate_summary={
            "xgboost": {"window_fp_per_hour": 0.0, "episodes_fp_per_hour": 0.0, "exposure_hours": 0.0},
        },
    ),
}

PROFILE_ALIASES: Dict[str, str] = {
    "pilot": "pilot_20261018",
    "pilot_20261018": "pilot_20261018",
    "default": "pilot_20261018",
    "october2026": "pilot_20261018",
    "exp_PROTO_STAGE10_PILOT_001_20261023_141429": "pilot_20261018",
    "july2024": "expanded_july2024",
    "expanded_july2024": "expanded_july2024",
    "expanded": "expanded_july2024",
    "benchmark": "expanded_july2024",
    "exp_PROTO_STAGE10_EXPANDED_002_20261023_162431": "expanded_july2024",
    "multi_year": "expanded_2024_2026",
    "expanded_2024_2026": "expanded_2024_2026",
    "stage16": "expanded_2024_2026",
    "exp_PROTO_STAGE16_EXPANDED_2024_2026": "expanded_2024_2026",
}

DEFAULT_PROFILE_ID = "pilot_20261018"


class InferencePipeline:
    """Production inference pipeline connecting trained models to live UI and API."""

    def __init__(
        self,
        experiment_id: Optional[str] = None,
        model_name: str = "xgboost",
        experiments_root: Optional[Union[Path, str]] = None,
    ) -> None:
        root = project_root()
        base_exp = Path(experiments_root) if experiments_root else (root / "results" / "experiments")

        # Resolve experiment profile strictly without filesystem modification-time sorting
        self.profile: Optional[ExperimentProfile] = None
        target_exp_id: str

        if experiment_id is None:
            # The October 2026 pilot MUST remain the default profile
            self.profile = EXPERIMENT_PROFILES[DEFAULT_PROFILE_ID]
            target_exp_id = self.profile.experiment_id
        elif experiment_id in PROFILE_ALIASES:
            canon_profile = PROFILE_ALIASES[experiment_id]
            self.profile = EXPERIMENT_PROFILES[canon_profile]
            target_exp_id = self.profile.experiment_id
        else:
            # Custom explicit experiment directory
            target_exp_id = experiment_id

        exp_dir = base_exp / target_exp_id
        if not exp_dir.is_dir():
            raise FileNotFoundError(
                f"Experiment directory '{target_exp_id}' not found in {base_exp}. "
                f"Available profiles: {list(EXPERIMENT_PROFILES.keys())}"
            )

        self.exp_dir = exp_dir
        self.exp_id = exp_dir.name
        self.model_name = model_name

        # Load preprocessor
        preproc_path = exp_dir / "preprocessor.joblib"
        if not preproc_path.is_file():
            raise FileNotFoundError(f"Preprocessor artifact not found at {preproc_path}")
        self.preprocessor = joblib.load(preproc_path)
        if isinstance(self.preprocessor, dict):
            self.expected_features: List[str] = list(self.preprocessor.get("feature_names", []))
        else:
            self.expected_features: List[str] = list(getattr(self.preprocessor, "feature_names_in_", []))

        # Load model artifact
        models_dir = exp_dir / "models"
        model_path = models_dir / f"{model_name}.joblib"
        if not model_path.is_file():
            # Try alternate fallback to xgboost or first available joblib
            candidates = list(models_dir.glob("*.joblib"))
            if not candidates:
                raise FileNotFoundError(f"No model artifacts found in {models_dir}")
            model_path = candidates[0]
            self.model_name = model_path.stem

        self.model = joblib.load(model_path)
        logger.info("Loaded model '%s' from %s", self.model_name, model_path)

        # Load manifest and metadata
        self.manifest: Dict[str, Any] = {}
        manifest_file = models_dir / "model_manifest.json"
        if manifest_file.is_file():
            try:
                self.manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            except Exception:
                self.manifest = {}

        # Load metrics if available
        self.metrics_df: Optional[pd.DataFrame] = None
        metrics_file = exp_dir / "evaluation" / "metrics.csv"
        if metrics_file.is_file():
            try:
                self.metrics_df = pd.read_csv(metrics_file)
            except Exception:
                self.metrics_df = None

        self.feature_registry = FeatureRegistry()
        self.history: List[Dict[str, Any]] = []

    @property
    def version_info(self) -> Dict[str, Any]:
        """Return model metadata and version dictionary."""
        return {
            "experiment_id": self.exp_id,
            "profile_id": self.profile.profile_id if self.profile else "custom",
            "model_name": self.model_name,
            "model_class": self.model.__class__.__name__,
            "model_version": f"{self.model_name}@{self.exp_id}",
            "features_count": len(self.expected_features),
            "expected_features": self.expected_features,
            "scaler": (
                self.preprocessor.get("scaler").__class__.__name__
                if isinstance(self.preprocessor, dict) and self.preprocessor.get("scaler")
                else getattr(self.preprocessor, "scaler_name", "StandardScaler")
            ),
            "imputer": (
                self.preprocessor.get("imputer").__class__.__name__
                if isinstance(self.preprocessor, dict) and self.preprocessor.get("imputer")
                else getattr(self.preprocessor, "imputer_name", "median")
            ),
            "evaluated": self.metrics_df is not None,
            "task": "window_flare_detection",
            "window_duration_seconds": 60.0,
            "forecast_horizon_seconds": None,
            "dataset_cohort": self.profile.dataset_cohort if self.profile else "custom",
            "governance_status": self.profile.governance_status if self.profile else "UNREGISTERED",
            "is_default": self.profile.is_default if self.profile else False,
            "production_ready": False,
            "limitations": self.profile.limitations if self.profile else "Unregistered experiment run.",
            "operational_advisory": (
                "RESEARCH BENCHMARK: Task A 60-second window flare detection. "
                "Not calibrated for operational real-time space-weather alerting or mission-critical spacecraft protection."
            ),
        }

    def _prepare_dataframe(self, X: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]) -> pd.DataFrame:
        """Convert and align input into a DataFrame matching expected training features."""
        if isinstance(X, dict):
            df = pd.DataFrame([X])
        elif isinstance(X, list):
            df = pd.DataFrame(X)
        elif isinstance(X, pd.DataFrame):
            df = X.copy()
        else:
            raise ValueError(f"Input must be DataFrame, dict, or list of dicts, got {type(X)}")

        # Check missing features
        missing_cols = set(self.expected_features) - set(df.columns)
        if missing_cols:
            # If some engineered features are missing, fill with NaN so imputer handles them
            for col in missing_cols:
                df[col] = np.nan

        # Align column order strictly to expected features
        return df[self.expected_features]

    def predict_proba(self, X: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]) -> np.ndarray:
        """Compute flaring probability for input features."""
        df_aligned = self._prepare_dataframe(X)
        if isinstance(self.preprocessor, dict):
            imputer = self.preprocessor.get("imputer")
            scaler = self.preprocessor.get("scaler")
            arr = imputer.transform(df_aligned.values) if imputer is not None else df_aligned.values
            df_trans = scaler.transform(arr) if scaler is not None else arr
        else:
            df_trans = self.preprocessor.transform(df_aligned)

        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(df_trans)[:, 1]
        elif hasattr(self.model, "decision_function"):
            df_scores = self.model.decision_function(df_trans)
            probs = 1.0 / (1.0 + np.exp(-df_scores))
        else:
            probs = self.model.predict(df_trans).astype(float)

        return np.clip(probs, 0.0, 1.0)

    def predict(
        self,
        X: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]],
        threshold: float = 0.50,
        observation_timestamp: Optional[str] = None,
        record_history: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generate structured solar flare prediction results."""
        df_aligned = self._prepare_dataframe(X)
        probs = self.predict_proba(df_aligned)

        results: List[Dict[str, Any]] = []
        ts_now = datetime.now(timezone.utc).isoformat()

        for idx, p in enumerate(probs):
            prob = float(p)
            is_flare = bool(prob >= threshold)
            risk = classify_risk(prob)
            b_margin = round(abs(prob - 0.5) * 2.0, 4)

            # Check if observation epoch was provided in feature row
            row_obs_ts = observation_timestamp
            if row_obs_ts is None and isinstance(X, dict):
                row_obs_ts = X.get("window_start") or X.get("timestamp") or X.get("epoch")
                if row_obs_ts is not None:
                    row_obs_ts = str(row_obs_ts)

            res = {
                "flare_detected": is_flare,
                "flare_probability": round(prob, 4),
                "boundary_margin": b_margin,
                "confidence": b_margin,  # DEPRECATED: backwards compatibility alias
                "risk_level": risk,
                "expected_flare_class": "NOT_EVALUATED_BINARY_DETECTOR_ONLY",
                "threshold_used": threshold,
                "window_duration_seconds": 60.0,
                "forecast_horizon_seconds": None,  # DEPRECATED: Task A detection only
                "inference_timestamp_utc": ts_now,
                "observation_timestamp_utc": row_obs_ts,
                "prediction_timestamp_utc": ts_now,  # DEPRECATED: backwards compatibility alias
                "model_version": f"{self.model_name}@{self.exp_id}",
                "experiment_id": self.exp_id,
                "profile": self.profile.profile_id if self.profile else "custom",
                "dataset_cohort": self.profile.dataset_cohort if self.profile else "custom",
                "task": "window_flare_detection",
                "production_ready": False,
                "advisory": (
                    "RESEARCH BENCHMARK: Task A 60-second window flare detection. "
                    "Uncalibrated raw model output score. Not certified for operational space-weather alerting."
                ),
            }
            results.append(res)
            if record_history:
                self.history.append(res)
                # Keep latest 100 in memory
                if len(self.history) > 100:
                    self.history = self.history[-100:]

        return results

    def predict_from_counts(
        self,
        counts: Sequence[float],
        times: Optional[Sequence[float]] = None,
        baseline_value: Optional[float] = None,
        threshold: float = 0.50,
    ) -> Dict[str, Any]:
        """Compute window features dynamically from raw count observations and predict."""
        c_arr = np.asarray(counts, dtype=np.float64)
        t_arr = np.asarray(times, dtype=np.float64) if times is not None else np.arange(len(c_arr), dtype=np.float64)

        if len(c_arr) == 0:
            raise ValueError("Count array cannot be empty")

        obs_ts: Optional[str] = None
        if times is not None and len(times) > 0:
            obs_ts = str(times[0])

        # Causal baseline estimation if not supplied
        base_val = baseline_value if baseline_value is not None else float(np.median(c_arr[:max(1, len(c_arr) // 2)]))
        base_val = max(1e-6, base_val)

        # Extract features dictionary matching exact training schema
        from solar_flare.features.registry import compute_features
        feat_dict, _ = compute_features(
            window_values=c_arr,
            window_times=t_arr,
            baseline_value=base_val,
            n_expected_samples=60,
            rolling_trend_k=15.0,
            percentile_levels=(5, 25, 75, 95),
        )

        res = self.predict(feat_dict, threshold=threshold, observation_timestamp=obs_ts)[0]
        res["extracted_features"] = {k: round(v, 4) if isinstance(v, float) else v for k, v in feat_dict.items()}
        return res

    def get_metrics_table(self) -> pd.DataFrame:
        """Return the held-out test evaluation metrics table."""
        if self.metrics_df is not None:
            return self.metrics_df
        return pd.DataFrame()


_PIPELINE_CACHE: Dict[str, InferencePipeline] = {}


def get_pipeline(
    profile_or_id: Optional[str] = None,
    model_name: str = "xgboost",
    experiments_root: Optional[Union[Path, str]] = None,
    *,
    profile_id: Optional[str] = None,
) -> InferencePipeline:
    """Retrieve or initialize a cached pipeline for an explicit experiment profile and model."""
    global _PIPELINE_CACHE
    prof_key = profile_id or profile_or_id or DEFAULT_PROFILE_ID
    cache_key = f"{prof_key}:{model_name}:{experiments_root or ''}"
    if cache_key not in _PIPELINE_CACHE:
        _PIPELINE_CACHE[cache_key] = InferencePipeline(
            experiment_id=prof_key,
            model_name=model_name,
            experiments_root=experiments_root,
        )
    return _PIPELINE_CACHE[cache_key]


def get_default_pipeline() -> InferencePipeline:
    """Singleton getter for default production inference pipeline (strictly the October 2026 pilot)."""
    return get_pipeline(DEFAULT_PROFILE_ID, "xgboost")
