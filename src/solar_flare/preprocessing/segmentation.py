"""Continuous observation segmentation for SOLARIS-A1 (Stage 7).

Segments GTI-filtered light-curve observations at continuous cadence boundaries.
Splits occur strictly whenever time difference dt > max_gap_seconds.
Gaps are never bridged, estimated, or reconstructed.
Segments shorter than min_segment_seconds are excluded and recorded in the audit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from solar_flare.preprocessing.filters import EXCLUSION_COLUMNS, _create_empty_exclusion_log


class ParameterPendingError(RuntimeError):
    """Raised when segmentation is invoked with PENDING decision parameters."""
    pass


@dataclass
class Segment:
    """Continuous observation segment representation."""
    segment_id: str
    start: float
    end: float
    n_samples: int
    cadence_median: float
    gap_before_seconds: Optional[float]
    dataframe: pd.DataFrame

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "start": self.start,
            "end": self.end,
            "n_samples": self.n_samples,
            "cadence_median": self.cadence_median,
            "gap_before_seconds": self.gap_before_seconds,
            "duration_seconds": float(self.end - self.start),
        }


def _validate_segmentation_parameters(
    max_gap_seconds: Any,
    min_segment_seconds: Any,
) -> Tuple[float, float]:
    """Validate that segmentation parameters are numeric and not PENDING."""
    if max_gap_seconds is None:
        raise ParameterPendingError(
            "Parameter max_gap_seconds is null (PENDING). "
            "Gate G4 requires formal human approval of Decision D-14 before final segmentation."
        )
    if isinstance(max_gap_seconds, str) and "PENDING" in max_gap_seconds.upper():
        raise ParameterPendingError(
            f"Parameter max_gap_seconds is '{max_gap_seconds}'. "
            "Decision D-14 is PENDING human approval at Gate G4."
        )

    if min_segment_seconds is None:
        raise ParameterPendingError(
            "Parameter min_segment_seconds is null (PENDING). "
            "Gate G4 requires formal human approval of Decision D-14 before final segmentation."
        )
    if isinstance(min_segment_seconds, str) and "PENDING" in min_segment_seconds.upper():
        raise ParameterPendingError(
            f"Parameter min_segment_seconds is '{min_segment_seconds}'. "
            "Decision D-14 is PENDING human approval at Gate G4."
        )

    try:
        max_gap = float(max_gap_seconds)
        min_seg = float(min_segment_seconds)
    except (ValueError, TypeError) as exc:
        raise ParameterPendingError(f"Segmentation parameters could not be converted to float: {exc}") from exc

    if max_gap <= 0.0:
        raise ValueError(f"max_gap_seconds must be positive, got {max_gap}")
    if min_seg <= 0.0:
        raise ValueError(f"min_segment_seconds must be positive, got {min_seg}")

    return max_gap, min_seg


def segment_continuous(
    df: pd.DataFrame,
    time_col: str,
    max_gap_seconds: Any,
    min_segment_seconds: Any,
    stem: str = "segment",
) -> Tuple[List[Segment], pd.DataFrame]:
    """Split observation DataFrame into continuous segments at gaps > max_gap_seconds.
    
    Parameters
    ----------
    df : pd.DataFrame
        GTI-filtered observations.
    time_col : str
        Timestamp column name.
    max_gap_seconds : float or Any
        Gap threshold; splits occur at dt > max_gap_seconds. Raises if PENDING.
    min_segment_seconds : float or Any
        Minimum physical duration (end - start) for a segment to be retained. Raises if PENDING.
    stem : str
        File stem for deterministic segment IDs (e.g. 'AL1_SOLEXS_20261018_SDD2_L1').
        
    Returns
    -------
    Tuple[List[Segment], pd.DataFrame]
        (valid_segments, exclusion_log_df)
        valid_segments: list of Segment objects exceeding min_segment_seconds.
        exclusion_log_df: table of samples belonging to segments discarded as SEGMENT_TOO_SHORT.
        
    Raises
    -------
    ParameterPendingError
        If max_gap_seconds or min_segment_seconds is PENDING or unconfigured.
    """
    max_gap, min_seg = _validate_segmentation_parameters(max_gap_seconds, min_segment_seconds)

    if df.empty or time_col not in df.columns:
        return [], _create_empty_exclusion_log()

    times = df[time_col].to_numpy(dtype=np.float64)
    n = len(times)

    if n == 0:
        return [], _create_empty_exclusion_log()

    # Find split indices where gap strictly exceeds max_gap_seconds
    diffs = np.diff(times)
    split_indices = np.where(diffs > max_gap)[0] + 1

    # Form raw segment chunks
    segment_slices: List[Tuple[int, int]] = []
    start_idx = 0
    for split_idx in split_indices:
        segment_slices.append((start_idx, split_idx))
        start_idx = split_idx
    segment_slices.append((start_idx, n))

    valid_segments: List[Segment] = []
    excluded_records: List[Dict[str, Any]] = []
    seg_counter = 1
    last_end_time: Optional[float] = None

    for s_idx, e_idx in segment_slices:
        sub_df = df.iloc[s_idx:e_idx].copy()
        seg_times = sub_df[time_col].to_numpy(dtype=np.float64)
        t_start = float(seg_times[0])
        t_end = float(seg_times[-1])
        duration = float(t_end - t_start)
        n_samples = len(seg_times)

        # Compute median cadence within segment
        if n_samples > 1:
            cadence_median = float(np.median(np.diff(seg_times)))
        else:
            cadence_median = 0.0

        gap_before = float(t_start - last_end_time) if last_end_time is not None else 0.0

        # Check minimum duration criterion
        if duration < min_seg:
            # Segment is too short; log every sample
            for row_idx, row in sub_df.iterrows():
                t_val = row[time_col]
                excluded_records.append({
                    "original_index": row_idx,
                    "time": t_val,
                    "reason": "SEGMENT_TOO_SHORT",
                    "value": duration,
                    "details": (
                        f"Sample in segment of duration {duration:.2f}s < min_segment_seconds={min_seg:.2f}s "
                        f"(start={t_start}, end={t_end}, n_samples={n_samples})"
                    ),
                })
        else:
            seg_id = f"{stem}_seg_{seg_counter:03d}"
            segment = Segment(
                segment_id=seg_id,
                start=t_start,
                end=t_end,
                n_samples=n_samples,
                cadence_median=cadence_median,
                gap_before_seconds=gap_before,
                dataframe=sub_df,
            )
            valid_segments.append(segment)
            seg_counter += 1

        last_end_time = t_end

    if excluded_records:
        excl_df = pd.DataFrame(excluded_records, columns=EXCLUSION_COLUMNS)
    else:
        excl_df = _create_empty_exclusion_log()

    return valid_segments, excl_df
