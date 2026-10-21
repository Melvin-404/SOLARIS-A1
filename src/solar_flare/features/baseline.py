"""Causal background baseline flux estimation for SOLARIS-A1 (Stage 8).

Computes local quiescent background flux using strictly pre-window observations:
    t in [window_start - lookback_seconds, window_start)
within the same continuous segment.
Samples at or after window_start are never accessed, guaranteeing causal isolation.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple, Union
import numpy as np
import pandas as pd

from solar_flare.preprocessing.segmentation import ParameterPendingError


def causal_baseline(
    segment_df: pd.DataFrame,
    window_start: float,
    lookback_seconds: Any,
    time_col: str = "TIME",
    value_col: str = "COUNTS",
    min_samples: int = 30,
    is_final: bool = False,
) -> Tuple[float, Optional[str]]:
    """Compute strictly pre-window median background flux within the same segment.
    
    Parameters
    ----------
    segment_df : pd.DataFrame
        Continuous observation segment table.
    window_start : float
        Start timestamp of the target sliding window.
    lookback_seconds : float or Any
        Duration of the lookback interval (Decision D-18). Raises if PENDING in final mode.
    time_col : str
        Timestamp column name.
    value_col : str
        Observation count / flux column name.
    min_samples : int
        Minimum number of valid samples required to compute baseline (default: 30).
    is_final : bool
        If True, requires approved parameters and rejects PENDING values.
        
    Returns
    -------
    Tuple[float, Optional[str]]
        (baseline_value, reason_code)
        baseline_value is median flux in lookback interval, or NaN with reason code.
        
    Raises
    -------
    ParameterPendingError
        If lookback_seconds is PENDING or unconfigured in final mode.
    """
    if lookback_seconds is None or (isinstance(lookback_seconds, str) and "PENDING" in lookback_seconds.upper()):
        if is_final:
            raise ParameterPendingError(
                "Baseline lookback_seconds (Decision D-18) is PENDING human approval at Gate G5. "
                "Final baseline estimation refuses to execute without approved lookback duration."
            )
        lookback = 600.0
    else:
        lookback = float(lookback_seconds)

    if segment_df.empty or time_col not in segment_df.columns or value_col not in segment_df.columns:
        return np.nan, "SEGMENT_EMPTY"

    times = segment_df[time_col].to_numpy(dtype=np.float64)
    vals = segment_df[value_col].to_numpy(dtype=np.float64)

    # Strictly causal time range: [window_start - lookback, window_start)
    # Excludes any sample with t >= window_start
    t_min = float(window_start - lookback)
    t_max = float(window_start)

    mask = (times >= t_min) & (times < t_max)
    in_range_vals = vals[mask]

    # Exclude non-finite
    finite_mask = np.isfinite(in_range_vals)
    clean_vals = in_range_vals[finite_mask]

    if len(clean_vals) < min_samples:
        return np.nan, f"BASELINE_INSUFFICIENT (n={len(clean_vals)} < min={min_samples})"

    med_baseline = float(np.median(clean_vals))
    return med_baseline, None
