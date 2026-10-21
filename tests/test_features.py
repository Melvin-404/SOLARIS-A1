"""Unit tests for solar_flare.features.features module.

Tests individual statistical feature calculations, edge cases, zero division safeguards,
and non-finite sample filtering.
All synthetic fixtures are named fixture_synthetic_*.
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_flare.features import features as F


@pytest.fixture
def fixture_synthetic_constant_series() -> Tuple[list, list]:
    """Create a constant series where std and slope are mathematically zero."""
    times = [10.0, 11.0, 12.0, 13.0, 14.0]
    counts = [25.0, 25.0, 25.0, 25.0, 25.0]
    return counts, times


@pytest.fixture
def fixture_synthetic_linear_series() -> Tuple[list, list]:
    """Create a linear series with known slope = 3.5 counts/second."""
    times = [0.0, 1.0, 2.0, 3.0, 4.0]
    # y = 10.0 + 3.5 * t -> [10.0, 13.5, 17.0, 20.5, 24.0]
    counts = [10.0 + 3.5 * t for t in times]
    return counts, times


@pytest.fixture
def fixture_synthetic_known_mad_series() -> list:
    """Create a known series for MAD calculation.
    
    Series: [1, 2, 3, 4, 5, 6, 7, 8, 9]
    Median = 5
    Absolute deviations: [4, 3, 2, 1, 0, 1, 2, 3, 4]
    Sorted deviations: [0, 1, 1, 2, 2, 3, 3, 4, 4]
    Median deviation (MAD) = 2.0
    Robust variability = 1.4826 * 2.0 = 2.9652
    """
    return [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]


def test_constant_series_std_and_slope(fixture_synthetic_constant_series):
    """Verify that constant series yields std=0 and slope=0."""
    counts, times = fixture_synthetic_constant_series

    std_val, std_rsn = F.calc_std(counts)
    assert std_val == 0.0
    assert std_rsn is None

    slope_val, slope_rsn = F.calc_temporal_slope(counts, times)
    assert slope_val == 0.0
    assert slope_rsn is None


def test_linear_series_exact_slope(fixture_synthetic_linear_series):
    """Verify that linear series yields exact slope (3.5)."""
    counts, times = fixture_synthetic_linear_series
    slope_val, slope_rsn = F.calc_temporal_slope(counts, times)
    assert pytest.approx(slope_val, abs=1e-7) == 3.5
    assert slope_rsn is None


def test_robust_variability_on_known_array(fixture_synthetic_known_mad_series):
    """Verify that normalized MAD yields 1.4826 * 2.0 = 2.9652."""
    counts = fixture_synthetic_known_mad_series
    val, rsn = F.calc_robust_variability(counts)
    assert pytest.approx(val, abs=1e-4) == 2.9652
    assert rsn is None


def test_iqr_and_percentiles():
    """Verify that IQR and percentile calculations match empirical quantiles."""
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    pcts = F.calc_percentiles(values, levels=(25, 75))
    assert pcts["p25"][0] == 20.0
    assert pcts["p75"][0] == 40.0

    iqr_val, _ = F.calc_iqr(values)
    assert iqr_val == 20.0


def test_slope_insufficient_samples_returns_nan():
    """Verify that slope returns NaN with 'INSUFFICIENT_SAMPLES' when fewer than 3 samples."""
    val, rsn = F.calc_temporal_slope([10.0, 20.0], [1.0, 2.0])
    assert np.isnan(val)
    assert rsn == "INSUFFICIENT_SAMPLES"


def test_peak_to_baseline_ratio_safeguards():
    """Verify that peak_to_baseline_ratio handles zero and negative baselines safely."""
    counts = [10.0, 20.0, 30.0]

    # Valid baseline
    v1, r1 = F.calc_peak_to_baseline_ratio(counts, baseline_value=15.0)
    assert pytest.approx(v1, abs=1e-7) == 2.0
    assert r1 is None

    # Zero baseline
    v2, r2 = F.calc_peak_to_baseline_ratio(counts, baseline_value=0.0)
    assert np.isnan(v2)
    assert r2 == "BASELINE_NONPOSITIVE"

    # Negative baseline
    v3, r3 = F.calc_peak_to_baseline_ratio(counts, baseline_value=-5.0)
    assert np.isnan(v3)
    assert r3 == "BASELINE_NONPOSITIVE"

    # Unavailable baseline
    v4, r4 = F.calc_peak_to_baseline_ratio(counts, baseline_value=None)
    assert np.isnan(v4)
    assert r4 == "BASELINE_UNAVAILABLE"


def test_non_finite_samples_excluded_and_counted():
    """Verify that NaN and inf values are excluded without crashing calculations."""
    counts = [10.0, np.nan, 20.0, np.inf, 30.0]
    mean_val, _ = F.calc_mean(counts)
    assert mean_val == 20.0

    n_obs, _ = F.calc_n_observed_samples(counts)
    assert n_obs == 3
