"""Unit tests for solar_flare.labels.matching module.

Tests interval overlap algorithms and tolerance boundary enforcement.
"""

from __future__ import annotations

import pytest

from solar_flare.labels.matching import interval_overlap_seconds, is_event_in_window


def test_interval_overlap_exact_seconds():
    """Verify exact overlap duration calculation."""
    # Window [100, 160] (duration 60s), Event [120, 150] (duration 30s)
    overlap = interval_overlap_seconds(100.0, 160.0, 120.0, 150.0, tolerance_seconds=0.0)
    assert overlap == 30.0


def test_interval_overlap_tolerance_boundary():
    """Verify tolerance boundary expansion captures near-boundary events."""
    # Window [100, 160], Event [170, 200]
    # At tolerance=0, no overlap
    overlap_zero = interval_overlap_seconds(100.0, 160.0, 170.0, 200.0, tolerance_seconds=0.0)
    assert overlap_zero == 0.0

    # At tolerance=20, window expands to [80, 180]. Overlap with [170, 200] is [170, 180] = 10s
    overlap_tol = interval_overlap_seconds(100.0, 160.0, 170.0, 200.0, tolerance_seconds=20.0)
    assert overlap_tol == 10.0


def test_missing_tolerance_raises_error():
    """Verify that calling without tolerance_seconds or with None raises."""
    # Calling without argument raises TypeError
    with pytest.raises(TypeError):
        interval_overlap_seconds(100.0, 160.0, 120.0, 150.0)  # type: ignore

    # Calling with None raises ValueError
    with pytest.raises(ValueError):
        interval_overlap_seconds(100.0, 160.0, 120.0, 150.0, tolerance_seconds=None)  # type: ignore


def test_is_event_in_window():
    """Verify window-level positive label decision rule."""
    # Window 60s [100, 160], Event [120, 160] (40s overlap = 66.7% of window)
    assert is_event_in_window(100.0, 160.0, 120.0, 160.0, tolerance_seconds=0.0, min_overlap_fraction=0.5) is True

    # Overlap only 10s (16.7%) -> fails 50% fraction requirement
    assert is_event_in_window(100.0, 160.0, 150.0, 160.0, tolerance_seconds=0.0, min_overlap_fraction=0.5) is False
