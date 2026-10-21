"""Variability and count distribution analysis for SOLARIS-A1 (Stage 5).

Provides pure functional tools for time-based rolling summaries, non-parametric
dispersion metrics, skewness, kurtosis, and count distributions with segregated
zero and non-finite tracking.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats


def rolling_summary(
    times: np.ndarray,
    values: np.ndarray,
    window_seconds: float = 60.0,
    stride: int = 1,
) -> Dict[str, Any]:
    """Compute rolling median and robust standard deviation over a time-based window.
    
    METHODOLOGICAL RATIONALE:
    A physical time-based window [t - W/2, t + W/2] is used instead of an index-based
    window. Astronomical time series frequently contain sampling jitter, variable integration
    times, or telemetry dropouts. An index-based window would stretch or compress in physical
    duration across missing intervals, corrupting transient timescale estimation. A time-based
    window guarantees a constant physical window duration across all observations.
    
    Non-finite samples (NaN, +inf, -inf) are strictly excluded from window calculations
    and counted.
    
    Parameters
    ----------
    times : np.ndarray
        Observation timestamps in seconds.
    values : np.ndarray
        Light-curve count or count-rate values.
    window_seconds : float
        Physical window duration in seconds (from config).
    stride : int
        Step size for rolling calculation (default 1 for full resolution).
        
    Returns
    -------
    dict
        Rolling statistics:
        - "times": evaluated timestamps
        - "rolling_median": rolling median array
        - "rolling_robust_std": rolling robust dispersion (1.4826 * MAD)
        - "n_samples_in_window": average count of finite samples per window
        - "n_excluded_total": total non-finite samples encountered
        - "window_seconds": configured physical window duration
    """
    t_arr = np.asarray(times, dtype=np.float64)
    v_arr = np.asarray(values, dtype=np.float64)
    n = len(t_arr)

    if n == 0:
        return {
            "times": np.array([]),
            "rolling_median": np.array([]),
            "rolling_robust_std": np.array([]),
            "n_samples_in_window": 0.0,
            "n_excluded_total": 0,
            "window_seconds": window_seconds,
        }

    half_win = window_seconds / 2.0
    left_indices = np.searchsorted(t_arr, t_arr - half_win, side="left")
    right_indices = np.searchsorted(t_arr, t_arr + half_win, side="right")

    eval_indices = np.arange(0, n, stride)
    n_eval = len(eval_indices)

    roll_med = np.full(n_eval, np.nan, dtype=np.float64)
    roll_std = np.full(n_eval, np.nan, dtype=np.float64)
    counts_in_win = np.zeros(n_eval, dtype=np.int32)
    total_excluded = int(np.isnan(v_arr).sum() + np.isinf(v_arr).sum())

    for i, idx in enumerate(eval_indices):
        l = left_indices[idx]
        r = right_indices[idx]
        w_vals = v_arr[l:r]
        finite_mask = np.isfinite(w_vals)
        f_vals = w_vals[finite_mask]
        counts_in_win[i] = len(f_vals)

        if len(f_vals) > 0:
            m = float(np.median(f_vals))
            roll_med[i] = m
            # Robust MAD dispersion
            mad = float(np.median(np.abs(f_vals - m)))
            if mad > 1e-12:
                roll_std[i] = 1.4826 * mad
            else:
                mean_ad = float(np.mean(np.abs(f_vals - m)))
                roll_std[i] = 1.2533 * mean_ad if mean_ad > 1e-12 else 0.0

    return {
        "times": t_arr[eval_indices],
        "rolling_median": roll_med,
        "rolling_robust_std": roll_std,
        "n_samples_in_window": float(np.mean(counts_in_win)) if n_eval > 0 else 0.0,
        "n_excluded_total": total_excluded,
        "window_seconds": float(window_seconds),
    }


def variability_stats(values: np.ndarray) -> Dict[str, Any]:
    """Compute non-parametric and parametric variability statistics on finite values.
    
    Excludes all non-finite values and reports the count of excluded samples.
    
    Parameters
    ----------
    values : np.ndarray
        Array of count or rate values.
        
    Returns
    -------
    dict
        Comprehensive variability summary:
        mean, std, cv, median, mad, mad_dispersion, iqr, skewness, kurtosis,
        n_finite, n_excluded.
    """
    arr = np.asarray(values, dtype=np.float64)
    total_samples = len(arr)
    finite_mask = np.isfinite(arr)
    f_vals = arr[finite_mask]
    n_finite = int(len(f_vals))
    n_excluded = int(total_samples - n_finite)

    if n_finite == 0:
        return {
            "mean": None,
            "std": None,
            "cv": None,
            "median": None,
            "mad": None,
            "mad_dispersion": None,
            "iqr": None,
            "skewness": None,
            "kurtosis": None,
            "n_finite": 0,
            "n_excluded": n_excluded,
        }

    mean_v = float(np.mean(f_vals))
    std_v = float(np.std(f_vals, ddof=1)) if n_finite > 1 else 0.0
    cv_v = float(std_v / mean_v) if abs(mean_v) > 1e-12 else 0.0

    med_v = float(np.median(f_vals))
    mad_v = float(np.median(np.abs(f_vals - med_v)))
    mad_disp = float(1.4826 * mad_v)

    q25, q75 = np.percentile(f_vals, [25.0, 75.0])
    iqr_v = float(q75 - q25)

    skew_v = float(stats.skew(f_vals, bias=False)) if n_finite > 2 and std_v > 1e-12 else 0.0
    kurt_v = float(stats.kurtosis(f_vals, bias=False)) if n_finite > 3 and std_v > 1e-12 else 0.0

    return {
        "mean": mean_v,
        "std": std_v,
        "cv": cv_v,
        "median": med_v,
        "mad": mad_v,
        "mad_dispersion": mad_disp,
        "iqr": iqr_v,
        "skewness": skew_v,
        "kurtosis": kurt_v,
        "n_finite": n_finite,
        "n_excluded": n_excluded,
    }


def count_histogram_data(
    values: np.ndarray,
    bins: int = 50,
) -> Dict[str, Any]:
    """Compute histogram arrays with separate reporting for zero counts and non-finite samples.
    
    Parameters
    ----------
    values : np.ndarray
        Array of count values.
    bins : int
        Number of histogram bins for positive counts.
        
    Returns
    -------
    dict
        Histogram edges, counts, and segregated counts for zero and non-finite samples.
    """
    arr = np.asarray(values, dtype=np.float64)
    n_non_finite = int(np.isnan(arr).sum() + np.isinf(arr).sum())
    finite_mask = np.isfinite(arr)
    f_vals = arr[finite_mask]

    n_zeros = int((f_vals == 0.0).sum())
    pos_vals = f_vals[f_vals > 0.0]
    n_pos = int(len(pos_vals))

    if n_pos > 0:
        counts, edges = np.histogram(pos_vals, bins=bins)
        bin_counts = [int(c) for c in counts]
        bin_edges = [float(e) for e in edges]
    else:
        bin_counts = []
        bin_edges = []

    return {
        "bin_edges": bin_edges,
        "counts": bin_counts,
        "n_zeros": n_zeros,
        "n_non_finite": n_non_finite,
        "n_positive": n_pos,
        "n_finite": int(len(f_vals)),
        "total_samples": len(arr),
    }
