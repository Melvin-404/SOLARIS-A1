"""Good Time Interval (GTI) application for SOLARIS-A1 (Stage 7).

Filters light-curve observations against approved GTI time intervals using an explicit
boundary inclusion convention. Excluded samples are logged with reason 'OUTSIDE_GTI'.
Adds 'gti_flag' column exclusively to the retained processed copy.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
import pandas as pd

from solar_flare.preprocessing.filters import EXCLUSION_COLUMNS, _create_empty_exclusion_log

ALLOWED_GTI_BOUNDARIES = {
    "START_INCLUSIVE_STOP_EXCLUSIVE",
    "START_EXCLUSIVE_STOP_INCLUSIVE",
    "BOTH_INCLUSIVE",
}


def apply_gti(
    df: pd.DataFrame,
    time_col: str,
    gti_intervals: Union[List[Dict[str, float]], pd.DataFrame, Sequence[Tuple[float, float]]],
    boundary: str = "START_INCLUSIVE_STOP_EXCLUSIVE",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Apply GTI intervals to filter continuous observations.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input observations.
    time_col : str
        Name of timestamp column in df.
    gti_intervals : list of dict, DataFrame, or sequence of tuples
        Approved GTI intervals. Each entry must provide start and stop timestamps.
    boundary : str
        Boundary inclusion convention:
        - 'START_INCLUSIVE_STOP_EXCLUSIVE' (start <= t < stop)
        - 'START_EXCLUSIVE_STOP_INCLUSIVE' (start < t <= stop)
        - 'BOTH_INCLUSIVE' (start <= t <= stop)
        
    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        (filtered_df, exclusion_log_df)
        filtered_df includes an added 'gti_flag' column (=True).
        exclusion_log_df records all samples falling outside valid intervals.
        
    Raises
    -------
    ValueError
        If an unrecognised boundary convention is provided.
    """
    bound_upper = boundary.upper()
    if bound_upper not in ALLOWED_GTI_BOUNDARIES:
        raise ValueError(
            f"Invalid GTI boundary convention '{boundary}'. "
            f"Allowed conventions: {sorted(list(ALLOWED_GTI_BOUNDARIES))}"
        )

    if df.empty:
        empty_ret = df.copy()
        empty_ret["gti_flag"] = pd.Series(dtype=bool)
        return empty_ret, _create_empty_exclusion_log()

    # Extract parsed interval start/stop pairs
    parsed_intervals: List[Tuple[float, float]] = []
    if isinstance(gti_intervals, pd.DataFrame):
        s_col = "START" if "START" in gti_intervals.columns else ("start" if "start" in gti_intervals.columns else gti_intervals.columns[0])
        e_col = "STOP" if "STOP" in gti_intervals.columns else ("stop" if "stop" in gti_intervals.columns else gti_intervals.columns[1])
        for _, r in gti_intervals.iterrows():
            parsed_intervals.append((float(r[s_col]), float(r[e_col])))
    elif isinstance(gti_intervals, (list, tuple)):
        for item in gti_intervals:
            if isinstance(item, dict):
                s = item.get("START", item.get("start", item.get("start_time")))
                e = item.get("STOP", item.get("stop", item.get("end_time")))
                if s is not None and e is not None:
                    parsed_intervals.append((float(s), float(e)))
            elif isinstance(item, (tuple, list)) and len(item) >= 2:
                parsed_intervals.append((float(item[0]), float(item[1])))

    # Special handling: 0 GTI rows / empty intervals
    if len(parsed_intervals) == 0:
        # All samples are outside GTI
        records: List[Dict[str, Any]] = []
        for idx, row in df.iterrows():
            t_val = row[time_col] if time_col in row else None
            records.append({
                "original_index": idx,
                "time": t_val,
                "reason": "OUTSIDE_GTI",
                "value": t_val,
                "details": "GTI EMPTY — no samples retained for this file",
            })
        excl_df = pd.DataFrame(records, columns=EXCLUSION_COLUMNS)
        empty_ret = df.iloc[0:0].copy()
        empty_ret["gti_flag"] = pd.Series(dtype=bool)
        return empty_ret, excl_df

    # Evaluate GTI inclusion mask
    times = df[time_col].to_numpy(dtype=np.float64)
    inside_mask = np.zeros(len(times), dtype=bool)

    for start_t, stop_t in parsed_intervals:
        if bound_upper == "START_INCLUSIVE_STOP_EXCLUSIVE":
            cur_inside = (times >= start_t) & (times < stop_t)
        elif bound_upper == "START_EXCLUSIVE_STOP_INCLUSIVE":
            cur_inside = (times > start_t) & (times <= stop_t)
        else:  # BOTH_INCLUSIVE
            cur_inside = (times >= start_t) & (times <= stop_t)
        inside_mask |= cur_inside

    outside_mask = ~inside_mask

    # Build exclusion log for outside-GTI samples
    if outside_mask.any():
        outside_df = df[outside_mask]
        records = []
        for idx, row in outside_df.iterrows():
            t_val = row[time_col]
            records.append({
                "original_index": idx,
                "time": t_val,
                "reason": "OUTSIDE_GTI",
                "value": t_val,
                "details": f"Timestamp {t_val} outside all {len(parsed_intervals)} GTI intervals (boundary={bound_upper})",
            })
        excl_df = pd.DataFrame(records, columns=EXCLUSION_COLUMNS)
    else:
        excl_df = _create_empty_exclusion_log()

    # Retain inside-GTI samples and add gti_flag
    retained_df = df[inside_mask].copy()
    retained_df["gti_flag"] = True

    return retained_df, excl_df
