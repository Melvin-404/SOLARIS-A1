"""Unit tests for SOLARIS-A1 model inference engine."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from solar_flare.inference.pipeline import (
    InferencePipeline,
    get_default_pipeline,
    classify_risk,
    estimate_flare_class,
)


def test_pipeline_initialization():
    """Verify that the default pipeline initializes with the champion model."""
    pipe = get_default_pipeline()
    info = pipe.version_info
    assert info["model_name"] == "xgboost"
    assert info["features_count"] == 19
    assert info["scaler"] == "StandardScaler"
    assert info["imputer"] == "median"
    assert info["evaluated"] is True


def test_classify_risk_boundaries():
    """Verify operational risk tier boundaries."""
    assert classify_risk(0.0) == "LOW"
    assert classify_risk(0.199) == "LOW"
    assert classify_risk(0.20) == "MODERATE"
    assert classify_risk(0.499) == "MODERATE"
    assert classify_risk(0.50) == "HIGH"
    assert classify_risk(0.799) == "HIGH"
    assert classify_risk(0.80) == "SEVERE"
    assert classify_risk(1.0) == "SEVERE"


def test_estimate_flare_class():
    """Verify physical flare class returns explicit unavailable status for binary model."""
    assert estimate_flare_class(50.0, is_flare=False) == "NOT_EVALUATED_BINARY_DETECTOR_ONLY"
    assert estimate_flare_class(85.0, is_flare=True) == "NOT_EVALUATED_BINARY_DETECTOR_ONLY"


def test_predict_proba_bounds():
    """Verify that output probabilities are strictly bounded in [0.0, 1.0]."""
    pipe = get_default_pipeline()
    sample = {f: 10.0 for f in pipe.expected_features}
    probs = pipe.predict_proba(sample)
    assert len(probs) == 1
    assert 0.0 <= probs[0] <= 1.0


def test_predict_structured_output():
    """Verify structured output fields of single window prediction."""
    pipe = get_default_pipeline()
    sample = {f: 10.0 for f in pipe.expected_features}
    res = pipe.predict(sample, threshold=0.50)[0]

    assert "flare_detected" in res
    assert "flare_probability" in res
    assert "boundary_margin" in res
    assert "confidence" in res  # deprecated alias
    assert "risk_level" in res
    assert res["expected_flare_class"] == "NOT_EVALUATED_BINARY_DETECTOR_ONLY"
    assert res["forecast_horizon_seconds"] is None
    assert res["window_duration_seconds"] == 60.0
    assert "inference_timestamp_utc" in res
    assert res["model_version"] == "xgboost@exp_PROTO_STAGE10_PILOT_001_20261023_141429"


def test_predict_from_counts():
    """Verify prediction directly from raw count rate sequence."""
    pipe = get_default_pipeline()
    counts = [10.0] * 50 + [40.0, 60.0, 80.0, 70.0, 50.0]
    res = pipe.predict_from_counts(counts=counts, threshold=0.50)

    assert res["flare_detected"] is True
    assert res["flare_probability"] > 0.50
    assert "extracted_features" in res
    assert "mean" in res["extracted_features"]
    assert "max" in res["extracted_features"]


def test_pipeline_handles_partial_features():
    """Verify that input with partial features is imputed by the training-fitted imputer without error."""
    pipe = get_default_pipeline()
    partial = {"mean": 15.0, "max": 60.0}
    probs = pipe.predict_proba(partial)
    assert len(probs) == 1
    assert 0.0 <= probs[0] <= 1.0


def test_pipeline_prediction_history():
    """Verify that predictions are logged to in-memory history."""
    pipe = get_default_pipeline()
    initial_len = len(pipe.history)
    pipe.predict({f: 10.0 for f in pipe.expected_features}, record_history=True)
    assert len(pipe.history) == initial_len + 1
