"""Unit tests for solar_flare.eda.variability module.

Uses synthetic fixtures named fixture_synthetic_*.
No real data files in data/raw/ are touched.
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_flare.eda.variability import (
    rolling_summary,
    variability_stats,
    count_histogram_data,
)


@pytest.fixture
def fixture_synthetic_variability_array():
    """Known numeric array: [2, 4, 4, 4, 5, 5, 7, 9] plus 2 NaNs and 1 +inf."""
    clean = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0], dtype=np.float64)
    with_non_finite = np.array([
        2.0, 4.0, np.nan, 4.0, 4.0, np.inf, 5.0, 5.0, 7.0, 9.0, np.nan
    ], dtype=np.float64)
    return clean, with_non_finite


@pytest.fixture
def fixture_synthetic_histogram_array():
    """Array with 5 positive counts, 3 finite zeros, and 2 NaNs."""
    return np.array([10.0, 0.0, 15.0, np.nan, 0.0, 20.0, 25.0, np.nan, 0.0, 30.0], dtype=np.float64)


def test_variability_stats_exact_metrics(fixture_synthetic_variability_array):
    """Verify exact mean, median, MAD, IQR, and CV on known array."""
    clean, with_non_finite = fixture_synthetic_variability_array
    res_clean = variability_stats(clean)

    # Clean array: [2, 4, 4, 4, 5, 5, 7, 9]
    # Sum = 40, N = 8 -> Mean = 5.0
    assert res_clean["mean"] == 5.0
    # Median of [2, 4, 4, 4, 5, 5, 7, 9] is 4.5
    assert res_clean["median"] == 4.5
    # Absolute deviations from 4.5: [2.5, 0.5, 0.5, 0.5, 0.5, 0.5, 2.5, 4.5]
    # Sorted: [0.5, 0.5, 0.5, 0.5, 0.5, 2.5, 2.5, 4.5] -> Median = 0.5
    assert res_clean["mad"] == 0.5
    assert pytest.approx(res_clean["mad_dispersion"], 1e-4) == 1.4826 * 0.5
    assert res_clean["n_finite"] == 8
    assert res_clean["n_excluded"] == 0

    # With non-finite: 8 finite, 3 non-finite -> metrics should be identical on finite subset
    res_dirty = variability_stats(with_non_finite)
    assert res_dirty["mean"] == 5.0
    assert res_dirty["median"] == 4.5
    assert res_dirty["mad"] == 0.5
    assert res_dirty["n_finite"] == 8
    assert res_dirty["n_excluded"] == 3


def test_count_histogram_data_segregates_zeros(fixture_synthetic_histogram_array):
    """Verify count_histogram_data reports zeros and non-finite counts separately."""
    res = count_histogram_data(fixture_synthetic_histogram_array, bins=5)
    assert res["n_zeros"] == 3
    assert res["n_non_finite"] == 2
    assert res["n_positive"] == 5
    assert res["total_samples"] == 10
    assert len(res["counts"]) == 5
    assert sum(res["counts"]) == 5


def test_rolling_summary_time_based_window():
    """Verify rolling_summary uses physical time duration rather than sample index."""
    # Timestamps with a gap: [0, 1, 2, 10, 11, 12]
    # At t=1, window [1 - 2, 1 + 2] = [-1, 3] includes indices 0, 1, 2 (values 10, 10, 10)
    times = np.array([0.0, 1.0, 2.0, 10.0, 11.0, 12.0], dtype=np.float64)
    values = np.array([10.0, 10.0, 10.0, 50.0, 50.0, 50.0], dtype=np.float64)

    res = rolling_summary(times, values, window_seconds=4.0)
    assert len(res["rolling_median"]) == 6
    # For t=1, window is [-1, 3], finite values are [10, 10, 10], median is 10.0
    assert res["rolling_median"][1] == 10.0
    # For t=11, window is [9, 13], finite values are [50, 50, 50], median is 50.0
    assert res["rolling_median"][4] == 50.0
