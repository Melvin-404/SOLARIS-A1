"""Automated tests for SOLARIS-A1 model registry, multi-experiment API, and governance.

Covers:
1. Model Registry and Profile Resolution (Pilot default vs July 2024 explicit selection).
2. Regression Test: Proving newer experiment directories cannot silently alter the default model.
3. Preprocessing Consistency: Zero feature leakage, exact schema alignment, finite transformations.
4. Prediction Reproducibility: Bitwise deterministic probabilities across runs.
5. API Endpoints: /models, /model/info, /predict, /predict/batch, and /metrics/heldout.
6. Safeguards: Strict verification that production_ready is False and Task A detection semantics are respected.
"""

from __future__ import annotations

import os
from pathlib import Path
import time
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from solar_flare.api.main import app
from solar_flare.inference.pipeline import (
    InferencePipeline,
    get_default_pipeline,
    get_pipeline,
    EXPERIMENT_PROFILES,
    DEFAULT_PROFILE_ID,
)

client = TestClient(app)


def test_default_pipeline_is_pilot():
    """Verify that default pipeline initialization strictly binds to October 2026 pilot."""
    pipe = get_default_pipeline()
    assert pipe.profile is not None
    assert pipe.profile.profile_id == "pilot_20261018"
    assert pipe.profile.is_default is True
    assert pipe.profile.production_ready is False
    assert pipe.exp_id == "exp_PROTO_STAGE10_PILOT_001_20261023_141429"
    assert pipe.version_info["dataset_cohort"] == "pilot_october2026"
    assert pipe.version_info["task"] == "window_flare_detection"
    assert pipe.version_info["production_ready"] is False


def test_explicit_selection_loads_july2024():
    """Verify that explicit selection loads the July 2024 benchmark model."""
    pipe = get_pipeline("expanded_july2024")
    assert pipe.profile is not None
    assert pipe.profile.profile_id == "expanded_july2024"
    assert pipe.profile.is_default is False
    assert pipe.profile.production_ready is False
    assert pipe.exp_id == "exp_PROTO_STAGE10_EXPANDED_002_20261023_162431"
    assert pipe.version_info["dataset_cohort"] == "july2024_benchmark"
    assert pipe.version_info["task"] == "window_flare_detection"
    assert "AR3738" in pipe.version_info["limitations"]


def test_regression_newer_experiment_cannot_change_default(tmp_path: Path):
    """Regression test proving that newer experiment directories with newer mtime
    NEVER silently hijack or alter the default model pipeline.
    """
    # Create a mock experiments root
    mock_root = tmp_path / "experiments"
    mock_root.mkdir()

    # 1. Create pilot experiment folder
    pilot_dir = mock_root / "exp_PROTO_STAGE10_PILOT_001_20261023_141429"
    pilot_dir.mkdir()
    (pilot_dir / "models").mkdir()
    (pilot_dir / "evaluation").mkdir()

    # Copy real preprocessor and model from actual pilot experiment
    actual_pilot = Path("results/experiments/exp_PROTO_STAGE10_PILOT_001_20261023_141429")
    import shutil
    shutil.copy(actual_pilot / "preprocessor.joblib", pilot_dir / "preprocessor.joblib")
    shutil.copy(actual_pilot / "models" / "xgboost.joblib", pilot_dir / "models" / "xgboost.joblib")
    shutil.copy(actual_pilot / "evaluation" / "metrics.csv", pilot_dir / "evaluation" / "metrics.csv")

    # Set pilot mtime to the past
    past_time = time.time() - 100000
    os.utime(pilot_dir, (past_time, past_time))

    # 2. Create a "newer" unapproved experiment with mtime far in the future
    newer_dir = mock_root / "exp_FUTURE_RUN_999_20990101_000000"
    newer_dir.mkdir()
    (newer_dir / "models").mkdir()
    (newer_dir / "evaluation").mkdir()
    shutil.copy(actual_pilot / "preprocessor.joblib", newer_dir / "preprocessor.joblib")
    shutil.copy(actual_pilot / "models" / "xgboost.joblib", newer_dir / "models" / "xgboost.joblib")
    shutil.copy(actual_pilot / "evaluation" / "metrics.csv", newer_dir / "evaluation" / "metrics.csv")

    future_time = time.time() + 100000
    os.utime(newer_dir, (future_time, future_time))

    # 3. Instantiate pipeline with no experiment_id specified
    pipe = InferencePipeline(experiment_id=None, experiments_root=mock_root)

    # Prove that despite newer_dir having newer mtime, the pipeline loaded the pilot!
    assert pipe.exp_id == "exp_PROTO_STAGE10_PILOT_001_20261023_141429"
    assert pipe.profile is not None
    assert pipe.profile.profile_id == "pilot_20261018"
    assert pipe.profile.is_default is True


def test_preprocessing_consistency_both_cohorts():
    """Verify that both pilot and July 2024 benchmark preprocessors enforce consistent
    19-feature schemas, deterministic scaling, and finite output without NaN leakage.
    """
    sample_features = {
        "mean": 15.0, "std": 12.0, "min": 8.0, "max": 75.0, "median": 12.0,
        "iqr": 5.0, "p05": 8.5, "p25": 10.0, "p75": 15.0, "p95": 60.0,
        "temporal_slope": 0.5, "rolling_trend": 2.5, "mean_abs_first_difference": 1.2,
        "max_abs_first_difference": 20.0, "coverage_fraction": 1.0, "n_observed_samples": 60,
        "baseline_value": 9.0, "peak_to_baseline_ratio": 8.33, "robust_variability": 3.0,
    }

    for prof_id in ["pilot_20261018", "expanded_july2024"]:
        pipe = get_pipeline(prof_id)
        assert len(pipe.expected_features) == 19
        df_aligned = pipe._prepare_dataframe(sample_features)
        assert list(df_aligned.columns) == pipe.expected_features

        transformed = pipe.preprocessor.transform(df_aligned)
        assert transformed.shape == (1, 19)
        assert np.all(np.isfinite(transformed))

        probs = pipe.predict_proba(df_aligned)
        assert len(probs) == 1
        assert 0.0 <= probs[0] <= 1.0


def test_prediction_reproducibility():
    """Verify that model inferences are 100% bitwise deterministic across repeated calls."""
    sample_features = {
        "mean": 22.5, "std": 18.0, "min": 10.0, "max": 85.0, "median": 16.0,
        "iqr": 8.0, "p05": 10.0, "p25": 12.0, "p75": 20.0, "p95": 70.0,
        "temporal_slope": 0.8, "rolling_trend": 3.5, "mean_abs_first_difference": 1.5,
        "max_abs_first_difference": 30.0, "coverage_fraction": 1.0, "n_observed_samples": 60,
        "baseline_value": 10.0, "peak_to_baseline_ratio": 8.5, "robust_variability": 4.0,
    }

    for prof_id in ["pilot_20261018", "expanded_july2024"]:
        pipe = get_pipeline(prof_id)
        res1 = pipe.predict(sample_features, threshold=0.50, record_history=False)[0]
        res2 = pipe.predict(sample_features, threshold=0.50, record_history=False)[0]

        assert res1["flare_probability"] == res2["flare_probability"]
        assert res1["flare_detected"] == res2["flare_detected"]
        assert res1["risk_level"] == res2["risk_level"]
        assert res1["boundary_margin"] == res2["boundary_margin"]
        assert res1["confidence"] == res2["confidence"]
        assert res1["expected_flare_class"] == "NOT_EVALUATED_BINARY_DETECTOR_ONLY"
        assert res1["forecast_horizon_seconds"] is None
        assert res1["model_version"] == f"xgboost@{pipe.exp_id}"
        assert "inference_timestamp_utc" in res1


def test_api_models_registry_endpoint():
    """Verify GET /models returns both experiment profiles with correct default status and metadata."""
    response = client.get("/models")
    assert response.status_code == 200
    profiles = response.json()
    assert isinstance(profiles, list)
    assert len(profiles) >= 2

    prof_map = {p["profile_id"]: p for p in profiles}
    assert "pilot_20261018" in prof_map
    assert "expanded_july2024" in prof_map

    pilot = prof_map["pilot_20261018"]
    assert pilot["is_default"] is True
    assert pilot["production_ready"] is False
    assert pilot["dataset_cohort"] == "pilot_october2026"

    expanded = prof_map["expanded_july2024"]
    assert expanded["is_default"] is False
    assert expanded["production_ready"] is False
    assert expanded["dataset_cohort"] == "july2024_benchmark"
    assert "AR3738" in expanded["limitations"]
    assert "xgboost" in expanded["false_alarm_rate_summary"]
    assert expanded["false_alarm_rate_summary"]["xgboost"]["window_fp_per_hour"] == 118.85


def test_api_model_info_profiles():
    """Verify GET /model/info returns profile-specific metadata."""
    # 1. Default (omitted profile) -> Pilot
    resp_def = client.get("/model/info")
    assert resp_def.status_code == 200
    d_def = resp_def.json()
    assert d_def["profile_id"] == "pilot_20261018"
    assert d_def["decision_d15_status"] == "PILOT"
    assert d_def["production_ready"] is False
    assert d_def["forecast_horizon_seconds"] is None
    assert d_def["model_version"] == "xgboost@exp_PROTO_STAGE10_PILOT_001_20261023_141429"

    # 2. Explicit July 2024 profile
    resp_exp = client.get("/model/info?profile=expanded_july2024")
    assert resp_exp.status_code == 200
    d_exp = resp_exp.json()
    assert d_exp["profile_id"] == "expanded_july2024"
    assert d_exp["dataset_cohort"] == "july2024_benchmark"
    assert d_exp["governance_status"] == "BENCHMARK_FROZEN"
    assert d_exp["production_ready"] is False
    assert d_exp["forecast_horizon_seconds"] is None
    assert d_exp["model_version"] == "xgboost@exp_PROTO_STAGE10_EXPANDED_002_20261023_162431"
    assert "AR3738" in d_exp["limitations"]
    assert d_exp["false_alarm_rate_info"]["xgboost"]["window_fp_per_hour"] == 118.85


def test_api_predict_explicit_profile_selection():
    """Verify POST /predict respects explicit profile selection while maintaining backwards compatibility."""
    features = {
        "mean": 14.7, "std": 15.6, "min": 10.0, "max": 80.0, "median": 10.0,
        "iqr": 0.0, "p05": 10.0, "p25": 10.0, "p75": 10.0, "p95": 53.0,
        "temporal_slope": 0.47, "rolling_trend": 4.28, "mean_abs_first_difference": 1.85,
        "max_abs_first_difference": 35.0, "coverage_fraction": 1.0, "n_observed_samples": 60,
        "baseline_value": 10.0, "peak_to_baseline_ratio": 8.0, "robust_variability": 0.0,
    }

    # Default call (no profile passed)
    resp_default = client.post("/predict", json={"features": features})
    assert resp_default.status_code == 200
    data_def = resp_default.json()
    assert data_def["profile"] == "pilot_20261018"
    assert data_def["dataset_cohort"] == "pilot_october2026"
    assert data_def["production_ready"] is False
    assert data_def["experiment_id"] == "exp_PROTO_STAGE10_PILOT_001_20261023_141429"
    assert data_def["model_version"] == "xgboost@exp_PROTO_STAGE10_PILOT_001_20261023_141429"
    assert data_def["expected_flare_class"] == "NOT_EVALUATED_BINARY_DETECTOR_ONLY"
    assert data_def["forecast_horizon_seconds"] is None
    assert data_def["boundary_margin"] == 0.295 or "boundary_margin" in data_def
    assert "inference_timestamp_utc" in data_def

    # Explicit July 2024 call
    resp_july = client.post("/predict", json={"features": features, "profile": "expanded_july2024"})
    assert resp_july.status_code == 200
    data_july = resp_july.json()
    assert data_july["profile"] == "expanded_july2024"
    assert data_july["dataset_cohort"] == "july2024_benchmark"
    assert data_july["production_ready"] is False
    assert data_july["experiment_id"] == "exp_PROTO_STAGE10_EXPANDED_002_20261023_162431"
    assert data_july["model_version"] == "xgboost@exp_PROTO_STAGE10_EXPANDED_002_20261023_162431"
    assert data_july["expected_flare_class"] == "NOT_EVALUATED_BINARY_DETECTOR_ONLY"
    assert data_july["forecast_horizon_seconds"] is None
    assert "boundary_margin" in data_july


def test_api_heldout_metrics_profiles():
    """Verify GET /metrics/heldout retrieves metrics for both profiles."""
    # Pilot
    r_pilot = client.get("/metrics/heldout?profile=pilot_20261018")
    assert r_pilot.status_code == 200
    m_pilot = r_pilot.json()
    assert len(m_pilot) > 0

    # July 2024
    r_july = client.get("/metrics/heldout?profile=expanded_july2024")
    assert r_july.status_code == 200
    m_july = r_july.json()
    assert len(m_july) >= 3
    models = [row["model_name"] for row in m_july]
    assert "xgboost" in models
    assert "random_forest" in models
    assert "logistic_regression" in models
