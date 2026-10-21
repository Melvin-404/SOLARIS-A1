"""Pure functional feature library for SOLARIS-A1 (Stage 8).

Every function computes a strictly causal time-series statistic over observations
belonging to a single window [window_start, window_end].
Edge cases (zero division, insufficient samples, non-positive baselines) return NaN
accompanied by explicit scientific reason codes.

PROHIBITIONS:
- No future-peeking or acausal operations.
- Non-finite samples are excluded from evaluation and counted; never estimated or reconstructed.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple, Union
import numpy as np
import scipy.stats


def _extract_finite_pairs(
    values: Sequence[float],
    times: Optional[Sequence[float]] = None,
) -> Tuple[np.ndarray, Optional[np.ndarray], int]:
    """Extract valid finite (value, time) sample arrays and count dropped non-finite samples."""
    v_arr = np.asarray(values, dtype=np.float64)
    finite_mask = np.isfinite(v_arr)
    n_dropped = int((~finite_mask).sum())

    v_clean = v_arr[finite_mask]

    if times is not None:
        t_arr = np.asarray(times, dtype=np.float64)
        t_clean = t_arr[finite_mask]
        return v_clean, t_clean, n_dropped

    return v_clean, None, n_dropped


def calc_mean(values: Sequence[float]) -> Tuple[float, Optional[str]]:
    """Compute arithmetic mean of window samples.
    
    Definition:
        mean = (1 / N) * sum_{i=1}^N x_i
    Units:
        Counts (or detector count rate)
    Edge cases:
        Returns (NaN, 'ZERO_SAMPLES') if N == 0.
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    if len(v_clean) == 0:
        return np.nan, "ZERO_SAMPLES"
    return float(np.mean(v_clean)), None


def calc_median(values: Sequence[float]) -> Tuple[float, Optional[str]]:
    """Compute sample median (50th percentile) of window samples.
    
    Definition:
        median = 50th percentile of finite samples.
    Units:
        Counts
    Edge cases:
        Returns (NaN, 'ZERO_SAMPLES') if N == 0.
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    if len(v_clean) == 0:
        return np.nan, "ZERO_SAMPLES"
    return float(np.median(v_clean)), None


def calc_std(values: Sequence[float]) -> Tuple[float, Optional[str]]:
    """Compute sample standard deviation with Bessel correction (ddof=1).
    
    Definition:
        std = sqrt( (1 / (N - 1)) * sum_{i=1}^N (x_i - mean)^2 )
    Units:
        Counts
    Edge cases:
        Returns (0.0, None) if all values are identical.
        Returns (NaN, 'INSUFFICIENT_SAMPLES') if N < 2.
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    if len(v_clean) < 2:
        return np.nan, "INSUFFICIENT_SAMPLES"
    return float(np.std(v_clean, ddof=1)), None


def calc_robust_variability(values: Sequence[float]) -> Tuple[float, Optional[str]]:
    """Compute robust dispersion estimator via Median Absolute Deviation (MAD).
    
    Definition:
        robust_var = 1.4826 * median( |x_i - median(x)| )
    Units:
        Counts
    Edge cases:
        Returns (0.0, None) if N >= 1 and all values identical.
        Returns (NaN, 'ZERO_SAMPLES') if N == 0.
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    if len(v_clean) == 0:
        return np.nan, "ZERO_SAMPLES"
    med = np.median(v_clean)
    mad = np.median(np.abs(v_clean - med))
    return float(1.4826 * mad), None


def calc_min(values: Sequence[float]) -> Tuple[float, Optional[str]]:
    """Compute minimum observed value within the window.
    
    Definition:
        min = min_{i=1..N} x_i
    Units:
        Counts
    Edge cases:
        Returns (NaN, 'ZERO_SAMPLES') if N == 0.
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    if len(v_clean) == 0:
        return np.nan, "ZERO_SAMPLES"
    return float(np.min(v_clean)), None


def calc_max(values: Sequence[float]) -> Tuple[float, Optional[str]]:
    """Compute maximum observed value within the window.
    
    Definition:
        max = max_{i=1..N} x_i
    Units:
        Counts
    Edge cases:
        Returns (NaN, 'ZERO_SAMPLES') if N == 0.
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    if len(v_clean) == 0:
        return np.nan, "ZERO_SAMPLES"
    return float(np.max(v_clean)), None


def calc_percentiles(
    values: Sequence[float],
    levels: Sequence[float] = (5, 25, 75, 95),
) -> Dict[str, Tuple[float, Optional[str]]]:
    """Compute empirical percentiles at configured levels.
    
    Definition:
        p_q = q-th empirical percentile.
    Units:
        Counts
    Edge cases:
        Returns (NaN, 'ZERO_SAMPLES') for each level if N == 0.
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    results = {}
    if len(v_clean) == 0:
        for lvl in levels:
            key = f"p{int(lvl):02d}" if lvl == int(lvl) else f"p{lvl}"
            results[key] = (np.nan, "ZERO_SAMPLES")
        return results

    computed = np.percentile(v_clean, levels)
    for lvl, val in zip(levels, computed):
        key = f"p{int(lvl):02d}" if lvl == int(lvl) else f"p{lvl}"
        results[key] = (float(val), None)
    return results


def calc_iqr(values: Sequence[float]) -> Tuple[float, Optional[str]]:
    """Compute Interquartile Range (75th percentile minus 25th percentile).
    
    Definition:
        iqr = p_75 - p_25
    Units:
        Counts
    Edge cases:
        Returns (NaN, 'ZERO_SAMPLES') if N == 0.
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    if len(v_clean) == 0:
        return np.nan, "ZERO_SAMPLES"
    q75, q25 = np.percentile(v_clean, [75, 25])
    return float(q75 - q25), None


def calc_mean_abs_first_diff(values: Sequence[float]) -> Tuple[float, Optional[str]]:
    """Compute mean absolute first difference between adjacent chronological samples.
    
    Definition:
        mean_abs_diff = (1 / (N - 1)) * sum_{i=1}^{N-1} |x_{i+1} - x_i|
    Units:
        Counts (per cadence step)
    Edge cases:
        Returns (NaN, 'INSUFFICIENT_SAMPLES') if N < 2.
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    if len(v_clean) < 2:
        return np.nan, "INSUFFICIENT_SAMPLES"
    diffs = np.abs(np.diff(v_clean))
    return float(np.mean(diffs)), None


def calc_max_abs_first_diff(values: Sequence[float]) -> Tuple[float, Optional[str]]:
    """Compute maximum absolute first difference between adjacent chronological samples.
    
    Definition:
        max_abs_diff = max_{i=1..N-1} |x_{i+1} - x_i|
    Units:
        Counts (per cadence step)
    Edge cases:
        Returns (NaN, 'INSUFFICIENT_SAMPLES') if N < 2.
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    if len(v_clean) < 2:
        return np.nan, "INSUFFICIENT_SAMPLES"
    diffs = np.abs(np.diff(v_clean))
    return float(np.max(diffs)), None


def calc_temporal_slope(
    values: Sequence[float],
    times: Sequence[float],
) -> Tuple[float, Optional[str]]:
    """Compute ordinary least-squares slope of count versus time in seconds.
    
    Definition:
        slope = Cov(values, times) / Var(times)
    Units:
        Counts per second (s^-1)
    Edge cases:
        Returns (NaN, 'INSUFFICIENT_SAMPLES') if N < 3.
        Returns (NaN, 'ZERO_TIME_SPAN') if max(times) == min(times).
    """
    v_clean, t_clean, _ = _extract_finite_pairs(values, times)
    if len(v_clean) < 3:
        return np.nan, "INSUFFICIENT_SAMPLES"

    delta_t = float(t_clean[-1] - t_clean[0])
    if delta_t <= 0.0:
        return np.nan, "ZERO_TIME_SPAN"

    # Least squares linear regression slope
    t_mean = np.mean(t_clean)
    v_mean = np.mean(v_clean)
    numerator = np.sum((t_clean - t_mean) * (v_clean - v_mean))
    denominator = np.sum((t_clean - t_mean) ** 2)

    if denominator <= 0.0:
        return np.nan, "ZERO_VARIANCE_TIME"

    slope = float(numerator / denominator)
    return slope, None


def calc_rolling_trend(
    values: Sequence[float],
    times: Sequence[float],
    k_seconds: float = 15.0,
) -> Tuple[float, Optional[str]]:
    """Compute least-squares slope over the trailing K seconds of the window.
    
    Evaluates only samples where:
        t_i >= t_end - k_seconds
    Units:
        Counts per second (s^-1)
    Edge cases:
        Returns (NaN, 'INSUFFICIENT_TAIL_SAMPLES') if fewer than 3 samples in tail.
        Returns (NaN, 'ZERO_TIME_SPAN') if time span of tail is zero.
    """
    v_clean, t_clean, _ = _extract_finite_pairs(values, times)
    if len(v_clean) < 3:
        return np.nan, "INSUFFICIENT_TAIL_SAMPLES"

    t_end = t_clean[-1]
    tail_cutoff = t_end - float(k_seconds)
    tail_mask = t_clean >= tail_cutoff

    t_tail = t_clean[tail_mask]
    v_tail = v_clean[tail_mask]

    if len(t_tail) < 3:
        return np.nan, "INSUFFICIENT_TAIL_SAMPLES"

    return calc_temporal_slope(v_tail, t_tail)


def calc_peak_to_baseline_ratio(
    values: Sequence[float],
    baseline_value: Optional[float],
    epsilon: float = 1e-6,
) -> Tuple[float, Optional[str]]:
    """Compute ratio of window maximum to local pre-window causal baseline flux.
    
    Definition:
        ratio = max(values) / baseline_value
    Units:
        Dimensionless
    Edge cases:
        Returns (NaN, 'BASELINE_UNAVAILABLE') if baseline_value is None or NaN.
        Returns (NaN, 'BASELINE_NONPOSITIVE') if baseline_value <= epsilon.
        Guarantees zero division never occurs.
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    if len(v_clean) == 0:
        return np.nan, "ZERO_SAMPLES"

    if baseline_value is None or not np.isfinite(baseline_value):
        return np.nan, "BASELINE_UNAVAILABLE"

    if float(baseline_value) <= float(epsilon):
        return np.nan, "BASELINE_NONPOSITIVE"

    peak_val = float(np.max(v_clean))
    ratio = float(peak_val / baseline_value)
    return ratio, None


def calc_coverage_fraction(
    values: Sequence[float],
    n_expected: int,
) -> Tuple[float, Optional[str]]:
    """Compute fraction of observed finite samples against expected count.
    
    Definition:
        coverage = N_finite / n_expected
    Units:
        Dimensionless (ratio in [0.0, 1.0])
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    if n_expected <= 0:
        return 0.0, "INVALID_EXPECTED_COUNT"
    frac = float(len(v_clean) / n_expected)
    return frac, None


def calc_n_observed_samples(values: Sequence[float]) -> Tuple[int, Optional[str]]:
    """Count number of valid finite observations present in the window.
    
    Definition:
        n_obs = count of finite samples
    Units:
        Count (integer)
    """
    v_clean, _, _ = _extract_finite_pairs(values)
    return int(len(v_clean)), None
