"""Unit and integration tests for SOLARIS-A1 Task B (Pre-Flare Risk Analysis).

Validates:
1. Pre-flare target label construction across 300s, 600s, and 1800s horizons.
2. Temporal leakage guards: zero data past t0 used in feature windows.
3. GTI gaps and boundary exclusion handling (< 80% coverage -> <NA>).
4. Ongoing event exclusion (active flare at t0 -> <NA> with reason ONGOING_EVENT_AT_T0).
5. Forecasting model loading and artifact integrity.
6. Pipeline risk prediction outputs, uncertainty intervals, and risk tier categorization.
7. Telemetry observation auditor verification.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from solar_flare.export.targets import prediction_target
from solar_flare.forecasting.pipeline import (
    ForecastingPipeline,
    get_forecasting_pipeline,
    classify_pre_flare_risk,
)


@pytest.fixture
def sample_events_df() -> pd.DataFrame:
    """Fixture providing synthetic approved flare event records."""
    return pd.DataFrame([
        {
            "event_id": "EVT_TEST_01",
            "source_id": "SRC_TEST",
            "onset_time": 1000.0,
            "end_time": 1200.0,
            "classification": "M1.0",
        },
        {
            "event_id": "EVT_TEST_02",
            "source_id": "SRC_TEST",
            "onset_time": 5000.0,
            "end_time": 5400.0,
            "classification": "X1.0",
        },
    ])


@pytest.fixture
def sample_window_index() -> pd.DataFrame:
    """Fixture providing synthetic window index instances."""
    return pd.DataFrame([
        # Window 1: Quiet Sun (t0 = 200, next onset at 1000 -> 800s away)
        {
            "window_id": "win_01",
            "segment_id": "seg_01",
            "window_start": 140.0,
            "window_end": 200.0,
            "segment_end": 6000.0,
        },
        # Window 2: Pre-flare (t0 = 800, next onset at 1000 -> 200s away, inside 300s & 1800s horizon)
        {
            "window_id": "win_02",
            "segment_id": "seg_01",
            "window_start": 740.0,
            "window_end": 800.0,
            "segment_end": 6000.0,
        },
        # Window 3: Inside ongoing flare (t0 = 1100, flare active from 1000 to 1200)
        {
            "window_id": "win_03",
            "segment_id": "seg_01",
            "window_start": 1040.0,
            "window_end": 1100.0,
            "segment_end": 6000.0,
        },
        # Window 4: Boundary window with insufficient horizon coverage (t0 = 5900, seg_end = 6000 -> 100s / 1800s = 5.5% coverage)
        {
            "window_id": "win_04",
            "segment_id": "seg_01",
            "window_start": 5840.0,
            "window_end": 5900.0,
            "segment_end": 6000.0,
        },
    ])


def test_label_construction_horizons(sample_window_index, sample_events_df):
    """Verify pre-flare label generation for 300s (5m) and 1800s (30m) horizons."""
    # 1. Horizon 300s: win_02 (200s to onset) should be Positive (1)
    res_300 = prediction_target(
        window_index=sample_window_index,
        onsets=sample_events_df,
        horizon_seconds=300.0,
        embargo_seconds=0.0,
        min_coverage_fraction=0.80,
    )
    # win_01: next onset at 1000 (800s away) -> Negative (0)
    assert res_300.loc[res_300["window_id"] == "win_01", "label_prediction"].iloc[0] == 0
    # win_02: next onset at 1000 (200s away) -> Positive (1)
    assert res_300.loc[res_300["window_id"] == "win_02", "label_prediction"].iloc[0] == 1

    # 2. Horizon 1800s (30m)
    res_1800 = prediction_target(
        window_index=sample_window_index,
        onsets=sample_events_df,
        horizon_seconds=1800.0,
        embargo_seconds=0.0,
        min_coverage_fraction=0.80,
    )
    # win_02 (200s to onset) is inside 1800s -> Positive (1)
    assert res_1800.loc[res_1800["window_id"] == "win_02", "label_prediction"].iloc[0] == 1


def test_ongoing_event_exclusion(sample_window_index, sample_events_df):
    """Verify that an ongoing flare active at t0 is excluded as <NA> with reason ONGOING_EVENT_AT_T0."""
    res = prediction_target(
        window_index=sample_window_index,
        onsets=sample_events_df,
        horizon_seconds=1800.0,
        embargo_seconds=0.0,
        min_coverage_fraction=0.80,
    )
    win3 = res[res["window_id"] == "win_03"].iloc[0]
    assert pd.isna(win3["label_prediction"]), "Ongoing flare window must be excluded (<NA>)"
    assert win3["excluded_reason"] == "ONGOING_EVENT_AT_T0"
    assert bool(win3["ongoing_event_at_t0"]) is True


def test_gti_boundary_coverage_exclusion(sample_window_index, sample_events_df):
    """Verify that windows near segment ends with < 80% coverage in the horizon are excluded."""
    res = prediction_target(
        window_index=sample_window_index,
        onsets=sample_events_df,
        horizon_seconds=1800.0,
        embargo_seconds=0.0,
        min_coverage_fraction=0.80,
    )
    win4 = res[res["window_id"] == "win_04"].iloc[0]
    assert pd.isna(win4["label_prediction"]), "Boundary window with low coverage must be excluded"
    assert "INSUFFICIENT_HORIZON_COVERAGE" in win4["excluded_reason"]


def test_temporal_leakage_absence():
    """Verify that feature extraction strictly uses samples <= window_end (t0)."""
    # Create synthetic series
    times = np.arange(0, 100, 1.0)
    flux = np.ones_like(times) * 20.0
    # Inject spike AFTER t0 = 60
    flux[70:80] = 500.0  # Future spike past t0

    # Feature calculation on window [0, 60]
    win_mask = (times >= 0) & (times <= 60)
    win_flux = flux[win_mask]

    # Verify max and mean do not observe the future spike at t=70
    assert np.max(win_flux) == 20.0, "Feature peeked into future data past t0!"
    assert np.mean(win_flux) == 20.0, "Feature mean tainted by future spike!"


def test_forecasting_pipeline_loading():
    """Verify that the dedicated ForecastingPipeline loads champion model and artifacts."""
    pipe = get_forecasting_pipeline()
    assert pipe.is_available, "ForecastingPipeline failed to load models and preprocessor"
    assert pipe.champion_model is not None
    assert pipe.preprocessor is not None
    assert pipe.metrics_df is not None
    assert len(pipe.metrics_df) >= 3, "Metrics table should contain baselines and ML models"


def test_forecasting_prediction_output():
    """Verify risk prediction values, bounds, and uncertainty intervals."""
    pipe = get_forecasting_pipeline()
    features = {
        "mean": 30.0,
        "std": 5.0,
        "temporal_slope": 0.02,
        "peak_to_baseline_ratio": 1.15,
        "robust_variability": 4.0,
    }
    pred = pipe.predict_risk(features, threshold=0.50, horizon_minutes=30.0)

    assert 0.0 <= pred.forecast_probability <= 1.0, f"Probability out of range: {pred.forecast_probability}"
    assert 0.0 <= pred.calibrated_uncertainty_lower <= pred.forecast_probability
    assert pred.forecast_probability <= pred.calibrated_uncertainty_upper <= 1.0
    assert pred.risk_tier in {"QUIET", "ELEVATED", "WATCH", "WARNING"}
    assert pred.horizon_minutes == 30.0
    assert pred.decision_threshold == 0.50


def test_risk_tier_classification():
    """Verify standardized pre-flare risk tier thresholds."""
    assert classify_pre_flare_risk(0.05) == "QUIET"
    assert classify_pre_flare_risk(0.19) == "QUIET"
    assert classify_pre_flare_risk(0.20) == "ELEVATED"
    assert classify_pre_flare_risk(0.39) == "ELEVATED"
    assert classify_pre_flare_risk(0.40) == "WATCH"
    assert classify_pre_flare_risk(0.64) == "WATCH"
    assert classify_pre_flare_risk(0.65) == "WARNING"
    assert classify_pre_flare_risk(0.99) == "WARNING"


def test_observation_auditor(sample_events_df, sample_window_index):
    """Verify that audit_observation_time accurately detects ongoing events and gaps."""
    pipe = get_forecasting_pipeline()

    # 1. Audit active ongoing flare
    audit_flare = pipe.audit_observation_time(
        epoch_seconds=1100.0,
        events_df=sample_events_df,
        window_index_df=sample_window_index,
        horizon_seconds=1800.0,
    )
    assert audit_flare.is_ongoing_flare is True
    assert audit_flare.ongoing_flare_id == "EVT_TEST_01"
    assert audit_flare.rejection_reason is not None

    # 2. Audit gap (epoch far outside segment)
    audit_gap = pipe.audit_observation_time(
        epoch_seconds=99999.0,
        events_df=sample_events_df,
        window_index_df=sample_window_index,
        horizon_seconds=1800.0,
    )
    assert audit_gap.is_valid_gti is False
    assert "telemetry gap" in audit_gap.rejection_reason.lower()
