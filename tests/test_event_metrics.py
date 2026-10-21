"""Unit tests for event-level metrics and window merging (Stage 11).

Tests:
1. Merge gap behavior exactness (merging within gap, splitting beyond gap).
2. Synthetic reference events vs. predicted intervals:
   - Known detections, misses, false alarms.
   - Onset timing errors (median and IQR).
"""

import numpy as np
import pandas as pd
import pytest
from solar_flare.evaluation.event_metrics import (
    PredictedInterval,
    compute_event_metrics,
    merge_positive_windows,
)


def test_merge_gap_exactness():
    """Verify that adjacent windows within merge_gap are merged, while gaps > merge_gap create new intervals."""
    # Windows with 60 s length:
    # W1: [0, 60]
    # W2: [50, 110] (gap = 50 - 60 = -10 <= 60 -> merge)
    # W3: [120, 180] (gap = 120 - 110 = 10 <= 60 -> merge)
    # W4: [300, 360] (gap = 300 - 180 = 120 > 60 -> split)
    window_times = [
        (0.0, 60.0),
        (50.0, 110.0),
        (120.0, 180.0),
        (300.0, 360.0),
    ]
    scores = [0.8, 0.95, 0.85, 0.70]

    intervals = merge_positive_windows(window_times, scores, merge_gap_seconds=60.0)

    assert len(intervals) == 2
    # First merged interval spans 0 to 180
    assert intervals[0].start_sec == 0.0
    assert intervals[0].end_sec == 180.0
    assert intervals[0].duration_sec == 180.0
    assert intervals[0].n_windows == 3
    assert intervals[0].max_score == 0.95

    # Second interval spans 300 to 360
    assert intervals[1].start_sec == 300.0
    assert intervals[1].end_sec == 360.0
    assert intervals[1].duration_sec == 60.0
    assert intervals[1].n_windows == 1
    assert intervals[1].max_score == 0.70


def test_event_detection_and_timing_metrics():
    """Verify known event detection count, misses, false alarms, and timing errors on synthetic data."""
    # 3 Reference events:
    # E1: [1000, 2000]
    # E2: [4000, 5000]
    # E3: [8000, 9000]
    ref_events = pd.DataFrame([
        {"event_id": "EV1", "start_sec": 1000.0, "end_sec": 2000.0},
        {"event_id": "EV2", "start_sec": 4000.0, "end_sec": 5000.0},
        {"event_id": "EV3", "start_sec": 8000.0, "end_sec": 9000.0},
    ])

    # 3 Predicted intervals:
    # P1: [1020, 1500] -> overlaps E1 (timing error = 1020 - 1000 = +20 s)
    # P2: [3980, 4500] -> overlaps E2 (timing error = 3980 - 4000 = -20 s)
    # P3: [6000, 6500] -> false alarm (does not overlap any reference event)
    # E3 is missed!
    pred_intervals = [
        PredictedInterval(start_sec=1020.0, end_sec=1500.0, duration_sec=480.0, n_windows=8, max_score=0.9),
        PredictedInterval(start_sec=3980.0, end_sec=4500.0, duration_sec=520.0, n_windows=9, max_score=0.85),
        PredictedInterval(start_sec=6000.0, end_sec=6500.0, duration_sec=500.0, n_windows=5, max_score=0.6),
    ]

    rep = compute_event_metrics(
        reference_events=ref_events,
        predicted_intervals=pred_intervals,
        task="detection",
        merge_gap_seconds=60.0,
    )

    assert rep.n_reference_events == 3
    assert rep.n_detected_events == 2
    assert rep.n_missed_events == 1
    assert pytest.approx(rep.event_detection_rate, 1e-5) == 2.0 / 3.0
    assert rep.n_predicted_intervals == 3
    assert rep.n_false_alarm_intervals == 1
    assert rep.timing_errors_sec == [20.0, -20.0]
    assert pytest.approx(rep.median_timing_error_sec, 1e-5) == 0.0
    # IQR: 20 - (-20) = 40 (or 50% spread)
    assert rep.iqr_timing_error_sec is not None
