"""Unit tests for solar_flare.features.windows module.

Tests sliding window generation, exact count formulas, boundary enforcement,
coverage tracking, and LOW_COVERAGE quality flags.
All synthetic fixtures are named fixture_synthetic_*.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from solar_flare.features.windows import generate_windows


@pytest.fixture
def fixture_synthetic_regular_segment() -> pd.DataFrame:
    """Create a 20-sample regular continuous segment at 1.0 s cadence (times 0.0 to 19.0 s)."""
    times = [float(i) for i in range(20)]
    counts = [10.0 + float(i) for i in range(20)]
    return pd.DataFrame({"TIME": times, "COUNTS": counts})


@pytest.fixture
def fixture_synthetic_gapped_segment() -> pd.DataFrame:
    """Create a segment with missing samples to test LOW_COVERAGE qualification."""
    # 20-second span with 10 samples missing in the middle:
    # Times 0..4 (5 samples), gap, times 15..19 (5 samples). Total 10 observed samples across 19s span.
    times = [0.0, 1.0, 2.0, 3.0, 4.0, 15.0, 16.0, 17.0, 18.0, 19.0]
    counts = [10.0] * len(times)
    return pd.DataFrame({"TIME": times, "COUNTS": counts})


def test_regular_segment_window_generation(fixture_synthetic_regular_segment):
    """Verify window generation for 20 samples at 1s cadence with window=5s and stride=2s.
    
    Segment: start=0.0, end=19.0, duration=19.0s.
    Expected count: floor((19.0 - 5.0) / 2.0) + 1 = floor(14.0 / 2.0) + 1 = 8 windows.
    Windows:
    - w_0: [0.0, 5.0], start_idx=0, end_idx=5
    - w_1: [2.0, 7.0]
    ...
    - w_7: [14.0, 19.0], start_idx=14, end_idx=19
    """
    df = fixture_synthetic_regular_segment
    win_df, summary = generate_windows(
        segment_df=df,
        segment_id="TEST_seg_001",
        window_seconds=5.0,
        stride_seconds=2.0,
        time_col="TIME",
        value_col="COUNTS",
        min_coverage_fraction=0.80,
    )

    assert len(win_df) == 8
    assert summary["n_windows"] == 8

    # First window
    w0 = win_df.iloc[0]
    assert w0["window_id"] == "TEST_seg_001_win_00001"
    assert w0["window_start"] == 0.0
    assert w0["window_end"] == 5.0
    assert w0["start_index"] == 0
    assert w0["end_index"] == 5
    assert w0["quality_flag"] == "OK"
    assert bool(w0["include_flag"]) is True

    # Last window
    w7 = win_df.iloc[7]
    assert w7["window_id"] == "TEST_seg_001_win_00008"
    assert w7["window_start"] == 14.0
    assert w7["window_end"] == 19.0
    assert w7["start_index"] == 14
    assert w7["end_index"] == 19
    assert w7["quality_flag"] == "OK"


def test_two_segments_produce_no_cross_boundary_windows():
    """Verify that windows generated independently for two segments never span across them."""
    seg1_df = pd.DataFrame({"TIME": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], "COUNTS": [1.0]*6})
    seg2_df = pd.DataFrame({"TIME": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0], "COUNTS": [1.0]*6})

    w1_df, _ = generate_windows(seg1_df, segment_id="SEG_01", window_seconds=4.0, stride_seconds=2.0)
    w2_df, _ = generate_windows(seg2_df, segment_id="SEG_02", window_seconds=4.0, stride_seconds=2.0)

    # Every window in seg 1 ends <= 5.0
    assert all(w1_df["window_end"] <= 5.0)
    # Every window in seg 2 starts >= 100.0
    assert all(w2_df["window_start"] >= 100.0)


def test_missing_samples_produce_low_coverage(fixture_synthetic_gapped_segment):
    """Verify that windows covering sparse observations receive quality_flag='LOW_COVERAGE'."""
    df = fixture_synthetic_gapped_segment
    # Window [6.0, 14.0] has zero samples in that range (times are 0..4 and 15..19)
    win_df, _ = generate_windows(
        segment_df=df,
        segment_id="TEST_seg_001",
        window_seconds=8.0,
        stride_seconds=2.0,
        min_coverage_fraction=0.80,
    )

    low_cov_windows = win_df[win_df["quality_flag"] == "LOW_COVERAGE"]
    assert len(low_cov_windows) > 0
    # Confirm they are NOT dropped from the table
    assert len(win_df) == 6


def test_segment_shorter_than_window_produces_zero_windows():
    """Verify that a segment with duration < window_seconds returns an empty table without error."""
    df = pd.DataFrame({"TIME": [10.0, 11.0, 12.0], "COUNTS": [1.0, 2.0, 3.0]})
    win_df, summary = generate_windows(
        segment_df=df,
        segment_id="SHORT_seg_001",
        window_seconds=10.0,  # Duration is 2.0s < 10.0s
        stride_seconds=2.0,
    )

    assert win_df.empty
    assert summary["n_windows"] == 0
    assert summary["status"] == "SEGMENT_TOO_SHORT_FOR_WINDOW"
