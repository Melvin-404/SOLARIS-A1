"""Unit tests for solar_flare.quality.cadence module.

Uses synthetic fixtures in pytest tmp_path or in-memory arrays.
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_flare.quality.cadence import estimate_cadence, find_cadence_gaps


@pytest.fixture
def fixture_synthetic_regular_cadence():
    """Regular 1.0 s cadence array."""
    return np.arange(0.0, 100.0, 1.0)


@pytest.fixture
def fixture_synthetic_irregular_cadence():
    """Irregular cadence with known steps: [1, 1, 2, 1, 3, 1, 1]."""
    steps = [1.0, 1.0, 2.0, 1.0, 3.0, 1.0, 1.0]
    return np.cumsum([0.0] + steps)


@pytest.fixture
def fixture_synthetic_timestamps_with_gaps():
    """Timestamps with nominal 1.0 s cadence and two distinct gaps: 5.0 s and 10.0 s."""
    # 0 to 10 by 1.0, then jump of 5.0 to 15.0, then to 20 by 1.0, then jump of 10.0 to 30.0
    part1 = np.arange(0.0, 11.0, 1.0)  # 0 to 10
    part2 = np.arange(15.0, 21.0, 1.0)  # 15 to 20 (gap at 10 -> 15 is 5.0 s)
    part3 = np.arange(30.0, 36.0, 1.0)  # 30 to 35 (gap at 20 -> 30 is 10.0 s)
    return np.concatenate([part1, part2, part3])


def test_estimate_cadence_regular(fixture_synthetic_regular_cadence):
    """Verify regular cadence returns exact 1.0 s median, mode, and 0.0 std."""
    res = estimate_cadence(fixture_synthetic_regular_cadence)
    assert res["status"] == "PASS"
    assert res["cadence_median"] == 1.0
    assert res["cadence_mode"] == 1.0
    assert res["cadence_min"] == 1.0
    assert res["cadence_max"] == 1.0
    assert res["cadence_std"] == 0.0
    assert res["n_positive_diffs"] == 99


def test_estimate_cadence_irregular(fixture_synthetic_irregular_cadence):
    """Verify irregular cadence returns documented statistics."""
    res = estimate_cadence(fixture_synthetic_irregular_cadence)
    assert res["status"] == "PASS"
    assert res["cadence_mode"] == 1.0
    assert res["cadence_min"] == 1.0
    assert res["cadence_max"] == 3.0
    assert res["n_positive_diffs"] == 7


def test_find_cadence_gaps_known_gaps(fixture_synthetic_timestamps_with_gaps):
    """Verify known cadence gaps are detected with exact start, end, and duration."""
    res = find_cadence_gaps(fixture_synthetic_timestamps_with_gaps, expected_cadence=1.0, tolerance_factor=1.5)
    assert res["status"] == "WARN"
    assert res["n_cadence_gaps"] == 2
    assert res["threshold_s"] == 1.5

    gaps = res["gaps"]
    assert len(gaps) == 2
    # Gap 1: 10.0 -> 15.0, duration 5.0 s
    assert gaps[0]["start_time"] == 10.0
    assert gaps[0]["end_time"] == 15.0
    assert gaps[0]["duration_s"] == 5.0
    assert gaps[0]["missing_steps_estimated"] == 4

    # Gap 2: 20.0 -> 30.0, duration 10.0 s
    assert gaps[1]["start_time"] == 20.0
    assert gaps[1]["end_time"] == 30.0
    assert gaps[1]["duration_s"] == 10.0
    assert gaps[1]["missing_steps_estimated"] == 9

    assert res["total_gap_duration_s"] == 15.0


def test_find_cadence_gaps_clean_no_gaps(fixture_synthetic_regular_cadence):
    """Verify clean regular series yields zero gaps."""
    res = find_cadence_gaps(fixture_synthetic_regular_cadence, expected_cadence=1.0, tolerance_factor=1.5)
    assert res["status"] == "PASS"
    assert res["n_cadence_gaps"] == 0
    assert len(res["gaps"]) == 0
