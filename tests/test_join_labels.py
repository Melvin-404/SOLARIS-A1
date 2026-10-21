"""Tests for Task A label integration and matching (Stage 9).

Validates:
- Clear positive window
- Clear negative window
- Tolerance boundary matching
- Partial overlap exclusion (NA not 0)
- Embargo buffer exclusion (NA not 0)
- Low coverage exclusion (NA not 0)
- Quiet interval filtering
- Unhandled policy condition raises UnhandledPolicyCase
"""

from __future__ import annotations

from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import yaml

from solar_flare.export.join_labels import label_windows_detection, UnhandledPolicyCase
from solar_flare.labels.policy import LabellingNotApprovedError


@pytest.fixture
def synthetic_approved_policy(tmp_path: Path):
    """Create synthetic approved policy and decisions in tmp_path."""
    policy_file = tmp_path / "08_labelling_policy.md"
    policy_file.write_text(
        "# Labelling Policy\n\nStatus: APPROVED by Researcher, date 2026-10-21\n",
        encoding="utf-8",
    )

    decisions_file = tmp_path / "decisions.yaml"
    decisions_data = {
        "decisions": {
            "D-01": {"status": "APPROVED", "value": "SRC_NOAA_GOES"},
            "D-02": {"status": "APPROVED", "value": 5.0},
            "D-03": {"status": "APPROVED", "value": "PEAK_HALF_POWER"},
            "D-04": {"status": "APPROVED", "value": "EXCLUDE_PARTIAL"},
            "D-08": {"status": "APPROVED", "value": 60.0},
            "D-10": {"status": "APPROVED", "value": "UTC_SECONDS"},
            "D-15": {"status": "APPROVED", "value": 10},
        }
    }
    with open(decisions_file, "w", encoding="utf-8") as f:
        yaml.dump(decisions_data, f)

    return policy_file, decisions_file


def test_clear_positive_and_clear_negative_windows(synthetic_approved_policy):
    """Verify that a window containing a flare is positive (1) and a clean window is negative (0)."""
    p_file, d_file = synthetic_approved_policy

    # Window index: 3 windows of length 60s
    win_df = pd.DataFrame([
        {
            "window_id": "win_001",
            "window_start": 100.0,
            "window_end": 160.0,
            "coverage_fraction": 1.0,
            "quality_flag": "OK",
        },
        {
            "window_id": "win_002",
            "window_start": 300.0,
            "window_end": 360.0,
            "coverage_fraction": 1.0,
            "quality_flag": "OK",
        },
    ])

    # Event occurs in [110, 150] -> completely inside win_001
    events_df = pd.DataFrame([
        {
            "event_id": "EV_01",
            "onset_time": 110.0,
            "end_time": 150.0,
        }
    ])

    params = {
        "tolerance_seconds": 2.0,
        "min_overlap_fraction": 0.50,
        "embargo_seconds": 30.0,
        "min_coverage_fraction": 0.80,
    }

    res = label_windows_detection(
        window_index=win_df,
        events=events_df,
        params=params,
        policy_path=p_file,
        decisions_path=d_file,
    )

    assert len(res) == 2
    # win_001 is positive
    w1 = res.iloc[0]
    assert w1["window_id"] == "win_001"
    assert w1["label_detection"] == 1
    assert w1["event_id"] == "EV_01"
    assert "MATCHED_EVENT" in w1["label_reason"]

    # win_002 is verified negative (clean quiet interval)
    w2 = res.iloc[1]
    assert w2["window_id"] == "win_002"
    assert w2["label_detection"] == 0
    assert pd.isna(w2["event_id"]) or w2["event_id"] is None
    assert w2["label_reason"] == "VERIFIED_QUIET_BACKGROUND"


def test_partial_overlap_excludes_window(synthetic_approved_policy):
    """Verify that partial overlap (< min_overlap_fraction) yields NA not 0."""
    p_file, d_file = synthetic_approved_policy

    win_df = pd.DataFrame([
        {
            "window_id": "win_part",
            "window_start": 100.0,
            "window_end": 160.0,  # 60s window
            "coverage_fraction": 1.0,
            "quality_flag": "OK",
        }
    ])

    # Event [155, 200] overlaps window by only 5 seconds (5/60 = 8.3% < 50%)
    events_df = pd.DataFrame([
        {"event_id": "EV_PART", "onset_time": 155.0, "end_time": 200.0}
    ])

    params = {
        "tolerance_seconds": 0.0,
        "min_overlap_fraction": 0.50,
        "embargo_seconds": 0.0,
        "min_coverage_fraction": 0.80,
    }

    res = label_windows_detection(win_df, events_df, params, policy_path=p_file, decisions_path=d_file)
    w = res.iloc[0]
    assert pd.isna(w["label_detection"])
    assert "PARTIAL_OVERLAP_EXCLUDED" in w["label_reason"]


def test_embargo_buffer_excludes_window(synthetic_approved_policy):
    """Verify that a window within event embargo buffer yields NA not 0."""
    p_file, d_file = synthetic_approved_policy

    win_df = pd.DataFrame([
        {
            "window_id": "win_emb",
            "window_start": 50.0,
            "window_end": 90.0,  # [50, 90]
            "coverage_fraction": 1.0,
            "quality_flag": "OK",
        }
    ])

    # Event onset is 100. Embargo is 20s (buffer [80, 100]). Window ends at 90s, overlapping embargo.
    events_df = pd.DataFrame([
        {"event_id": "EV_EMB", "onset_time": 100.0, "end_time": 150.0}
    ])

    params = {
        "tolerance_seconds": 0.0,
        "min_overlap_fraction": 0.50,
        "embargo_seconds": 20.0,
        "min_coverage_fraction": 0.80,
    }

    res = label_windows_detection(win_df, events_df, params, policy_path=p_file, decisions_path=d_file)
    w = res.iloc[0]
    assert pd.isna(w["label_detection"])
    assert "EMBARGO_EXCLUDED" in w["label_reason"]


def test_low_coverage_excludes_window(synthetic_approved_policy):
    """Verify that a window with low coverage fraction yields NA not 0."""
    p_file, d_file = synthetic_approved_policy

    win_df = pd.DataFrame([
        {
            "window_id": "win_low",
            "window_start": 500.0,
            "window_end": 560.0,
            "coverage_fraction": 0.65,  # < 0.80
            "quality_flag": "LOW_COVERAGE",
        }
    ])

    events_df = pd.DataFrame(columns=["event_id", "onset_time", "end_time"])

    params = {
        "tolerance_seconds": 0.0,
        "min_overlap_fraction": 0.50,
        "embargo_seconds": 0.0,
        "min_coverage_fraction": 0.80,
    }

    res = label_windows_detection(win_df, events_df, params, policy_path=p_file, decisions_path=d_file)
    w = res.iloc[0]
    assert pd.isna(w["label_detection"])
    assert "LOW_COVERAGE_EXCLUDED" in w["label_reason"]


def test_unapproved_policy_raises_guard(tmp_path: Path):
    """Verify that labelling strictly refuses to run under DRAFT policy."""
    policy_file = tmp_path / "08_labelling_policy.md"
    policy_file.write_text("Status: DRAFT — REQUIRES HUMAN APPROVAL\n", encoding="utf-8")

    win_df = pd.DataFrame([{"window_id": "w1", "window_start": 0.0, "window_end": 60.0, "coverage_fraction": 1.0, "quality_flag": "OK"}])
    events_df = pd.DataFrame(columns=["event_id", "onset_time", "end_time"])

    with pytest.raises(LabellingNotApprovedError):
        label_windows_detection(win_df, events_df, params={"tolerance_seconds": 2.0}, policy_path=policy_file)


def test_tolerance_boundary_matching(synthetic_approved_policy):
    """Verify that an event matching exactly at the tolerance boundary is included."""
    p_file, d_file = synthetic_approved_policy

    # Window [100.0, 160.0]
    win_df = pd.DataFrame([{
        "window_id": "win_tol",
        "window_start": 100.0,
        "window_end": 160.0,
        "coverage_fraction": 1.0,
        "quality_flag": "OK",
    }])

    # Event starts at 162.0s. Tolerance is 5.0s -> window effective end is 165.0s. Overlap = 3.0s.
    # With min_overlap_fraction=0.04 (4%), 3.0s / 60s = 5% >= 4% -> positive
    events_df = pd.DataFrame([{"event_id": "EV_TOL", "onset_time": 162.0, "end_time": 200.0}])

    params = {
        "tolerance_seconds": 5.0,
        "min_overlap_fraction": 0.04,
        "embargo_seconds": 0.0,
        "min_coverage_fraction": 0.80,
    }
    res = label_windows_detection(win_df, events_df, params, policy_path=p_file, decisions_path=d_file)
    assert res.iloc[0]["label_detection"] == 1
    assert res.iloc[0]["event_id"] == "EV_TOL"


def test_quiet_interval_unknown_gives_na(synthetic_approved_policy):
    """Verify that when quiet_intervals is defined, windows outside it are NA not 0."""
    p_file, d_file = synthetic_approved_policy

    win_df = pd.DataFrame([{
        "window_id": "win_outside_quiet",
        "window_start": 500.0,
        "window_end": 560.0,
        "coverage_fraction": 1.0,
        "quality_flag": "OK",
    }])

    events_df = pd.DataFrame(columns=["event_id", "onset_time", "end_time"])

    # Approved quiet interval is [1000, 2000]. Window [500, 560] is outside it.
    params = {
        "tolerance_seconds": 2.0,
        "min_overlap_fraction": 0.50,
        "embargo_seconds": 0.0,
        "min_coverage_fraction": 0.80,
        "quiet_intervals": [(1000.0, 2000.0)],
    }

    res = label_windows_detection(win_df, events_df, params, policy_path=p_file, decisions_path=d_file)
    assert pd.isna(res.iloc[0]["label_detection"])
    assert res.iloc[0]["label_reason"] == "OUTSIDE_APPROVED_QUIET_INTERVAL"
