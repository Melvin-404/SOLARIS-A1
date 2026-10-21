"""Sliding window generation for continuous segments in SOLARIS-A1 (Stage 8).

Generates strictly intra-segment sliding windows with deterministic indexing,
reference-time anchoring (window_end = t_0), and sample coverage qualification.
Windows NEVER cross segment boundaries or data gaps.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from solar_flare.preprocessing.segmentation import ParameterPendingError


@dataclass
class WindowRecord:
    """Standardized metadata record for an individual sliding window."""
    window_id: str
    segment_id: str
    file_stem: str
    window_start: float
    window_end: float  # Reference time t_ref = t_0
    n_expected_samples: int
    n_observed_samples: int
    coverage_fraction: float
    start_index: int
    end_index: int
    min_time_used: float
    max_time_used: float
    quality_flag: str
    include_flag: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_windows(
    segment_df: pd.DataFrame,
    segment_id: str,
    window_seconds: Any,
    stride_seconds: Any,
    time_col: str = "TIME",
    value_col: str = "COUNTS",
    min_coverage_fraction: Any = 0.80,
    include_low_coverage: bool = True,
    is_final: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate sliding windows within a single validated continuous segment.
    
    Parameters
    ----------
    segment_df : pd.DataFrame
        Continuous observation segment table.
    segment_id : str
        Deterministic segment identifier (e.g. 'AL1_SOLEXS_20261018_SDD2_L1_seg_001').
    window_seconds : float or Any
        Window length W in seconds (Decision D-05). Raises if PENDING in final mode.
    stride_seconds : float or Any
        Window stride S in seconds (Decision D-06). Raises if PENDING in final mode.
    time_col : str
        Timestamp column name.
    value_col : str
        Observation count / flux column name.
    min_coverage_fraction : float or Any
        Minimum coverage fraction to receive quality_flag='OK'.
    include_low_coverage : bool
        Whether windows with LOW_COVERAGE receive include_flag=True.
    is_final : bool
        If True, requires approved parameters and rejects PENDING values.
        
    Returns
    -------
    Tuple[pd.DataFrame, Dict[str, Any]]
        window_index_df: Table of all generated windows with provenance and coverage flags.
        summary_dict: Summary metrics on window generation.
        
    Raises
    -------
    ParameterPendingError
        If window or stride parameters are null or PENDING in final mode.
    ValueError
        If DataFrame is missing time_col or window parameters are non-positive.
    """
    # 1. Parameter validation and approval guard
    for name, val, dec_id in [
        ("window_seconds", window_seconds, "D-05"),
        ("stride_seconds", stride_seconds, "D-06"),
        ("min_coverage_fraction", min_coverage_fraction, "D-20"),
    ]:
        if val is None or (isinstance(val, str) and "PENDING" in val.upper()):
            if is_final:
                raise ParameterPendingError(
                    f"Parameter '{name}' is PENDING human approval ({dec_id}). "
                    "Final window generation refuses to execute without Gate G5 approval."
                )

    w_sec = float(window_seconds) if window_seconds is not None else 60.0
    s_sec = float(stride_seconds) if stride_seconds is not None else 10.0
    min_cov = float(min_coverage_fraction) if min_coverage_fraction is not None else 0.80

    if w_sec <= 0.0:
        raise ValueError(f"window_seconds must be positive, got {w_sec}")
    if s_sec <= 0.0:
        raise ValueError(f"stride_seconds must be positive, got {s_sec}")

    file_stem = segment_id.split("_seg_")[0] if "_seg_" in segment_id else segment_id

    # 2. Check segment sufficiency
    if segment_df.empty or time_col not in segment_df.columns:
        return pd.DataFrame(), {
            "segment_id": segment_id,
            "status": "EMPTY_SEGMENT",
            "n_windows": 0,
            "reason": "Segment table is empty or missing time column",
        }

    times = segment_df[time_col].to_numpy(dtype=np.float64)
    n_total_samples = len(times)
    t_start = float(times[0])
    t_end = float(times[-1])
    duration = float(t_end - t_start)

    # Median cadence
    if n_total_samples > 1:
        cadence_median = float(np.median(np.diff(times)))
    else:
        cadence_median = 1.0

    if cadence_median <= 0.0:
        cadence_median = 1.0

    n_expected = max(1, int(round(w_sec / cadence_median)))

    # If duration < window_seconds, segment cannot produce any full window
    if duration < w_sec:
        return pd.DataFrame(), {
            "segment_id": segment_id,
            "status": "SEGMENT_TOO_SHORT_FOR_WINDOW",
            "duration_seconds": duration,
            "window_seconds": w_sec,
            "n_windows": 0,
            "reason": f"Segment duration ({duration:.2f}s) < window_seconds ({w_sec:.2f}s)",
        }

    # 3. Calculate exact number of windows
    # Formula: floor((duration - window_seconds) / stride_seconds) + 1
    n_windows = int(np.floor((duration - w_sec + 1e-6) / s_sec)) + 1

    records: List[Dict[str, Any]] = []

    for win_idx in range(n_windows):
        w_start = float(t_start + win_idx * s_sec)
        w_end = float(w_start + w_sec)

        # Locate sample slice within [w_start, w_end]
        # Using binary search / searchsorted for exact and fast indexing
        left_idx = int(np.searchsorted(times, w_start - 1e-9, side="left"))
        right_idx = int(np.searchsorted(times, w_end + 1e-9, side="right"))

        sub_times = times[left_idx:right_idx]
        n_obs = len(sub_times)

        if n_obs > 0:
            min_t_used = float(sub_times[0])
            max_t_used = float(sub_times[-1])
            start_i = left_idx
            end_i = right_idx - 1
        else:
            min_t_used = w_start
            max_t_used = w_end
            start_i = left_idx
            end_i = left_idx

        cov_frac = float(n_obs / n_expected)
        is_low_cov = cov_frac < min_cov
        q_flag = "LOW_COVERAGE" if is_low_cov else "OK"
        inc_flag = (not is_low_cov) or include_low_coverage

        win_id = f"{segment_id}_win_{win_idx + 1:05d}"

        record = WindowRecord(
            window_id=win_id,
            segment_id=segment_id,
            file_stem=file_stem,
            window_start=w_start,
            window_end=w_end,
            n_expected_samples=n_expected,
            n_observed_samples=n_obs,
            coverage_fraction=round(cov_frac, 4),
            start_index=start_i,
            end_index=end_i,
            min_time_used=min_t_used,
            max_time_used=max_t_used,
            quality_flag=q_flag,
            include_flag=inc_flag,
        )
        records.append(record.to_dict())

    window_df = pd.DataFrame(records)
    summary = {
        "segment_id": segment_id,
        "status": "SUCCESS",
        "n_windows": len(window_df),
        "duration_seconds": duration,
        "cadence_median": cadence_median,
        "n_expected_samples": n_expected,
        "n_low_coverage": int((window_df["quality_flag"] == "LOW_COVERAGE").sum()),
    }

    return window_df, summary
