"""Sample filtering and sorting functions for SOLARIS-A1 (Stage 7).

Every function accepts a DataFrame and returns a tuple of:
  (filtered_df, exclusion_log_df)
Original columns are preserved. Every sample removed is explicitly recorded with
original index, timestamp, exclusion reason, and numeric value.

PROHIBITION: No data estimation, reconstruction, or gap substitution is performed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np
import pandas as pd

EXCLUSION_COLUMNS = ["original_index", "time", "reason", "value", "details"]


class DuplicateTimestampError(ValueError):
    """Raised when duplicate timestamps are encountered under policy='ERROR'."""
    pass


def _create_empty_exclusion_log() -> pd.DataFrame:
    """Return an empty DataFrame formatted for exclusion logging."""
    return pd.DataFrame(columns=EXCLUSION_COLUMNS)


def _build_exclusion_log(
    df: pd.DataFrame,
    dropped_mask: pd.Series,
    time_col: Optional[str],
    reason: str,
    value_col: Optional[str] = None,
    details_prefix: str = "",
) -> pd.DataFrame:
    """Construct an exclusion log DataFrame for dropped rows."""
    if not dropped_mask.any():
        return _create_empty_exclusion_log()

    dropped_df = df[dropped_mask]
    records: List[Dict[str, Any]] = []

    for idx, row in dropped_df.iterrows():
        t_val = row[time_col] if (time_col and time_col in row) else None
        v_val = row[value_col] if (value_col and value_col in row) else None
        records.append({
            "original_index": idx,
            "time": t_val,
            "reason": reason,
            "value": v_val,
            "details": f"{details_prefix} (index={idx})",
        })

    return pd.DataFrame(records, columns=EXCLUSION_COLUMNS)


def exclude_non_finite(
    df: pd.DataFrame,
    value_col: str,
    time_col: Optional[str] = "TIME",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Exclude non-finite samples (NaN, +inf, -inf) from light curve.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input observations.
    value_col : str
        Target column to inspect for non-finite values (e.g. 'COUNTS').
    time_col : Optional[str]
        Timestamp column for logging.
        
    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        (filtered_df, exclusion_log_df)
    """
    if df.empty or value_col not in df.columns:
        return df.copy(), _create_empty_exclusion_log()

    vals = df[value_col]
    non_finite_mask = ~np.isfinite(vals)

    if not non_finite_mask.any():
        return df.copy(), _create_empty_exclusion_log()

    exclusion_log = _build_exclusion_log(
        df=df,
        dropped_mask=non_finite_mask,
        time_col=time_col if (time_col and time_col in df.columns) else None,
        reason="NON_FINITE",
        value_col=value_col,
        details_prefix=f"Non-finite value in column '{value_col}'",
    )

    filtered_df = df[~non_finite_mask].copy()
    return filtered_df, exclusion_log


def exclude_negative(
    df: pd.DataFrame,
    value_col: str,
    time_col: Optional[str] = "TIME",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Exclude samples with negative count values without clipping or mutating.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input observations.
    value_col : str
        Target column to inspect for negative values.
    time_col : Optional[str]
        Timestamp column for logging.
        
    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        (filtered_df, exclusion_log_df)
    """
    if df.empty or value_col not in df.columns:
        return df.copy(), _create_empty_exclusion_log()

    vals = df[value_col]
    neg_mask = vals < 0.0

    if not neg_mask.any():
        return df.copy(), _create_empty_exclusion_log()

    exclusion_log = _build_exclusion_log(
        df=df,
        dropped_mask=neg_mask,
        time_col=time_col if (time_col and time_col in df.columns) else None,
        reason="NEGATIVE_VALUE",
        value_col=value_col,
        details_prefix=f"Negative value ({value_col} < 0) excluded without clipping",
    )

    filtered_df = df[~neg_mask].copy()
    return filtered_df, exclusion_log


def exclude_flagged(
    df: pd.DataFrame,
    flag_col: Optional[str],
    excluded_values: Optional[Sequence[Any]],
    time_col: Optional[str] = "TIME",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Exclude samples bearing unapproved or anomalous instrument quality flags.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input observations.
    flag_col : Optional[str]
        Column name of quality flags (from column_roles.yaml).
    excluded_values : Optional[Sequence[Any]]
        List of flag codes to reject.
    time_col : Optional[str]
        Timestamp column for logging.
        
    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        (filtered_df, exclusion_log_df)
    """
    if df.empty or not flag_col or flag_col not in df.columns or not excluded_values:
        return df.copy(), _create_empty_exclusion_log()

    flag_mask = df[flag_col].isin(excluded_values)

    if not flag_mask.any():
        return df.copy(), _create_empty_exclusion_log()

    exclusion_log = _build_exclusion_log(
        df=df,
        dropped_mask=flag_mask,
        time_col=time_col if (time_col and time_col in df.columns) else None,
        reason="QUALITY_FLAG",
        value_col=flag_col,
        details_prefix=f"Rejected quality flag in column '{flag_col}'",
    )

    filtered_df = df[~flag_mask].copy()
    return filtered_df, exclusion_log


def resolve_duplicate_timestamps(
    df: pd.DataFrame,
    time_col: str = "TIME",
    policy: str = "ERROR",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Resolve duplicate timestamps in accordance with configured policy.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input observations.
    time_col : str
        Timestamp column name.
    policy : str
        One of {'ERROR', 'KEEP_FIRST', 'KEEP_LAST'}. Default 'ERROR'.
        
    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        (filtered_df, exclusion_log_df)
        
    Raises
    -------
    DuplicateTimestampError
        If policy is 'ERROR' and any duplicate timestamps exist.
    ValueError
        If an unrecognised policy is specified.
    """
    valid_policies = {"ERROR", "KEEP_FIRST", "KEEP_LAST"}
    pol_upper = policy.upper()
    if pol_upper not in valid_policies:
        raise ValueError(f"Invalid duplicate resolution policy '{policy}'. Allowed: {sorted(list(valid_policies))}")

    if df.empty or time_col not in df.columns:
        return df.copy(), _create_empty_exclusion_log()

    dup_mask = df.duplicated(subset=[time_col], keep=False)
    if not dup_mask.any():
        return df.copy(), _create_empty_exclusion_log()

    dup_count = int(dup_mask.sum())
    dup_times = df.loc[dup_mask, time_col].unique().tolist()

    if pol_upper == "ERROR":
        raise DuplicateTimestampError(
            f"Detected {dup_count} duplicate timestamp records across {len(dup_times)} unique epochs. "
            f"Policy is 'ERROR'. First few duplicates: {dup_times[:5]}"
        )

    # Determine which rows to drop under KEEP_FIRST vs KEEP_LAST
    keep_arg = "first" if pol_upper == "KEEP_FIRST" else "last"
    dropped_mask = df.duplicated(subset=[time_col], keep=keep_arg)

    exclusion_log = _build_exclusion_log(
        df=df,
        dropped_mask=dropped_mask,
        time_col=time_col,
        reason="DUPLICATE_TIMESTAMP",
        value_col=time_col,
        details_prefix=f"Duplicate timestamp resolved via policy={pol_upper}",
    )

    filtered_df = df[~dropped_mask].copy()
    return filtered_df, exclusion_log


def sort_by_time(
    df: pd.DataFrame,
    time_col: str = "TIME",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Sort observation DataFrame chronologically by time column.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input observations.
    time_col : str
        Timestamp column name.
        
    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        (sorted_df, exclusion_log_df)
        The exclusion log is empty, with metadata attribute 'was_reordered'.
    """
    if df.empty or time_col not in df.columns:
        empty_log = _create_empty_exclusion_log()
        empty_log.attrs["was_reordered"] = False
        return df.copy(), empty_log

    is_sorted = df[time_col].is_monotonic_increasing
    if is_sorted:
        empty_log = _create_empty_exclusion_log()
        empty_log.attrs["was_reordered"] = False
        return df.copy(), empty_log

    sorted_df = df.sort_values(by=time_col, ascending=True).copy()
    empty_log = _create_empty_exclusion_log()
    empty_log.attrs["was_reordered"] = True
    return sorted_df, empty_log
