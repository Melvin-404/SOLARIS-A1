"""Tests for target generation (Task A detection and Task B prediction).

Validates:
- prediction_target refuses under DRAFT forecasting policy
- Onset in (t0, t0+H] gives positive label (1)
- Clean horizon gives verified negative label (0)
- Onset in embargo before t0 excludes (NA)
- Ongoing event at t0 handled per policy (NA if EXCLUDE)
- Insufficient horizon coverage gives NA with reason
"""

from __future__ import annotations

from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import yaml

from solar_flare.export.targets import prediction_target, assert_forecasting_approved, ForecastingNotApprovedError


@pytest.fixture
def synthetic_approved_forecasting_setup(tmp_path: Path):
    """Create approved forecasting policy and decisions in tmp_path."""
    policy_file = tmp_path / "22_forecasting_policy.md"
    policy_file.write_text(
        "# Forecasting Policy\n\nStatus: APPROVED by Researcher, date 2026-10-21\n",
        encoding="utf-8",
    )

    decisions_file = tmp_path / "decisions.yaml"
    decisions_data = {
        "decisions": {
            "D-07": {"status": "APPROVED", "value": 1800.0},
            "D-08": {"status": "APPROVED", "value": 300.0},
        }
    }
    with open(decisions_file, "w", encoding="utf-8") as f:
        yaml.dump(decisions_data, f)

    return policy_file, decisions_file


def test_prediction_target_refuses_under_draft(tmp_path: Path):
    """Verify that prediction_target refuses to run if forecasting policy is DRAFT or missing."""
    draft_policy = tmp_path / "22_forecasting_policy.md"
    draft_policy.write_text("Status: DRAFT — PENDING GATE G6\n", encoding="utf-8")

    win_df = pd.DataFrame([{"window_id": "win_01", "window_end": 1000.0}])
    onsets_df = pd.DataFrame(columns=["event_id", "onset_time", "end_time"])

    with pytest.raises(ForecastingNotApprovedError):
        prediction_target(
            window_index=win_df,
            onsets=onsets_df,
            horizon_seconds=1800.0,
            embargo_seconds=300.0,
            policy_path=draft_policy,
        )


def test_prediction_target_positive_onset_in_horizon(synthetic_approved_forecasting_setup):
    """Verify that an onset falling in (t0, t0 + H] produces label 1."""
    p_file, d_file = synthetic_approved_forecasting_setup

    # Window reference time t0 = 1000.0s. Horizon H = 1800s -> (1000.0, 2800.0]
    win_df = pd.DataFrame([
        {"window_id": "win_pred_pos", "window_end": 1000.0, "segment_end": 5000.0}
    ])

    # Event onset at 1500.0s (within (1000, 2800])
    events_df = pd.DataFrame([
        {"event_id": "EV_FUTURE", "onset_time": 1500.0, "end_time": 1900.0}
    ])

    res = prediction_target(
        window_index=win_df,
        onsets=events_df,
        horizon_seconds=1800.0,
        embargo_seconds=300.0,
        policy_path=p_file,
        decisions_path=d_file,
    )

    assert len(res) == 1
    row = res.iloc[0]
    assert row["label_prediction"] == 1
    assert row["next_onset_time"] == 1500.0
    assert row["seconds_to_next_onset"] == 500.0
    assert row["excluded_reason"] is None


def test_prediction_target_negative_clean_horizon(synthetic_approved_forecasting_setup):
    """Verify that a clean horizon with no onsets produces label 0."""
    p_file, d_file = synthetic_approved_forecasting_setup

    win_df = pd.DataFrame([
        {"window_id": "win_pred_neg", "window_end": 1000.0, "segment_end": 5000.0}
    ])

    # Flare onset is at 4000.0s (far beyond horizon 2800.0s)
    events_df = pd.DataFrame([
        {"event_id": "EV_FAR", "onset_time": 4000.0, "end_time": 4500.0}
    ])

    res = prediction_target(
        window_index=win_df,
        onsets=events_df,
        horizon_seconds=1800.0,
        embargo_seconds=300.0,
        policy_path=p_file,
        decisions_path=d_file,
    )

    assert len(res) == 1
    row = res.iloc[0]
    assert row["label_prediction"] == 0
    assert row["next_onset_time"] == 4000.0
    assert row["seconds_to_next_onset"] == 3000.0
    assert row["excluded_reason"] is None


def test_prediction_target_embargo_exclusion(synthetic_approved_forecasting_setup):
    """Verify that an onset within pre-window embargo (t0 - embargo, t0] excludes the window."""
    p_file, d_file = synthetic_approved_forecasting_setup

    # Window t0 = 1000.0, embargo = 300s -> interval (700, 1000]
    win_df = pd.DataFrame([
        {"window_id": "win_pred_emb", "window_end": 1000.0, "segment_end": 5000.0}
    ])

    # Event onset occurred at 850.0s (in embargo)
    events_df = pd.DataFrame([
        {"event_id": "EV_RECENT", "onset_time": 850.0, "end_time": 950.0}
    ])

    res = prediction_target(
        window_index=win_df,
        onsets=events_df,
        horizon_seconds=1800.0,
        embargo_seconds=300.0,
        policy_path=p_file,
        decisions_path=d_file,
    )

    assert len(res) == 1
    row = res.iloc[0]
    assert pd.isna(row["label_prediction"])
    assert row["excluded_reason"] == "RECENT_ONSET_IN_EMBARGO"


def test_prediction_target_ongoing_event_exclusion(synthetic_approved_forecasting_setup):
    """Verify that an ongoing event active at t0 excludes the window under EXCLUDE policy."""
    p_file, d_file = synthetic_approved_forecasting_setup

    # Window t0 = 1000.0
    win_df = pd.DataFrame([
        {"window_id": "win_pred_ongoing", "window_end": 1000.0, "segment_end": 5000.0}
    ])

    # Event spans [900, 1100] -> active across t0
    events_df = pd.DataFrame([
        {"event_id": "EV_ACTIVE", "onset_time": 900.0, "end_time": 1100.0}
    ])

    res = prediction_target(
        window_index=win_df,
        onsets=events_df,
        horizon_seconds=1800.0,
        embargo_seconds=0.0,
        ongoing_event_policy="EXCLUDE",
        policy_path=p_file,
        decisions_path=d_file,
    )

    assert len(res) == 1
    row = res.iloc[0]
    assert pd.isna(row["label_prediction"])
    assert row["excluded_reason"] == "ONGOING_EVENT_AT_T0"
    assert bool(row["ongoing_event_at_t0"]) is True


def test_prediction_target_insufficient_horizon_coverage(synthetic_approved_forecasting_setup):
    """Verify that a window near the end of a segment with incomplete horizon coverage is excluded."""
    p_file, d_file = synthetic_approved_forecasting_setup

    # Window t0 = 1000.0, horizon H = 1800s (requires observation up to 2800s)
    # Segment ends at 1500s -> only 500s of horizon observed (500/1800 = 27.8% < 80%)
    win_df = pd.DataFrame([
        {"window_id": "win_pred_censored", "window_end": 1000.0, "segment_end": 1500.0}
    ])

    events_df = pd.DataFrame(columns=["event_id", "onset_time", "end_time"])

    res = prediction_target(
        window_index=win_df,
        onsets=events_df,
        horizon_seconds=1800.0,
        embargo_seconds=300.0,
        min_coverage_fraction=0.80,
        policy_path=p_file,
        decisions_path=d_file,
    )

    assert len(res) == 1
    row = res.iloc[0]
    assert pd.isna(row["label_prediction"])
    assert "INSUFFICIENT_HORIZON_COVERAGE" in row["excluded_reason"]
    assert row["horizon_coverage_fraction"] < 0.80
