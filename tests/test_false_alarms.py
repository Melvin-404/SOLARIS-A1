"""Unit tests for false alarm rate calculation and covered observation normalization (Stage 11).

Tests:
1. False-alarm rate is normalized strictly against covered observation hours (GTI duration),
   not uncorrected wall-clock time.
2. Negative or zero covered duration raises ValueError.
3. Detailed false-alarm and missed event records are populated.
"""

import pandas as pd
import pytest
from solar_flare.evaluation.event_metrics import PredictedInterval
from solar_flare.evaluation.false_alarms import compute_false_alarm_analysis


def test_false_alarm_rate_uses_covered_time_not_wall_clock():
    """Verify that false alarm rate is computed per GTI-covered hour rather than wall-clock hours."""
    # Reference event: [1000, 2000]
    ref_events = pd.DataFrame([
        {"event_id": "FLARE_01", "start_sec": 1000.0, "end_sec": 2000.0}
    ])

    # 3 predicted intervals: 1 true detection, 2 false alarms
    preds = [
        PredictedInterval(start_sec=1010.0, end_sec=1500.0, duration_sec=490.0, n_windows=5, max_score=0.9),
        PredictedInterval(start_sec=3000.0, end_sec=3200.0, duration_sec=200.0, n_windows=2, max_score=0.6),
        PredictedInterval(start_sec=4000.0, end_sec=4100.0, duration_sec=100.0, n_windows=1, max_score=0.55),
    ]

    # Suppose wall-clock time spanned 10 hours (36,000 s),
    # but valid GTI-covered observation time was only 2.0 hours (7,200 s).
    covered_sec = 7200.0  # 2.0 hours

    rep = compute_false_alarm_analysis(
        predicted_intervals=preds,
        reference_events=ref_events,
        covered_duration_seconds=covered_sec,
    )

    assert rep.n_false_alarms == 2
    assert rep.covered_duration_sec == 7200.0
    assert pytest.approx(rep.covered_observation_hours, 1e-5) == 2.0
    # Expected rate: 2 false alarms / 2.0 hours = 1.0 per hour
    # (If wall-clock 10 h had been used, rate would have been falsely diluted to 0.2/h)
    assert pytest.approx(rep.false_alarm_rate_per_hour, 1e-5) == 1.0
    assert len(rep.false_alarm_intervals) == 2
    assert len(rep.missed_events) == 0


def test_invalid_covered_duration_raises():
    """Verify that zero or negative covered observation duration raises ValueError."""
    ref_events = pd.DataFrame(columns=["start_sec", "end_sec"])
    preds = []
    with pytest.raises(ValueError, match="strictly positive"):
        compute_false_alarm_analysis(preds, ref_events, covered_duration_seconds=0.0)
    with pytest.raises(ValueError, match="strictly positive"):
        compute_false_alarm_analysis(preds, ref_events, covered_duration_seconds=-3600.0)
