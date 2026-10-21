"""Event-level detection and warning metrics for SOLARIS-A1 (Stage 11).

Evaluates macro solar flare event detection performance:
- Merges consecutive positive temporal windows into contiguous predicted intervals.
- Matches predicted intervals against independent reference flare events.
- Computes event detection rate (recall), false-alarm episode count, and missed events.
- Quantifies timing errors (onset differences: median and IQR).
- For prediction tasks: quantifies lead time, unwarned onsets, and false-alarm forecasts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PredictedInterval:
    """A contiguous predicted event episode created by merging adjacent positive windows."""

    start_sec: float
    end_sec: float
    duration_sec: float
    n_windows: int
    max_score: Optional[float] = None


@dataclass(frozen=True)
class EventMetricsReport:
    """Structured report of event-level detection performance."""

    n_reference_events: int
    n_detected_events: int
    n_missed_events: int
    event_detection_rate: float
    n_predicted_intervals: int
    n_false_alarm_intervals: int
    timing_errors_sec: List[float]
    median_timing_error_sec: Optional[float]
    iqr_timing_error_sec: Optional[float]
    lead_times_sec: List[float]
    median_lead_time_sec: Optional[float]
    n_unwarned_onsets: int
    merge_gap_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary representation."""
        return asdict(self)


def merge_positive_windows(
    window_times: Sequence[Tuple[float, float]],
    scores: Optional[Sequence[float]] = None,
    merge_gap_seconds: float = 60.0,
) -> List[PredictedInterval]:
    """Merge consecutive positive window intervals within an approved merge gap.

    Parameters
    ----------
    window_times : sequence of (start_sec, end_sec) tuples
        Start and end times in seconds for each positive window.
    scores : sequence of float, optional
        Confidence scores associated with each positive window.
    merge_gap_seconds : float, default=60.0
        Maximum time gap (in seconds) between windows to merge into a single event episode.

    Returns
    -------
    list of PredictedInterval
        Contiguous merged predicted intervals.
    """
    if not window_times:
        return []

    # Sort windows chronologically
    indexed_windows = []
    for idx, (st, en) in enumerate(window_times):
        sc = scores[idx] if scores is not None and idx < len(scores) else None
        indexed_windows.append((st, en, sc))

    indexed_windows.sort(key=lambda x: x[0])

    merged: List[PredictedInterval] = []
    curr_start, curr_end, curr_max_sc = (
        indexed_windows[0][0],
        indexed_windows[0][1],
        indexed_windows[0][2],
    )
    curr_count = 1

    for st, en, sc in indexed_windows[1:]:
        gap = st - curr_end
        if gap <= merge_gap_seconds:
            # Merge into current interval
            curr_end = max(curr_end, en)
            curr_count += 1
            if sc is not None:
                curr_max_sc = sc if curr_max_sc is None else max(curr_max_sc, sc)
        else:
            # Close previous interval and start new
            merged.append(
                PredictedInterval(
                    start_sec=curr_start,
                    end_sec=curr_end,
                    duration_sec=curr_end - curr_start,
                    n_windows=curr_count,
                    max_score=curr_max_sc,
                )
            )
            curr_start, curr_end, curr_max_sc = st, en, sc
            curr_count = 1

    # Append trailing interval
    merged.append(
        PredictedInterval(
            start_sec=curr_start,
            end_sec=curr_end,
            duration_sec=curr_end - curr_start,
            n_windows=curr_count,
            max_score=curr_max_sc,
        )
    )

    return merged


def compute_event_metrics(
    reference_events: pd.DataFrame,
    predicted_intervals: Sequence[PredictedInterval],
    task: str = "detection",
    lead_horizon_sec: float = 1800.0,
    merge_gap_seconds: float = 60.0,
) -> EventMetricsReport:
    """Compute event-level detection, false alarm, and timing metrics.

    Parameters
    ----------
    reference_events : pd.DataFrame
        Table of reference events with columns ['start_sec', 'end_sec'] (or ['onset_sec', 'end_sec']).
    predicted_intervals : sequence of PredictedInterval
        Merged candidate predicted intervals.
    task : str, default="detection"
        Task mode: "detection" or "prediction".
    lead_horizon_sec : float, default=1800.0
        Prediction warning horizon (for Task B prediction).
    merge_gap_seconds : float, default=60.0
        Merge gap parameter used to produce predicted intervals.

    Returns
    -------
    EventMetricsReport
        Dataclass containing event-level metrics.
    """
    n_ref = len(reference_events)
    n_pred = len(predicted_intervals)

    if n_ref == 0:
        return EventMetricsReport(
            n_reference_events=0,
            n_detected_events=0,
            n_missed_events=0,
            event_detection_rate=0.0,
            n_predicted_intervals=n_pred,
            n_false_alarm_intervals=n_pred,
            timing_errors_sec=[],
            median_timing_error_sec=None,
            iqr_timing_error_sec=None,
            lead_times_sec=[],
            median_lead_time_sec=None,
            n_unwarned_onsets=0,
            merge_gap_seconds=merge_gap_seconds,
        )

    # Resolve column names for reference events
    start_col = "start_sec" if "start_sec" in reference_events.columns else "onset_sec"
    end_col = "end_sec" if "end_sec" in reference_events.columns else "peak_sec"

    detected_event_flags = [False] * n_ref
    timing_errors: List[float] = []
    lead_times: List[float] = []
    predicted_matched = [False] * n_pred

    for ref_idx, (_, ref_row) in enumerate(reference_events.iterrows()):
        ref_start = float(ref_row[start_col])
        ref_end = float(ref_row[end_col])

        # Find matching predicted intervals
        matching_preds: List[Tuple[int, PredictedInterval]] = []
        for p_idx, pred in enumerate(predicted_intervals):
            if task == "detection":
                # Detection: interval overlap condition
                if pred.start_sec <= ref_end and pred.end_sec >= ref_start:
                    matching_preds.append((p_idx, pred))
                    predicted_matched[p_idx] = True
            else:
                # Prediction: forecast episode occurs within horizon before onset:
                # [ref_start - lead_horizon_sec, ref_start]
                if pred.end_sec >= (ref_start - lead_horizon_sec) and pred.start_sec <= ref_start:
                    matching_preds.append((p_idx, pred))
                    predicted_matched[p_idx] = True

        if matching_preds:
            detected_event_flags[ref_idx] = True
            # First matching prediction determines timing
            first_pred = matching_preds[0][1]
            if task == "detection":
                timing_err = first_pred.start_sec - ref_start
                timing_errors.append(timing_err)
            else:
                # Lead time: time difference between onset and warning initiation
                lead = ref_start - first_pred.start_sec
                lead_times.append(lead)

    n_detected = sum(detected_event_flags)
    n_missed = n_ref - n_detected
    detection_rate = float(n_detected / n_ref) if n_ref > 0 else 0.0

    n_fa = sum(1 for m in predicted_matched if not m)
    n_unwarned = n_missed if task == "prediction" else 0

    # Timing statistics
    med_timing: Optional[float] = None
    iqr_timing: Optional[float] = None
    if timing_errors:
        med_timing = float(np.median(timing_errors))
        q75, q25 = np.percentile(timing_errors, [75, 25])
        iqr_timing = float(q75 - q25)

    # Lead time statistics
    med_lead: Optional[float] = None
    if lead_times:
        med_lead = float(np.median(lead_times))

    return EventMetricsReport(
        n_reference_events=n_ref,
        n_detected_events=n_detected,
        n_missed_events=n_missed,
        event_detection_rate=detection_rate,
        n_predicted_intervals=n_pred,
        n_false_alarm_intervals=n_fa,
        timing_errors_sec=timing_errors,
        median_timing_error_sec=med_timing,
        iqr_timing_error_sec=iqr_timing,
        lead_times_sec=lead_times,
        median_lead_time_sec=med_lead,
        n_unwarned_onsets=n_unwarned,
        merge_gap_seconds=merge_gap_seconds,
    )
