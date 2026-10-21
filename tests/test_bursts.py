"""Unit tests for solar_flare.eda.bursts module.

Uses synthetic fixtures named fixture_synthetic_*.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from solar_flare.eda.bursts import robust_baseline, candidate_intervals


@pytest.fixture
def fixture_synthetic_flat_series():
    """Flat series of 100 points with constant count 10.0."""
    times = np.arange(0.0, 100.0, 1.0)
    values = np.full(100, 10.0, dtype=np.float64)
    return times, values


@pytest.fixture
def fixture_synthetic_injected_burst():
    """Flat 10.0 series with an injected burst of duration 15 s (t=40 to t=55)."""
    times = np.arange(0.0, 100.0, 1.0)
    values = np.full(100, 10.0, dtype=np.float64)
    # Inject burst spanning 15 seconds (16 points: indices 40 to 55)
    values[40:56] = 80.0
    values[48] = 150.0  # Peak
    return times, values


def test_candidate_intervals_flat_series_zero_candidates(fixture_synthetic_flat_series):
    """Verify flat series yields zero candidate bursts and returns header-only DataFrame."""
    times, values = fixture_synthetic_flat_series
    baseline = robust_baseline(times, values, span_seconds=20.0)
    cands = candidate_intervals(times, values, baseline, threshold_sigma=3.0, min_duration_seconds=5.0)

    assert isinstance(cands, pd.DataFrame)
    assert len(cands) == 0
    # Must contain exact column schema even when empty
    expected_cols = [
        "candidate_id",
        "start",
        "end",
        "duration",
        "peak_time",
        "peak_value",
        "peak_to_baseline_ratio",
        "n_samples",
        "status",
    ]
    assert list(cands.columns) == expected_cols


def test_candidate_intervals_injected_burst_detected(fixture_synthetic_injected_burst):
    """Verify exactly one candidate burst is detected with exact timestamps and mandatory status."""
    times, values = fixture_synthetic_injected_burst
    baseline = robust_baseline(times, values, span_seconds=40.0)
    cands = candidate_intervals(
        times,
        values,
        baseline,
        threshold_sigma=3.0,
        min_duration_seconds=10.0,
    )

    assert len(cands) == 1
    cand = cands.iloc[0]
    assert cand["candidate_id"] == "CAND_001"
    assert cand["start"] == 40.0
    assert cand["end"] == 55.0
    assert cand["duration"] == 15.0
    assert cand["peak_time"] == 48.0
    assert cand["peak_value"] == 150.0
    assert cand["n_samples"] == 16
    assert cand["status"] == "CANDIDATE — UNVERIFIED"


def test_candidate_intervals_empty_input():
    """Verify empty input arrays produce header-only DataFrame."""
    times = np.array([])
    values = np.array([])
    baseline = np.array([])
    cands = candidate_intervals(times, values, baseline)
    assert isinstance(cands, pd.DataFrame)
    assert len(cands) == 0
    assert "status" in cands.columns
