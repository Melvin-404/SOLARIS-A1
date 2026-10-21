"""False alarm and missed event analysis for SOLARIS-A1 (Stage 11).

Quantifies operational false alarms normalized strictly against verified GTI-covered
observation hours (NOT uncorrected wall-clock time) and provides structured audit tables
for both false alarms and missed events.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence
import pandas as pd

from solar_flare.evaluation.event_metrics import PredictedInterval


@dataclass(frozen=True)
class FalseAlarmRecord:
    """Detailed record for an individual false alarm interval."""

    start_sec: float
    end_sec: float
    duration_sec: float
    n_windows: int
    max_score: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MissedEventRecord:
    """Detailed record for an undetected reference event."""

    event_id: str
    onset_sec: float
    end_sec: float
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FalseAlarmReport:
    """Structured report on false alarm rate and event misses."""

    covered_duration_sec: float
    covered_observation_hours: float
    n_false_alarms: int
    false_alarm_rate_per_hour: float
    false_alarm_intervals: List[FalseAlarmRecord]
    missed_events: List[MissedEventRecord]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "covered_duration_sec": self.covered_duration_sec,
            "covered_observation_hours": self.covered_observation_hours,
            "n_false_alarms": self.n_false_alarms,
            "false_alarm_rate_per_hour": self.false_alarm_rate_per_hour,
            "false_alarm_intervals": [r.to_dict() for r in self.false_alarm_intervals],
            "missed_events": [r.to_dict() for r in self.missed_events],
        }


def compute_false_alarm_analysis(
    predicted_intervals: Sequence[PredictedInterval],
    reference_events: pd.DataFrame,
    covered_duration_seconds: float,
    task: str = "detection",
    lead_horizon_sec: float = 1800.0,
) -> FalseAlarmReport:
    """Compute false alarms per covered observation hour and missed event breakdown.

    Parameters
    ----------
    predicted_intervals : sequence of PredictedInterval
        Candidate event intervals produced by window merging.
    reference_events : pd.DataFrame
        Ground-truth reference event table.
    covered_duration_seconds : float
        Cumulative GTI-covered science observation time in seconds (NOT wall clock).
    task : str, default="detection"
        Evaluation task: "detection" or "prediction".
    lead_horizon_sec : float, default=1800.0
        Forecast horizon for prediction task.

    Returns
    -------
    FalseAlarmReport
        Detailed false alarm analysis report.
    """
    if covered_duration_seconds <= 0.0:
        raise ValueError(
            f"Covered observation duration must be strictly positive, got {covered_duration_seconds} s."
        )

    covered_hours = covered_duration_seconds / 3600.0

    start_col = "start_sec" if "start_sec" in reference_events.columns else "onset_sec"
    end_col = "end_sec" if "end_sec" in reference_events.columns else "peak_sec"
    id_col = "event_id" if "event_id" in reference_events.columns else None

    # 1. Identify False Alarm Intervals
    fa_records: List[FalseAlarmRecord] = []
    for pred in predicted_intervals:
        is_matched = False
        for _, ref in reference_events.iterrows():
            ref_start = float(ref[start_col])
            ref_end = float(ref[end_col])

            if task == "detection":
                if pred.start_sec <= ref_end and pred.end_sec >= ref_start:
                    is_matched = True
                    break
            else:
                if pred.end_sec >= (ref_start - lead_horizon_sec) and pred.start_sec <= ref_start:
                    is_matched = True
                    break

        if not is_matched:
            fa_records.append(
                FalseAlarmRecord(
                    start_sec=pred.start_sec,
                    end_sec=pred.end_sec,
                    duration_sec=pred.duration_sec,
                    n_windows=pred.n_windows,
                    max_score=pred.max_score,
                )
            )

    # 2. Identify Missed Reference Events
    missed_records: List[MissedEventRecord] = []
    for idx, ref in reference_events.iterrows():
        ref_start = float(ref[start_col])
        ref_end = float(ref[end_col])
        ev_id = str(ref[id_col]) if id_col and id_col in ref else f"EVENT_{idx+1:03d}"

        is_detected = False
        for pred in predicted_intervals:
            if task == "detection":
                if pred.start_sec <= ref_end and pred.end_sec >= ref_start:
                    is_detected = True
                    break
            else:
                if pred.end_sec >= (ref_start - lead_horizon_sec) and pred.start_sec <= ref_start:
                    is_detected = True
                    break

        if not is_detected:
            missed_records.append(
                MissedEventRecord(
                    event_id=ev_id,
                    onset_sec=ref_start,
                    end_sec=ref_end,
                    reason="No predicted interval matched reference window",
                )
            )

    fa_rate = len(fa_records) / covered_hours if covered_hours > 0 else 0.0

    return FalseAlarmReport(
        covered_duration_sec=covered_duration_seconds,
        covered_observation_hours=covered_hours,
        n_false_alarms=len(fa_records),
        false_alarm_rate_per_hour=fa_rate,
        false_alarm_intervals=fa_records,
        missed_events=missed_records,
    )
