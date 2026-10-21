"""Unit tests for solar_flare.eda.event_comparison module.

Uses synthetic fixtures named fixture_synthetic_*.
"""

from __future__ import annotations

import pandas as pd
import pytest

from solar_flare.eda.event_comparison import compare_candidates_to_events


@pytest.fixture
def fixture_synthetic_candidates():
    """Synthetic candidate burst intervals."""
    return pd.DataFrame([
        {
            "candidate_id": "CAND_001",
            "start": 100.0,
            "end": 150.0,
            "duration": 50.0,
            "peak_time": 125.0,
            "peak_value": 85.0,
            "status": "CANDIDATE — UNVERIFIED",
        },
        {
            "candidate_id": "CAND_002",
            "start": 1000.0,
            "end": 1080.0,
            "duration": 80.0,
            "peak_time": 1040.0,
            "peak_value": 110.0,
            "status": "CANDIDATE — UNVERIFIED",
        },
    ])


@pytest.fixture
def fixture_synthetic_events():
    """Synthetic external event catalog records."""
    return pd.DataFrame([
        {
            "event_id": "FLARE_A",
            "event_start": 130.0,
            "event_end": 200.0,
            "flare_class": "C2.1",
        },
        {
            "event_id": "FLARE_B",
            "event_start": 5000.0,
            "event_end": 5200.0,
            "flare_class": "M1.0",
        },
    ])


def test_event_comparison_none_returns_not_performed(fixture_synthetic_candidates):
    """Verify compare_candidates_to_events returns NOT PERFORMED when events_df is None."""
    res = compare_candidates_to_events(fixture_synthetic_candidates, events_df=None)
    assert res["status"] == "NOT PERFORMED — no independent event records supplied"
    assert res["n_candidates"] == 2
    assert res["n_events"] == 0
    assert len(res["matches"]) == 0


def test_event_comparison_empty_df_returns_not_performed(fixture_synthetic_candidates):
    """Verify compare_candidates_to_events returns NOT PERFORMED when events_df is empty."""
    res = compare_candidates_to_events(fixture_synthetic_candidates, events_df=pd.DataFrame())
    assert res["status"] == "NOT PERFORMED — no independent event records supplied"
    assert res["n_events"] == 0


def test_event_comparison_overlap_logic(fixture_synthetic_candidates, fixture_synthetic_events):
    """Verify overlap matching logic when synthetic event records are provided."""
    res = compare_candidates_to_events(
        fixture_synthetic_candidates,
        events_df=fixture_synthetic_events,
        tolerance_seconds=10.0,
    )
    assert res["status"] == "COMPLETED"
    assert res["n_candidates"] == 2
    assert res["n_events"] == 2
    # CAND_001 [100, 150] overlaps FLARE_A [130, 200]
    assert len(res["matches"]) == 1
    match = res["matches"][0]
    assert match["candidate_id"] == "CAND_001"
    assert match["event_id"] == "FLARE_A"
