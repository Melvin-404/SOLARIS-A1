"""Unit tests for solar_flare.labels.compatibility module.

Tests temporal overlap calculation and compatibility status assignment rules.
"""

from __future__ import annotations

import pytest

from solar_flare.labels.compatibility import (
    report_temporal_overlap,
    assess_source_compatibility,
)


def test_time_system_unconfirmed_returned_when_unknown():
    """Verify that TIME_SYSTEM_UNCONFIRMED is strictly returned when time system is unconfirmed."""
    record = {
        "source_id": "SRC_TEST",
        "verified_by_human": "no",
    }
    # Even with a positive overlap, if time_system_confirmed is False, must return TIME_SYSTEM_UNCONFIRMED
    status = assess_source_compatibility(record, time_system_confirmed=False, overlap_result=3600.0)
    assert status == "TIME_SYSTEM_UNCONFIRMED"


def test_report_temporal_overlap_disjoint_returns_no_overlap():
    """Verify that disjoint intervals return 'NO OVERLAP'."""
    # SoLEXS [1000, 2000], External [3000, 4000]
    res = report_temporal_overlap(1000.0, 2000.0, 3000.0, 4000.0)
    assert res == "NO OVERLAP"


def test_report_temporal_overlap_positive():
    """Verify that overlapping intervals return exact overlap duration in seconds."""
    # SoLEXS [1000, 2000], External [1500, 2500] -> overlap [1500, 2000] = 500s
    res = report_temporal_overlap(1000.0, 2000.0, 1500.0, 2500.0)
    assert res == 500.0


def test_assess_source_compatibility_no_overlap_when_confirmed():
    """Verify NO_OVERLAP status when time system is confirmed but intervals are disjoint."""
    record = {"source_id": "SRC_TEST", "verified_by_human": "no"}
    status = assess_source_compatibility(record, time_system_confirmed=True, overlap_result="NO OVERLAP")
    assert status == "NO_OVERLAP"


def test_assess_source_compatibility_compatible_pending_approval():
    """Verify COMPATIBLE_PENDING_APPROVAL when confirmed and human verified."""
    record = {"source_id": "SRC_TEST", "verified_by_human": "yes"}
    status = assess_source_compatibility(record, time_system_confirmed=True, overlap_result=500.0)
    assert status == "COMPATIBLE_PENDING_APPROVAL"
