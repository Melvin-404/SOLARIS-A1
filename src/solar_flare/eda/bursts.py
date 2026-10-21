"""Candidate transient burst identification for SOLARIS-A1 (Stage 5).

EXPLORATORY ONLY:
All detected intervals are strictly exploratory and labelled 'CANDIDATE — UNVERIFIED'.
No candidate produced here is a solar flare label, ground truth, or training target.
Output must NEVER be written to datasets or label paths.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def robust_baseline(
    times: np.ndarray,
    values: np.ndarray,
    span_seconds: float = 600.0,
    eval_step_seconds: Optional[float] = None,
) -> np.ndarray:
    """Compute a robust running median baseline with explicit edge handling.
    
    EDGE HANDLING METHODOLOGY:
    For any sample time t_i, the nominal window is [t_i - span/2, t_i + span/2].
    Near the observation boundaries:
    - Left edge: If t_i - span/2 < t_start, the window is truncated to [t_start, t_i + span/2]
      and the median is calculated from all finite samples in that asymmetric window.
    - Right edge: If t_i + span/2 > t_end, the window is truncated to [t_i - span/2, t_end]
      and the median is calculated from available finite samples.
    - Gaps/Voids: If a window contains zero finite samples, the global median of finite
      samples across the entire series is assigned.
      
    Parameters
    ----------
    times : np.ndarray
        Array of observation timestamps in seconds.
    values : np.ndarray
        Array of count values.
    span_seconds : float
        Physical time span for running median filter (from config, marked PROVISIONAL).
    eval_step_seconds : Optional[float]
        Evaluation grid resolution in seconds. If None, automatically determined.
        
    Returns
    -------
    np.ndarray
        Baseline array matching the shape of values.
    """
    t_arr = np.asarray(times, dtype=np.float64)
    v_arr = np.asarray(values, dtype=np.float64)
    n = len(t_arr)

    if n == 0:
        return np.array([], dtype=np.float64)

    finite_mask = np.isfinite(v_arr)
    if not np.any(finite_mask):
        return np.full(n, np.nan, dtype=np.float64)

    global_med = float(np.median(v_arr[finite_mask]))
    half_span = span_seconds / 2.0

    # Determine evaluation grid for performance on large series
    if n > 1000 and (t_arr[-1] - t_arr[0]) > span_seconds:
        step_s = eval_step_seconds or max(1.0, min(10.0, span_seconds / 60.0))
        grid_times = np.arange(t_arr[0], t_arr[-1] + step_s, step_s)
    else:
        grid_times = t_arr

    left_idx = np.searchsorted(t_arr, grid_times - half_span, side="left")
    right_idx = np.searchsorted(t_arr, grid_times + half_span, side="right")

    grid_medians = np.zeros(len(grid_times), dtype=np.float64)
    for i in range(len(grid_times)):
        l = left_idx[i]
        r = right_idx[i]
        w = v_arr[l:r]
        w_finite = w[np.isfinite(w)]
        if len(w_finite) > 0:
            grid_medians[i] = float(np.median(w_finite))
        else:
            grid_medians[i] = global_med

    # Interpolate grid medians back to sample timestamps
    if len(grid_times) == n and np.array_equal(grid_times, t_arr):
        return grid_medians

    baseline = np.interp(t_arr, grid_times, grid_medians)
    return baseline


def candidate_intervals(
    times: np.ndarray,
    values: np.ndarray,
    baseline: np.ndarray,
    threshold_sigma: float = 5.0,
    min_duration_seconds: float = 10.0,
) -> pd.DataFrame:
    """Identify contiguous candidate transient burst intervals above baseline.
    
    EXPLORATORY CANDIDATE DETECTION ONLY:
    Every candidate is strictly tagged as 'CANDIDATE — UNVERIFIED'.
    No candidate may be considered a verified solar flare without external catalog
    validation and human researcher approval at Gate G3.
    
    Parameters
    ----------
    times : np.ndarray
        Observation timestamps in seconds.
    values : np.ndarray
        Observed count values.
    baseline : np.ndarray
        Baseline counts (from robust_baseline).
    threshold_sigma : float
        Dispersion multiplier (from config, marked PROVISIONAL).
    min_duration_seconds : float
        Minimum contiguous time in seconds above threshold to flag a candidate.
        
    Returns
    -------
    pd.DataFrame
        Table with exact schema:
        candidate_id, start, end, duration, peak_time, peak_value,
        peak_to_baseline_ratio, n_samples, status.
    """
    columns = [
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

    t_arr = np.asarray(times, dtype=np.float64)
    v_arr = np.asarray(values, dtype=np.float64)
    b_arr = np.asarray(baseline, dtype=np.float64)
    n = len(t_arr)

    if n == 0:
        return pd.DataFrame(columns=columns)

    finite_mask = np.isfinite(v_arr) & np.isfinite(b_arr)
    if not np.any(finite_mask):
        return pd.DataFrame(columns=columns)

    diff = v_arr - b_arr
    diff_finite = diff[finite_mask]

    # Robust MAD dispersion around median residual
    diff_med = float(np.median(diff_finite))
    mad = float(np.median(np.abs(diff_finite - diff_med)))
    dispersion = 1.4826 * mad
    if dispersion <= 1e-12:
        mean_ad = float(np.mean(np.abs(diff_finite - diff_med)))
        dispersion = 1.2533 * mean_ad if mean_ad > 1e-12 else 1.0

    threshold = b_arr + threshold_sigma * dispersion
    above = (v_arr > threshold) & finite_mask

    # Find contiguous blocks where above == True
    records: List[Dict[str, Any]] = []
    padded = np.empty(n + 2, dtype=bool)
    padded[0] = False
    padded[-1] = False
    padded[1:-1] = above

    diffs = np.diff(padded.astype(np.int8))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0] - 1  # inclusive index

    cand_count = 1
    for s_idx, e_idx in zip(starts, ends):
        t_start = float(t_arr[s_idx])
        t_end = float(t_arr[e_idx])
        duration = float(t_end - t_start)

        # In case single bin or step
        cadence_step = (t_arr[1] - t_arr[0]) if n > 1 else 1.0
        effective_duration = max(duration, float(e_idx - s_idx + 1) * cadence_step)

        if duration >= min_duration_seconds or effective_duration >= min_duration_seconds:
            sub_vals = v_arr[s_idx : e_idx + 1]
            rel_peak = int(np.argmax(sub_vals))
            p_idx = s_idx + rel_peak

            peak_t = float(t_arr[p_idx])
            peak_v = float(v_arr[p_idx])
            base_at_p = float(b_arr[p_idx])
            ratio = float(peak_v / base_at_p) if abs(base_at_p) > 1e-6 else 0.0

            records.append({
                "candidate_id": f"CAND_{cand_count:03d}",
                "start": t_start,
                "end": t_end,
                "duration": duration,
                "peak_time": peak_t,
                "peak_value": peak_v,
                "peak_to_baseline_ratio": ratio,
                "n_samples": int(e_idx - s_idx + 1),
                "status": "CANDIDATE — UNVERIFIED",
            })
            cand_count += 1

    df = pd.DataFrame(records, columns=columns)
    return df
