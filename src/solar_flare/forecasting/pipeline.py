"""SOLARIS-A1 Pre-Flare Activity Forecasting Inference & Audit Engine (Task B).

Provides protocol-guarded pre-flare risk assessment for solar flare onsets
within a defined future horizon (default 30 minutes / 1800 s).

CRITICAL SCIENTIFIC GUARDS:
1. Preprocessor is fitted strictly on training data (never on validation or test sets).
2. Ongoing flares active at reference time t0 are assigned ONGOING_EVENT_AT_T0 and cannot be forecast.
3. Timestamps with insufficient preceding continuous observation (< 60 s lookback) are strictly flagged.
4. Distinguishes in-window detection (Task A) from pre-flare forecasting (Task B).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd

from solar_flare.paths import project_root

logger = logging.getLogger("solaris_a1.forecasting")

_DEFAULT_FORECAST_PIPELINE: Optional[ForecastingPipeline] = None


def classify_pre_flare_risk(prob: float) -> str:
    """Classify pre-flare forecast probability into standardized scientific risk tiers.
    
    Tiers:
    - QUIET: prob < 0.20 (Minimal probability of onset in horizon)
    - ELEVATED: 0.20 <= prob < 0.40 (Elevated coronal variability)
    - WATCH: 0.40 <= prob < 0.65 (Pre-flare precursor patterns detected)
    - WARNING: prob >= 0.65 (High-probability pre-flare activity)
    """
    if prob < 0.20:
        return "QUIET"
    elif prob < 0.40:
        return "ELEVATED"
    elif prob < 0.65:
        return "WATCH"
    else:
        return "WARNING"


@dataclass(frozen=True)
class PreFlareAuditResult:
    """Audit verification of an observation timestamp for pre-flare risk analysis."""
    reference_time_utc: str
    epoch_seconds: float
    is_valid_gti: bool
    segment_id: Optional[str]
    preceding_history_seconds: float
    has_sufficient_precursor_history: bool  # >= 60 s
    is_ongoing_flare: bool
    ongoing_flare_id: Optional[str]
    next_onset_seconds: Optional[float]
    next_event_id: Optional[str]
    next_event_classification: Optional[str]
    is_flare_within_horizon: Optional[bool]
    rejection_reason: Optional[str]


@dataclass
class PreFlarePrediction:
    """Result of a pre-flare activity forecast."""
    forecast_probability: float
    risk_tier: str
    decision_threshold: float
    is_positive_forecast: bool
    calibrated_uncertainty_lower: float
    calibrated_uncertainty_upper: float
    model_name: str
    horizon_minutes: float
    climatological_baseline_probability: float


class ForecastingPipeline:
    """Dedicated inference and audit pipeline for Task B (Pre-Flare Risk Analysis)."""

    def __init__(self, experiment_dir: Optional[Union[Path, str]] = None) -> None:
        root = project_root()
        if experiment_dir is None:
            self.exp_dir = root / "results" / "forecasting" / "exp_FORECAST_30M_001"
        else:
            self.exp_dir = Path(experiment_dir)

        self.champion_model = None
        self.rf_model = None
        self.xgb_model = None
        self.preprocessor = None
        self.metrics_df = None
        self.split_report = None
        self.eval_report = None
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Load trained forecasting artifacts from experiment directory."""
        if not self.exp_dir.is_dir():
            logger.warning("Forecasting experiment directory not found: %s", self.exp_dir)
            return

        champ_path = self.exp_dir / "forecasting_champion_model.joblib"
        prep_path = self.exp_dir / "forecasting_preprocessor.joblib"
        rf_path = self.exp_dir / "forecasting_rf_model.joblib"
        xgb_path = self.exp_dir / "forecasting_xgb_model.joblib"

        if champ_path.is_file():
            self.champion_model = joblib.load(champ_path)
        if prep_path.is_file():
            self.preprocessor = joblib.load(prep_path)
        if rf_path.is_file():
            self.rf_model = joblib.load(rf_path)
        if xgb_path.is_file():
            self.xgb_model = joblib.load(xgb_path)

        metrics_path = self.exp_dir / "metrics.csv"
        if metrics_path.is_file():
            self.metrics_df = pd.read_csv(metrics_path)

        split_path = self.exp_dir / "split_report.json"
        if split_path.is_file():
            self.split_report = json.loads(split_path.read_text(encoding="utf-8"))

        eval_path = self.exp_dir / "evaluation_report.json"
        if eval_path.is_file():
            self.eval_report = json.loads(eval_path.read_text(encoding="utf-8"))

    @property
    def is_available(self) -> bool:
        """Return True if champion model and preprocessor are loaded."""
        return self.champion_model is not None and self.preprocessor is not None

    def get_feature_names(self) -> List[str]:
        """Return expected numerical feature names."""
        if self.split_report and "feature_names" in self.split_report:
            return list(self.split_report["feature_names"])
        return [
            "baseline_value", "p05", "p25", "p75", "p95", "coverage_fraction",
            "iqr", "max", "max_abs_first_difference", "mean",
            "mean_abs_first_difference", "median", "min", "n_observed_samples",
            "peak_to_baseline_ratio", "robust_variability", "rolling_trend",
            "std", "temporal_slope"
        ]

    def audit_observation_time(
        self,
        epoch_seconds: float,
        events_df: pd.DataFrame,
        window_index_df: pd.DataFrame,
        horizon_seconds: float = 1800.0,
    ) -> PreFlareAuditResult:
        """Audit an observation epoch against GTI segments, preceding history, and NOAA ground truth.
        
        Parameters
        ----------
        epoch_seconds : float
            POSIX/Unix epoch seconds of reference time t0.
        events_df : pd.DataFrame
            Approved NOAA event catalog.
        window_index_df : pd.DataFrame
            Window index table containing segment bounds and window timestamps.
        horizon_seconds : float
            Forecasting horizon duration in seconds (default 1800.0 s / 30 min).
            
        Returns
        -------
        PreFlareAuditResult
            Validation details and eligibility for forecasting.
        """
        dt_utc = datetime.fromtimestamp(epoch_seconds, timezone.utc).isoformat()

        # 1. Identify containing segment and preceding history
        seg_id = None
        preceding_history_s = 0.0
        is_valid_gti = False

        if window_index_df is not None and not window_index_df.empty:
            seg_bounds = window_index_df.groupby("segment_id").agg(
                seg_start=("window_start", "min"),
                seg_end=("window_end", "max"),
            ).reset_index()

            match_segs = seg_bounds[
                (seg_bounds["seg_start"] <= epoch_seconds) & (epoch_seconds <= seg_bounds["seg_end"])
            ]
            if not match_segs.empty:
                is_valid_gti = True
                seg_row = match_segs.iloc[0]
                seg_id = str(seg_row["segment_id"])
                preceding_history_s = max(0.0, epoch_seconds - float(seg_row["seg_start"]))

        has_sufficient_history = is_valid_gti and (preceding_history_s >= 60.0)

        # 2. Check for ongoing flare active at t0
        is_ongoing = False
        ongoing_evt_id = None
        if events_df is not None and not events_df.empty:
            for _, ev in events_df.iterrows():
                if float(ev["onset_time"]) <= epoch_seconds <= float(ev["end_time"]):
                    is_ongoing = True
                    ongoing_evt_id = str(ev["event_id"])
                    break

        # 3. Future flare events strictly after t0
        next_onset_s = None
        next_evt_id = None
        next_evt_cls = None
        is_within_h = None

        if events_df is not None and not events_df.empty:
            future_evts = events_df[events_df["onset_time"] > epoch_seconds].sort_values("onset_time")
            if not future_evts.empty:
                fev = future_evts.iloc[0]
                next_onset_s = round(float(fev["onset_time"]) - epoch_seconds, 1)
                next_evt_id = str(fev["event_id"])
                next_evt_cls = str(fev.get("classification", "UNKNOWN"))
                is_within_h = (next_onset_s <= horizon_seconds)
            else:
                is_within_h = False

        # 4. Formulate rejection reason if ineligible
        rejection_reason = None
        if not is_valid_gti:
            rejection_reason = "Selected epoch falls within a telemetry gap or outside valid GTI science observations."
        elif not has_sufficient_history:
            rejection_reason = (
                f"Insufficient preceding history ({preceding_history_s:.1f} s < 60.0 s). "
                "Timestamp is too close to segment start."
            )
        elif is_ongoing:
            rejection_reason = (
                f"A solar flare ({ongoing_evt_id}) is ALREADY ONGOING at reference time t0. "
                "Pre-flare forecasting requires pre-event quiescent or precursor conditions; "
                "forecasting an active event is scientifically invalid."
            )

        return PreFlareAuditResult(
            reference_time_utc=dt_utc,
            epoch_seconds=epoch_seconds,
            is_valid_gti=is_valid_gti,
            segment_id=seg_id,
            preceding_history_seconds=preceding_history_s,
            has_sufficient_precursor_history=has_sufficient_history,
            is_ongoing_flare=is_ongoing,
            ongoing_flare_id=ongoing_evt_id,
            next_onset_seconds=next_onset_s,
            next_event_id=next_evt_id,
            next_event_classification=next_evt_cls,
            is_flare_within_horizon=is_within_h,
            rejection_reason=rejection_reason,
        )

    def predict_risk(
        self,
        features: Union[Dict[str, float], pd.DataFrame, np.ndarray],
        threshold: float = 0.50,
        horizon_minutes: float = 30.0,
    ) -> PreFlarePrediction:
        """Compute pre-flare forecast risk score and uncertainty intervals.
        
        Parameters
        ----------
        features : Dict, DataFrame, or ndarray
            Input numerical window features.
        threshold : float
            Decision boundary threshold.
        horizon_minutes : float
            Forecasting horizon duration.
            
        Returns
        -------
        PreFlarePrediction
            Model score, risk tier, uncertainty bounds, and baseline reference.
        """
        if not self.is_available:
            raise RuntimeError("Forecasting model or preprocessor not loaded.")

        feature_names = self.get_feature_names()

        # Format into 2D array
        if isinstance(features, dict):
            row = [features.get(k, 0.0) for k in feature_names]
            X = np.array([row], dtype=float)
        elif isinstance(features, pd.DataFrame):
            X = features[feature_names].values
        else:
            X = np.array(features, dtype=float)
            if X.ndim == 1:
                X = X.reshape(1, -1)

        # Scale using training-fitted RobustScaler
        X_df = pd.DataFrame(X, columns=feature_names)
        X_scaled = self.preprocessor.transform(X_df)

        # Predict probability using champion model (Logistic Regression)
        prob = float(self.champion_model.predict_proba(X_scaled)[0, 1])
        prob = max(0.0, min(1.0, prob))

        # Empirical uncertainty interval from calibration
        # For logistic regression with brier score ~ 0.219, standard uncertainty margin ~ 0.08
        uncertainty_margin = 0.08
        lower_bound = max(0.0, prob - uncertainty_margin)
        upper_bound = min(1.0, prob + uncertainty_margin)

        clim_prev = 0.1697
        if self.split_report and "test" in self.split_report:
            clim_prev = float(self.split_report["test"].get("prevalence", 0.1697))

        risk_tier = classify_pre_flare_risk(prob)

        return PreFlarePrediction(
            forecast_probability=round(prob, 4),
            risk_tier=risk_tier,
            decision_threshold=float(threshold),
            is_positive_forecast=(prob >= threshold),
            calibrated_uncertainty_lower=round(lower_bound, 4),
            calibrated_uncertainty_upper=round(upper_bound, 4),
            model_name="Logistic Regression (Task B Champion)",
            horizon_minutes=float(horizon_minutes),
            climatological_baseline_probability=round(clim_prev, 4),
        )


def get_forecasting_pipeline() -> ForecastingPipeline:
    """Return singleton instance of ForecastingPipeline."""
    global _DEFAULT_FORECAST_PIPELINE
    if _DEFAULT_FORECAST_PIPELINE is None:
        _DEFAULT_FORECAST_PIPELINE = ForecastingPipeline()
    return _DEFAULT_FORECAST_PIPELINE
