"""Pure functional quality checks for SOLARIS-A1 (Stage 4).

All functions are pure: no disk I/O, no network calls, no mutating operations.
Non-finite, negative, zero, and flagged samples are strictly segregated.
Candidate spikes are computed using robust MAD statistics and labelled
"candidate spike — not a verified event".
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np


def check_non_finite(values: np.ndarray) -> Dict[str, Any]:
    """Inspect array for NaN, positive infinity, and negative infinity.
    
    Parameters
    ----------
    values : np.ndarray
        Numeric array of count or rate values.
        
    Returns
    -------
    dict
        Structured check result with exact counts for NaN, +inf, and -inf.
    """
    arr = np.asarray(values, dtype=np.float64)
    total_samples = int(len(arr))
    n_nan = int(np.isnan(arr).sum())
    n_pos_inf = int(np.isposinf(arr).sum())
    n_neg_inf = int(np.isneginf(arr).sum())
    n_non_finite = n_nan + n_pos_inf + n_neg_inf

    status = "PASS" if n_non_finite == 0 else "WARN"

    return {
        "name": "check_non_finite",
        "status": status,
        "counts": {
            "total_samples": total_samples,
            "n_nan": n_nan,
            "n_pos_inf": n_pos_inf,
            "n_neg_inf": n_neg_inf,
            "n_non_finite": n_non_finite,
        },
        "detail": (
            "No non-finite samples observed."
            if n_non_finite == 0
            else f"Observed {n_nan} NaNs, {n_pos_inf} +inf, and {n_neg_inf} -inf samples."
        ),
    }


def check_negative_values(values: np.ndarray) -> Dict[str, Any]:
    """Check for negative count or rate values without clipping.
    
    Parameters
    ----------
    values : np.ndarray
        Numeric array of count or rate values.
        
    Returns
    -------
    dict
        Structured check result counting negative values. Never modifies data.
    """
    arr = np.asarray(values, dtype=np.float64)
    finite_mask = np.isfinite(arr)
    negative_mask = finite_mask & (arr < 0)
    n_negative = int(negative_mask.sum())
    min_val = float(np.min(arr[finite_mask])) if np.any(finite_mask) else None

    status = "PASS" if n_negative == 0 else "FAIL"

    return {
        "name": "check_negative_values",
        "status": status,
        "counts": {
            "total_samples": int(len(arr)),
            "n_negative": n_negative,
        },
        "detail": {
            "min_finite_value": min_val,
            "message": (
                "No negative values detected."
                if n_negative == 0
                else f"Found {n_negative} negative values. Minimum value is {min_val}."
            ),
        },
    }


def check_duplicate_timestamps(times: np.ndarray, max_examples: int = 5) -> Dict[str, Any]:
    """Detect duplicate timestamps and report count and first occurrences.
    
    Parameters
    ----------
    times : np.ndarray
        Array of observation timestamps.
    max_examples : int
        Maximum number of example duplicates to list.
        
    Returns
    -------
    dict
        Structured check result with duplicate count and examples.
    """
    t_arr = np.asarray(times)
    total_samples = int(len(t_arr))
    if total_samples == 0:
        return {
            "name": "check_duplicate_timestamps",
            "status": "PASS",
            "counts": {"total_samples": 0, "n_duplicates": 0},
            "detail": "Empty timestamp array.",
        }

    unique_vals, counts = np.unique(t_arr, return_counts=True)
    dup_mask = counts > 1
    n_duplicate_timestamps = int((counts[dup_mask] - 1).sum())

    examples = []
    dup_vals = unique_vals[dup_mask]
    for val in dup_vals[:max_examples]:
        indices = np.where(t_arr == val)[0].tolist()
        examples.append({
            "timestamp": float(val) if np.issubdtype(type(val), np.number) else str(val),
            "occurrences": len(indices),
            "indices": indices[:5],
        })

    status = "PASS" if n_duplicate_timestamps == 0 else "WARN"

    return {
        "name": "check_duplicate_timestamps",
        "status": status,
        "counts": {
            "total_samples": total_samples,
            "n_duplicates": n_duplicate_timestamps,
            "n_unique": int(len(unique_vals)),
        },
        "detail": {
            "message": (
                "All timestamps are unique."
                if n_duplicate_timestamps == 0
                else f"Found {n_duplicate_timestamps} duplicate timestamp occurrences."
            ),
            "examples": examples,
        },
    }


def check_time_ordering(times: np.ndarray, max_examples: int = 5) -> Dict[str, Any]:
    """Check that timestamps are strictly non-decreasing (no backward steps).
    
    Parameters
    ----------
    times : np.ndarray
        Array of observation timestamps.
    max_examples : int
        Maximum number of backward steps to report in detail.
        
    Returns
    -------
    dict
        Structured check result counting backward time steps.
    """
    t_arr = np.asarray(times, dtype=np.float64)
    total_samples = int(len(t_arr))
    if total_samples <= 1:
        return {
            "name": "check_time_ordering",
            "status": "PASS",
            "counts": {"total_samples": total_samples, "n_backward_steps": 0},
            "detail": "Array contains <= 1 timestamp; time ordering trivially satisfied.",
        }

    diffs = np.diff(t_arr)
    backward_indices = np.where(diffs < 0)[0]
    n_backward = int(len(backward_indices))

    examples = []
    for idx in backward_indices[:max_examples]:
        examples.append({
            "step_index": int(idx),
            "t_current": float(t_arr[idx]),
            "t_next": float(t_arr[idx + 1]),
            "delta_t": float(diffs[idx]),
        })

    status = "PASS" if n_backward == 0 else "FAIL"

    return {
        "name": "check_time_ordering",
        "status": status,
        "counts": {
            "total_samples": total_samples,
            "n_backward_steps": n_backward,
        },
        "detail": {
            "message": (
                "Timestamps are strictly non-decreasing."
                if n_backward == 0
                else f"Detected {n_backward} backward time steps."
            ),
            "examples": examples,
        },
    }


def check_zero_runs(
    values: np.ndarray,
    times: Optional[np.ndarray] = None,
    min_run_length: int = 5,
) -> Dict[str, Any]:
    """Identify contiguous runs of finite zero counts, segregated from NaNs.
    
    Parameters
    ----------
    values : np.ndarray
        Numeric array of count or rate values.
    times : Optional[np.ndarray]
        Matching array of timestamps for duration computation.
    min_run_length : int
        Minimum contiguous zero samples to record as a tracked run.
        
    Returns
    -------
    dict
        Structured check result with zero count and contiguous run diagnostics.
    """
    arr = np.asarray(values, dtype=np.float64)
    t_arr = np.asarray(times, dtype=np.float64) if times is not None else None
    total_samples = int(len(arr))

    # Segregate strictly finite zeros from NaNs and infinities
    finite_mask = np.isfinite(arr)
    zero_mask = finite_mask & (arr == 0.0)
    n_zero_samples = int(zero_mask.sum())

    runs: List[Dict[str, Any]] = []
    if total_samples > 0:
        # Detect runs of True in zero_mask
        padded = np.empty(total_samples + 2, dtype=bool)
        padded[0] = False
        padded[-1] = False
        padded[1:-1] = zero_mask

        diffs = np.diff(padded.astype(np.int8))
        run_starts = np.where(diffs == 1)[0]
        run_ends = np.where(diffs == -1)[0]  # exclusive index in arr

        for start, end in zip(run_starts, run_ends):
            length = int(end - start)
            if length >= min_run_length:
                run_info: Dict[str, Any] = {
                    "start_idx": int(start),
                    "end_idx": int(end - 1),
                    "length": length,
                }
                if t_arr is not None and len(t_arr) == total_samples:
                    run_info["start_time"] = float(t_arr[start])
                    run_info["end_time"] = float(t_arr[end - 1])
                    run_info["duration_s"] = float(t_arr[end - 1] - t_arr[start])
                runs.append(run_info)

    max_run_len = max([r["length"] for r in runs], default=0)
    status = "PASS" if len(runs) == 0 else "WARN"

    return {
        "name": "check_zero_runs",
        "status": status,
        "counts": {
            "total_samples": total_samples,
            "n_zero_samples": n_zero_samples,
            "n_zero_runs": len(runs),
            "max_zero_run_length": max_run_len,
            "min_run_length_threshold": min_run_length,
        },
        "detail": {
            "runs": runs,
            "message": (
                f"Observed {n_zero_samples} zero counts across {len(runs)} runs "
                f"(run length >= {min_run_length}). Maximum run length: {max_run_len} samples."
            ),
        },
    }


def check_quality_flags(
    flags: Optional[np.ndarray],
    confirmed_meanings: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Tabulate quality flag distribution. Interpretation is UNRESOLVED until G1.
    
    Parameters
    ----------
    flags : Optional[np.ndarray]
        Array of raw integer quality flags, or None if no flag column exists.
    confirmed_meanings : Optional[dict]
        Mapping from flag value/bitmask to confirmed scientific meaning.
        
    Returns
    -------
    dict
        Structured check result with raw distribution and unresolved notice.
    """
    if flags is None or len(flags) == 0:
        return {
            "name": "check_quality_flags",
            "status": "NOT_APPLICABLE",
            "counts": {"total_samples": 0},
            "detail": "No quality flag column available or column is null (UNRESOLVED pending G1).",
        }

    f_arr = np.asarray(flags)
    unique_vals, counts = np.unique(f_arr, return_counts=True)
    distribution = {str(val): int(cnt) for val, cnt in zip(unique_vals, counts)}

    if confirmed_meanings is None or len(confirmed_meanings) == 0:
        interpretation = "UNRESOLVED: flag meanings are not CONFIRMED. Raw distribution reported only."
        status = "WARN"
    else:
        interpretation = "CONFIRMED flag definitions applied."
        status = "PASS"

    return {
        "name": "check_quality_flags",
        "status": status,
        "counts": {
            "total_samples": int(len(f_arr)),
            "distribution": distribution,
        },
        "detail": {
            "interpretation_status": interpretation,
            "note": "requires human confirmation (G1)",
        },
    }


def check_candidate_spikes(
    values: np.ndarray,
    times: Optional[np.ndarray] = None,
    z_threshold: float = 5.0,
    max_examples: int = 10,
) -> Dict[str, Any]:
    """Compute robust z-scores via Median and MAD to identify candidate statistical spikes.
    
    CRITICAL: Labelled strictly as 'candidate spike — not a verified event'.
    Does not declare any solar flare or physical phenomenon.
    
    Parameters
    ----------
    values : np.ndarray
        Numeric array of count or rate values.
    times : Optional[np.ndarray]
        Matching array of timestamps.
    z_threshold : float
        Robust z-score threshold (from config).
    max_examples : int
        Maximum number of examples to include in detail.
        
    Returns
    -------
    dict
        Structured check result with candidate spike counts and statistics.
    """
    arr = np.asarray(values, dtype=np.float64)
    total_samples = int(len(arr))
    finite_mask = np.isfinite(arr)
    finite_vals = arr[finite_mask]

    if len(finite_vals) == 0:
        return {
            "name": "check_candidate_spikes",
            "status": "NOT_APPLICABLE",
            "counts": {"total_samples": total_samples, "n_candidate_spikes": 0},
            "detail": "No finite samples available to compute robust statistics.",
        }

    med = float(np.median(finite_vals))
    mad = float(np.median(np.abs(finite_vals - med)))
    # Normal consistency scale factor
    mad_scale = 1.4826 * mad

    # Fallback to Mean Absolute Deviation if MAD is zero (e.g., >50% identical values)
    if mad_scale <= 1e-12:
        mean_ad = float(np.mean(np.abs(finite_vals - med)))
        mad_scale = 1.2533 * mean_ad if mean_ad > 1e-12 else 0.0

    examples: List[Dict[str, Any]] = []
    if mad_scale > 1e-12:
        robust_z = (finite_vals - med) / mad_scale
        spike_mask_finite = robust_z > z_threshold
        n_spikes = int(spike_mask_finite.sum())
        spike_finite_indices = np.where(spike_mask_finite)[0]

        orig_indices = np.where(finite_mask)[0][spike_finite_indices]
        for idx, f_idx in zip(orig_indices[:max_examples], spike_finite_indices[:max_examples]):
            ex: Dict[str, Any] = {
                "index": int(idx),
                "value": float(arr[idx]),
                "robust_z": float(robust_z[f_idx]),
                "label": "candidate spike — not a verified event",
            }
            if times is not None and len(times) == total_samples:
                ex["time"] = float(times[idx])
            examples.append(ex)
    else:
        n_spikes = 0

    status = "PASS" if n_spikes == 0 else "WARN"

    return {
        "name": "check_candidate_spikes",
        "status": status,
        "counts": {
            "total_samples": total_samples,
            "n_candidate_spikes": n_spikes,
            "median": med,
            "mad": mad,
            "z_threshold": z_threshold,
        },
        "detail": {
            "label": "candidate spike — not a verified event",
            "message": (
                f"Detected {n_spikes} statistical candidate spikes with robust z > {z_threshold}. "
                "These are statistical anomalies only and MUST NOT be interpreted as solar flares."
            ),
            "examples": examples,
        },
    }
