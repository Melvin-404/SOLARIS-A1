"""Cadence estimation and gap analysis for SOLARIS-A1 (Stage 4).

All cadence metrics are derived empirically from timestamp differences.
Gaps are flagged when timestamp step exceeds expected_cadence * tolerance_factor.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np


def estimate_cadence(times: np.ndarray, round_decimals: int = 4) -> Dict[str, Any]:
    """Derive empirical cadence statistics from positive timestamp differences.
    
    Parameters
    ----------
    times : np.ndarray
        Array of observation timestamps.
    round_decimals : int
        Decimal precision for mode calculation on floating-point steps.
        
    Returns
    -------
    dict
        Empirical cadence statistics: median, mode, min, max, std, and sample counts.
    """
    t_arr = np.asarray(times, dtype=np.float64)
    total_samples = int(len(t_arr))
    if total_samples <= 1:
        return {
            "status": "NOT_APPLICABLE",
            "cadence_median": None,
            "cadence_mode": None,
            "cadence_min": None,
            "cadence_max": None,
            "cadence_std": None,
            "n_positive_diffs": 0,
            "total_samples": total_samples,
            "detail": "Timestamp array has fewer than 2 elements.",
        }

    diffs = np.diff(t_arr)
    pos_diffs = diffs[diffs > 0]
    n_pos = int(len(pos_diffs))

    if n_pos == 0:
        return {
            "status": "WARN",
            "cadence_median": None,
            "cadence_mode": None,
            "cadence_min": None,
            "cadence_max": None,
            "cadence_std": None,
            "n_positive_diffs": 0,
            "total_samples": total_samples,
            "detail": "No positive timestamp differences observed.",
        }

    med = float(np.median(pos_diffs))
    min_d = float(np.min(pos_diffs))
    max_d = float(np.max(pos_diffs))
    std_d = float(np.std(pos_diffs))

    # Calculate empirical mode
    rounded = np.round(pos_diffs, round_decimals)
    unique_vals, counts = np.unique(rounded, return_counts=True)
    mode_val = float(unique_vals[np.argmax(counts)])

    return {
        "status": "PASS",
        "cadence_median": med,
        "cadence_mode": mode_val,
        "cadence_min": min_d,
        "cadence_max": max_d,
        "cadence_std": std_d,
        "n_positive_diffs": n_pos,
        "total_samples": total_samples,
        "detail": (
            f"Derived cadence: median = {med:.4f} s, mode = {mode_val:.4f} s, "
            f"min = {min_d:.4f} s, max = {max_d:.4f} s, std = {std_d:.4f} s."
        ),
    }


def find_cadence_gaps(
    times: np.ndarray,
    expected_cadence: Optional[float] = None,
    tolerance_factor: float = 1.5,
) -> Dict[str, Any]:
    """Identify gaps in observation timestamps exceeding tolerance threshold.
    
    Parameters
    ----------
    times : np.ndarray
        Array of observation timestamps.
    expected_cadence : Optional[float]
        Nominal cadence in seconds. If None, derived from median of positive steps.
    tolerance_factor : float
        Tolerance multiplier (from config, marked PROVISIONAL).
        
    Returns
    -------
    dict
        Structured gap analysis containing list of identified gaps and total gap duration.
    """
    t_arr = np.asarray(times, dtype=np.float64)
    total_samples = int(len(t_arr))
    if total_samples <= 1:
        return {
            "status": "NOT_APPLICABLE",
            "n_cadence_gaps": 0,
            "gaps": [],
            "total_gap_duration_s": 0.0,
            "expected_cadence": expected_cadence,
            "tolerance_factor": tolerance_factor,
            "threshold_s": None,
            "detail": "Insufficient timestamps to analyze cadence gaps.",
        }

    diffs = np.diff(t_arr)

    # Derive expected cadence if not explicitly passed
    if expected_cadence is None:
        cadence_stats = estimate_cadence(t_arr)
        expected_cadence = cadence_stats.get("cadence_median")

    if expected_cadence is None or expected_cadence <= 0:
        return {
            "status": "WARN",
            "n_cadence_gaps": 0,
            "gaps": [],
            "total_gap_duration_s": 0.0,
            "expected_cadence": None,
            "tolerance_factor": tolerance_factor,
            "threshold_s": None,
            "detail": "Expected cadence could not be derived from timestamps.",
        }

    threshold_s = expected_cadence * tolerance_factor
    gap_indices = np.where(diffs > threshold_s)[0]
    n_gaps = int(len(gap_indices))

    gaps: List[Dict[str, Any]] = []
    total_gap_duration = 0.0

    for idx in gap_indices:
        dt = float(diffs[idx])
        total_gap_duration += dt
        gaps.append({
            "gap_index": int(idx),
            "start_time": float(t_arr[idx]),
            "end_time": float(t_arr[idx + 1]),
            "duration_s": dt,
            "missing_steps_estimated": max(0, int(round(dt / expected_cadence)) - 1),
        })

    status = "PASS" if n_gaps == 0 else "WARN"

    return {
        "status": status,
        "n_cadence_gaps": n_gaps,
        "gaps": gaps,
        "total_gap_duration_s": total_gap_duration,
        "expected_cadence": float(expected_cadence),
        "tolerance_factor": float(tolerance_factor),
        "threshold_s": float(threshold_s),
        "detail": (
            "No cadence gaps detected above threshold."
            if n_gaps == 0
            else f"Detected {n_gaps} cadence gaps (step > {threshold_s:.2f} s), total missing duration: {total_gap_duration:.2f} s."
        ),
    }
