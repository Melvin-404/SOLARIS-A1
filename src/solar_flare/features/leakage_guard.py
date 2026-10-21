"""Temporal leakage guards and acausal verification for SOLARIS-A1 (Stage 8).

Verifies provable causality:
Every observation sample used in computing window i features must satisfy:
    sample_time <= window_end_i
Raises LeakageError if any future observation is accessed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd


class LeakageError(RuntimeError):
    """Raised when acausal future sample contamination is detected in sliding windows."""
    pass


def check_no_future_samples(
    window_index_df: pd.DataFrame,
    feature_inputs_log: Optional[Union[pd.DataFrame, List[Dict[str, Any]]]] = None,
    time_col: str = "TIME",
    tolerance_seconds: float = 1e-6,
) -> bool:
    """Verify that no sample used in feature computation occurs after window_end.
    
    Inspects actual recorded sample provenance (max_time_used) against window_end.
    
    Parameters
    ----------
    window_index_df : pd.DataFrame
        Window metadata containing 'window_id', 'window_end', and 'max_time_used'.
    feature_inputs_log : Optional[DataFrame or list]
        Explicit sample log per window if tracked separately.
    time_col : str
        Timestamp column name.
    tolerance_seconds : float
        Numerical epsilon to account for floating point equality.
        
    Returns
    -------
    bool
        True if all windows strictly satisfy sample_time <= window_end.
        
    Raises
    -------
    LeakageError
        If any future observation is detected within any window.
    """
    if window_index_df.empty:
        return True

    violations: List[Dict[str, Any]] = []

    # Check 1: Using max_time_used recorded in window_index_df
    if "max_time_used" in window_index_df.columns and "window_end" in window_index_df.columns:
        for idx, row in window_index_df.iterrows():
            win_id = row.get("window_id", f"row_{idx}")
            w_end = float(row["window_end"])
            max_t = float(row["max_time_used"])

            if max_t > (w_end + tolerance_seconds):
                excess = max_t - w_end
                violations.append({
                    "window_id": win_id,
                    "window_end": w_end,
                    "max_time_used": max_t,
                    "future_leakage_seconds": round(excess, 6),
                })

    # Check 2: Inspect feature_inputs_log if provided
    if feature_inputs_log is not None:
        log_df = pd.DataFrame(feature_inputs_log)
        if not log_df.empty and "window_end" in log_df.columns and "sample_time" in log_df.columns:
            leaks = log_df[log_df["sample_time"] > (log_df["window_end"] + tolerance_seconds)]
            for _, r in leaks.iterrows():
                violations.append({
                    "window_id": r.get("window_id", "UNKNOWN"),
                    "window_end": float(r["window_end"]),
                    "sample_time": float(r["sample_time"]),
                    "future_leakage_seconds": float(r["sample_time"] - r["window_end"]),
                })

    if violations:
        msg_lines = [
            f"CRITICAL TEMPORAL LEAKAGE DETECTED in {len(violations)} sliding window(s):",
            "Samples with timestamp t > window_end (t_0 reference time) were accessed during feature extraction.",
        ]
        for v in violations[:10]:
            msg_lines.append(
                f"  - Window '{v['window_id']}': window_end={v['window_end']}, "
                f"sample_time={v.get('max_time_used', v.get('sample_time'))} "
                f"(leakage: +{v['future_leakage_seconds']:.6f}s)"
            )
        if len(violations) > 10:
            msg_lines.append(f"  ... and {len(violations) - 10} more windows.")
        raise LeakageError("\n".join(msg_lines))

    return True


def check_inputs_causal(
    feature_table: pd.DataFrame,
    t0_column: str = "window_end",
    observation_times_column: Optional[str] = "max_time_used",
) -> bool:
    """Verify that a feature table satisfies causality against a designated t_0 reference.
    
    Provided for reusability across Stage 8 and Stage 15 (Forecasting / Pre-flare horizon).
    
    Parameters
    ----------
    feature_table : pd.DataFrame
        Table of extracted feature vectors.
    t0_column : str
        Name of reference prediction epoch column.
    observation_times_column : Optional[str]
        Column storing the latest observation time included in the feature vector.
        
    Returns
    -------
    bool
        True if all rows satisfy latest_time <= t0.
        
    Raises
    -------
    LeakageError
        If any row violates causality.
    """
    if feature_table.empty or observation_times_column not in feature_table.columns or t0_column not in feature_table.columns:
        return True

    t0_vals = feature_table[t0_column].to_numpy(dtype=np.float64)
    obs_vals = feature_table[observation_times_column].to_numpy(dtype=np.float64)

    leak_mask = obs_vals > (t0_vals + 1e-6)
    if np.any(leak_mask):
        n_leaks = int(np.sum(leak_mask))
        raise LeakageError(
            f"Causality violation in feature table: {n_leaks} rows contain observations after reference epoch '{t0_column}'."
        )

    return True
