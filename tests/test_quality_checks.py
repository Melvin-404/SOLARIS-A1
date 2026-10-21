"""Unit tests for solar_flare.quality.checks module.

All tests utilize pure synthetic fixtures named fixture_synthetic_*.
No real data files in data/raw/ are touched.
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_flare.quality.checks import (
    check_non_finite,
    check_negative_values,
    check_duplicate_timestamps,
    check_time_ordering,
    check_zero_runs,
    check_quality_flags,
    check_candidate_spikes,
)


@pytest.fixture
def fixture_synthetic_non_finite_data():
    """Synthetic array with known counts of NaN, +inf, and -inf."""
    # 10 finite, 3 NaNs, 2 +inf, 1 -inf -> total 16
    return np.array([
        1.0, 2.0, np.nan, 4.0, np.inf, 6.0, -np.inf,
        np.nan, 9.0, 10.0, np.nan, 12.0, np.inf, 14.0, 15.0, 16.0
    ], dtype=np.float64)


@pytest.fixture
def fixture_synthetic_negative_data():
    """Synthetic array containing negative counts alongside positive counts."""
    return np.array([10.0, -2.5, 0.0, 15.0, -0.1, 8.0], dtype=np.float64)


@pytest.fixture
def fixture_synthetic_timestamps_with_duplicates():
    """Synthetic timestamp array with known duplicate occurrences."""
    return np.array([100.0, 101.0, 102.0, 102.0, 103.0, 104.0, 104.0, 104.0])


@pytest.fixture
def fixture_synthetic_timestamps_with_backward_steps():
    """Synthetic timestamps with known backward step."""
    return np.array([100.0, 101.0, 102.0, 99.5, 103.0, 104.0])


@pytest.fixture
def fixture_synthetic_zero_runs_data():
    """Synthetic array with distinct zero runs and embedded NaNs."""
    # 2 positive, 6 zeros, 3 positive, 8 zeros, 2 NaNs, 3 zeros, 2 positive
    return (
        np.array([
            5.0, 6.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # run 1: len 6
            4.0, 5.0, 6.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # run 2: len 8
            np.nan, np.nan,
            0.0, 0.0, 0.0,  # run 3: len 3 (below min_length 5)
            10.0, 12.0,
        ], dtype=np.float64),
        np.arange(100.0, 126.0)
    )


@pytest.fixture
def fixture_synthetic_spikes_data():
    """Synthetic baseline with an extreme isolated outlier."""
    np.random.seed(42)
    baseline = np.ones(100) * 10.0
    baseline[50] = 500.0  # Massive spike
    return baseline


def test_check_non_finite_known_counts(fixture_synthetic_non_finite_data):
    """Verify check_non_finite separates NaN, +inf, and -inf with exact counts."""
    res = check_non_finite(fixture_synthetic_non_finite_data)
    assert res["name"] == "check_non_finite"
    assert res["status"] == "WARN"
    assert res["counts"]["total_samples"] == 16
    assert res["counts"]["n_nan"] == 3
    assert res["counts"]["n_pos_inf"] == 2
    assert res["counts"]["n_neg_inf"] == 1
    assert res["counts"]["n_non_finite"] == 6


def test_check_non_finite_clean():
    """Verify check_non_finite on clean finite data returns PASS."""
    clean = np.array([1.0, 2.0, 3.0, 4.0])
    res = check_non_finite(clean)
    assert res["status"] == "PASS"
    assert res["counts"]["n_non_finite"] == 0


def test_check_negative_values(fixture_synthetic_negative_data):
    """Verify check_negative_values detects negatives without modifying array."""
    original_copy = fixture_synthetic_negative_data.copy()
    res = check_negative_values(fixture_synthetic_negative_data)

    assert res["name"] == "check_negative_values"
    assert res["status"] == "FAIL"
    assert res["counts"]["n_negative"] == 2
    assert res["detail"]["min_finite_value"] == -2.5
    # Verify non-destructive guarantee
    np.testing.assert_array_equal(fixture_synthetic_negative_data, original_copy)


def test_check_duplicate_timestamps(fixture_synthetic_timestamps_with_duplicates):
    """Verify check_duplicate_timestamps counts duplicates and identifies examples."""
    res = check_duplicate_timestamps(fixture_synthetic_timestamps_with_duplicates)
    assert res["name"] == "check_duplicate_timestamps"
    assert res["status"] == "WARN"
    # In [100, 101, 102, 102, 103, 104, 104, 104]:
    # 102 appears twice (1 duplicate), 104 appears 3 times (2 duplicates) -> total 3 duplicates
    assert res["counts"]["n_duplicates"] == 3
    assert len(res["detail"]["examples"]) == 2


def test_check_time_ordering(fixture_synthetic_timestamps_with_backward_steps):
    """Verify check_time_ordering identifies backward steps and positions."""
    res = check_time_ordering(fixture_synthetic_timestamps_with_backward_steps)
    assert res["name"] == "check_time_ordering"
    assert res["status"] == "FAIL"
    assert res["counts"]["n_backward_steps"] == 1
    assert res["detail"]["examples"][0]["step_index"] == 2
    assert res["detail"]["examples"][0]["t_current"] == 102.0
    assert res["detail"]["examples"][0]["t_next"] == 99.5


def test_check_zero_runs(fixture_synthetic_zero_runs_data):
    """Verify check_zero_runs tracks contiguous zero runs segregated from NaNs."""
    values, times = fixture_synthetic_zero_runs_data
    res = check_zero_runs(values, times, min_run_length=5)

    assert res["name"] == "check_zero_runs"
    assert res["status"] == "WARN"
    # Total zeros: 6 + 8 + 3 = 17
    assert res["counts"]["n_zero_samples"] == 17
    # Runs >= 5: run 1 (len 6) and run 2 (len 8) -> 2 runs
    assert res["counts"]["n_zero_runs"] == 2
    assert res["counts"]["max_zero_run_length"] == 8

    runs = res["detail"]["runs"]
    assert len(runs) == 2
    assert runs[0]["length"] == 6
    assert runs[0]["start_idx"] == 2
    assert runs[0]["end_idx"] == 7
    assert runs[1]["length"] == 8
    assert runs[1]["start_idx"] == 11
    assert runs[1]["end_idx"] == 18


def test_check_quality_flags_unresolved():
    """Verify check_quality_flags reports UNRESOLVED when meanings not confirmed."""
    raw_flags = np.array([0, 0, 1, 0, 2, 0, 1])
    res = check_quality_flags(raw_flags, confirmed_meanings=None)
    assert res["status"] == "WARN"
    assert "UNRESOLVED" in res["detail"]["interpretation_status"]
    assert res["counts"]["distribution"]["0"] == 4
    assert res["counts"]["distribution"]["1"] == 2
    assert res["counts"]["distribution"]["2"] == 1


def test_check_candidate_spikes(fixture_synthetic_spikes_data):
    """Verify candidate spikes are flagged with robust z-score and explicit scientific label."""
    times = np.arange(len(fixture_synthetic_spikes_data))
    res = check_candidate_spikes(fixture_synthetic_spikes_data, times=times, z_threshold=5.0)

    assert res["name"] == "check_candidate_spikes"
    assert res["status"] == "WARN"
    assert res["counts"]["n_candidate_spikes"] == 1
    assert res["detail"]["label"] == "candidate spike — not a verified event"
    example = res["detail"]["examples"][0]
    assert example["index"] == 50
    assert example["value"] == 500.0
    assert example["label"] == "candidate spike — not a verified event"
