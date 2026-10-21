"""Unit tests for solar_flare.preprocessing.segmentation module.

Tests gap boundary splits (equal, below, above max_gap_seconds), minimum duration exclusions,
exact value preservation without interpolation, and pending parameter guard.
All synthetic fixtures are named fixture_synthetic_*.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from solar_flare.preprocessing.segmentation import (
    segment_continuous,
    Segment,
    ParameterPendingError,
)


@pytest.fixture
def fixture_synthetic_gap_series() -> pd.DataFrame:
    """Create a series testing gap thresholds around max_gap_seconds = 2.0 s.
    
    Times:
    Segment 1: 100.0, 101.0, 102.99 (gap 1.99s < 2.0s -> continuous)
               104.99 (gap exactly 2.0s == 2.0s -> continuous, splits strictly > 2.0s)
               107.00 (gap 2.01s > 2.0s -> SPLIT!)
    Segment 2: 107.00, 108.00, 109.00
    """
    times = [100.0, 101.0, 102.99, 104.99, 107.00, 108.00, 109.00]
    counts = [10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5]
    return pd.DataFrame({"TIME": times, "COUNTS": counts})


def test_gap_threshold_boundary_splits(fixture_synthetic_gap_series):
    """Verify that gaps strictly > max_gap split, while gaps <= max_gap remain continuous."""
    df = fixture_synthetic_gap_series
    max_gap = 2.0
    min_seg = 1.0  # Allow both segments to qualify

    segments, excl_log = segment_continuous(
        df=df,
        time_col="TIME",
        max_gap_seconds=max_gap,
        min_segment_seconds=min_seg,
        stem="TEST_STEM",
    )

    assert len(segments) == 2
    assert len(excl_log) == 0

    # Segment 1: [100.0, 104.99], 4 samples
    seg1 = segments[0]
    assert seg1.segment_id == "TEST_STEM_seg_001"
    assert seg1.n_samples == 4
    assert seg1.start == 100.0
    assert seg1.end == 104.99
    # Verify exact values preserved
    assert list(seg1.dataframe["COUNTS"]) == [10.5, 11.5, 12.5, 13.5]

    # Segment 2: [107.00, 109.00], 3 samples
    seg2 = segments[1]
    assert seg2.segment_id == "TEST_STEM_seg_002"
    assert seg2.n_samples == 3
    assert seg2.start == 107.00
    assert seg2.end == 109.00
    assert list(seg2.dataframe["COUNTS"]) == [14.5, 15.5, 16.5]


def test_short_segment_exclusion():
    """Verify that segments shorter than min_segment_seconds are excluded and logged."""
    # 2 segments:
    # Seg 1: duration = 100.0s (>= 60s -> keep)
    # Seg 2: duration = 30.0s (< 60s -> exclude)
    t1 = list(np.arange(1000.0, 1101.0, 1.0))  # 101 samples, duration 100s
    t2 = list(np.arange(2000.0, 2031.0, 1.0))  # 31 samples, duration 30s
    times = t1 + t2
    counts = [1.0] * len(times)
    df = pd.DataFrame({"TIME": times, "COUNTS": counts})

    segments, excl_log = segment_continuous(
        df=df,
        time_col="TIME",
        max_gap_seconds=2.0,
        min_segment_seconds=60.0,
        stem="TEST_STEM",
    )

    assert len(segments) == 1
    assert segments[0].n_samples == 101
    assert len(excl_log) == 31
    assert set(excl_log["reason"]) == {"SEGMENT_TOO_SHORT"}


def test_pending_parameter_raises_parameter_pending_error():
    """Verify that passing null or PENDING parameters raises ParameterPendingError."""
    df = pd.DataFrame({"TIME": [1.0, 2.0], "COUNTS": [10.0, 20.0]})

    with pytest.raises(ParameterPendingError) as exc_info:
        segment_continuous(df, time_col="TIME", max_gap_seconds=None, min_segment_seconds=60.0)
    assert "D-14" in str(exc_info.value)

    with pytest.raises(ParameterPendingError) as exc_info2:
        segment_continuous(df, time_col="TIME", max_gap_seconds="PENDING", min_segment_seconds=60.0)
    assert "D-14" in str(exc_info2.value)
