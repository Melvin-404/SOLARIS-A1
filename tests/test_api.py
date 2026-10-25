"""Unit and integration tests for SOLARIS-A1 FastAPI service."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from solar_flare.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that the API root endpoint returns operational metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert "active_model" in data
    assert "endpoints" in data


def test_health_endpoint():
    """Verify that the health-check endpoint reports model readiness."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "xgboost" in data["model_name"]
    assert data["model_version"] == "xgboost@exp_PROTO_STAGE10_PILOT_001_20261023_141429"


def test_model_info_endpoint():
    """Verify that the model metadata endpoint returns features and training config."""
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert data["feature_count"] == 19
    assert "mean" in data["expected_features"]
    assert "temporal_slope" in data["expected_features"]
    assert data["decision_d15_status"] == "PILOT"
    assert data["forecast_horizon_seconds"] is None
    assert data["window_duration_seconds"] == 60.0
    assert data["model_version"] == "xgboost@exp_PROTO_STAGE10_PILOT_001_20261023_141429"


def test_predict_from_features():
    """Verify single-window prediction using pre-computed feature dictionary."""
    features = {
        "mean": 14.7,
        "std": 15.6,
        "min": 10.0,
        "max": 80.0,
        "median": 10.0,
        "iqr": 0.0,
        "p05": 10.0,
        "p25": 10.0,
        "p75": 10.0,
        "p95": 53.0,
        "temporal_slope": 0.47,
        "rolling_trend": 4.28,
        "mean_abs_first_difference": 1.85,
        "max_abs_first_difference": 35.0,
        "coverage_fraction": 1.0,
        "n_observed_samples": 60,
        "baseline_value": 10.0,
        "peak_to_baseline_ratio": 8.0,
        "robust_variability": 0.0,
    }
    response = client.post("/predict", json={"features": features, "threshold": 0.50})
    assert response.status_code == 200
    data = response.json()
    assert "flare_detected" in data
    assert "flare_probability" in data
    assert 0.0 <= data["flare_probability"] <= 1.0
    assert data["risk_level"] in {"LOW", "MODERATE", "HIGH", "SEVERE"}
    assert "boundary_margin" in data
    assert "confidence" in data  # deprecated alias
    assert data["forecast_horizon_seconds"] is None
    assert data["window_duration_seconds"] == 60.0
    assert data["expected_flare_class"] == "NOT_EVALUATED_BINARY_DETECTOR_ONLY"
    assert "inference_timestamp_utc" in data
    assert data["model_version"] == "xgboost@exp_PROTO_STAGE10_PILOT_001_20261023_141429"


def test_predict_from_counts_quiet_sun():
    """Verify prediction on a quiet-Sun count rate profile."""
    counts = [9.0] * 60
    response = client.post("/predict", json={"counts": counts, "threshold": 0.50})
    assert response.status_code == 200
    data = response.json()
    assert data["flare_detected"] is False
    assert data["flare_probability"] < 0.20
    assert data["risk_level"] == "LOW"
    assert data["expected_flare_class"] == "NOT_EVALUATED_BINARY_DETECTOR_ONLY"


def test_predict_from_counts_flare_burst():
    """Verify prediction on an impulsive solar flare burst profile."""
    counts = [10.0] * 50 + [35.0, 50.0, 75.0, 80.0, 60.0, 45.0, 30.0, 20.0, 15.0, 10.0]
    response = client.post("/predict", json={"counts": counts, "threshold": 0.50})
    assert response.status_code == 200
    data = response.json()
    assert data["flare_detected"] is True
    assert data["flare_probability"] >= 0.50
    assert data["risk_level"] in {"HIGH", "SEVERE"}
    assert data["expected_flare_class"] == "NOT_EVALUATED_BINARY_DETECTOR_ONLY"


def test_predict_batch():
    """Verify batch prediction over multiple windows."""
    w1 = {"mean": 9.0, "max": 9.0, "min": 9.0, "std": 0.0, "median": 9.0, "coverage_fraction": 1.0}
    w2 = {"mean": 35.0, "max": 80.0, "min": 10.0, "std": 20.0, "median": 25.0, "coverage_fraction": 1.0}
    response = client.post("/predict/batch", json={"windows": [w1, w2], "threshold": 0.50})
    assert response.status_code == 200
    data = response.json()
    assert data["total_evaluated"] == 2
    assert len(data["predictions"]) == 2


def test_predict_timeseries():
    """Verify sliding-window prediction over a continuous light-curve segment."""
    counts = [9.0] * 80 + [40.0, 60.0, 80.0, 70.0, 50.0] + [10.0] * 40
    response = client.post("/predict/timeseries", json={
        "counts": counts,
        "window_length": 60,
        "stride": 10,
        "threshold": 0.50,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_windows"] > 0
    assert "timeline" in data
    assert len(data["timeline"]) == data["total_windows"]


def test_held_out_metrics_endpoint():
    """Verify retrieval of the held-out test evaluation metrics table."""
    response = client.get("/metrics/heldout")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    model_names = [row["model_name"] for row in data]
    assert "xgboost" in model_names
    assert "logistic_regression" in model_names


def test_predict_empty_raises_400():
    """Verify that submitting an empty request returns 400 Bad Request."""
    response = client.post("/predict", json={})
    assert response.status_code == 400
    assert "Either 'features' dictionary or 'counts' list must be provided" in response.json()["detail"]


def test_predict_short_counts_raises_400():
    """Verify that submitting fewer than 10 samples returns 400 Bad Request."""
    response = client.post("/predict", json={"counts": [1.0, 2.0, 3.0]})
    assert response.status_code == 400
    assert "at least 10 samples" in response.json()["detail"]
