"""Unit tests for solar_flare.preprocessing.gti_apply module.

Tests boundary conditions, outside-GTI exclusion, and empty GTI behavior.
All synthetic fixtures are named fixture_synthetic_*.
"""

from __future__ import annotations

import pandas as pd
import pytest

from solar_flare.preprocessing.gti_apply import apply_gti


@pytest.fixture
def fixture_synthetic_boundary_data() -> pd.DataFrame:
    """Create a DataFrame with timestamps exactly on and near interval boundaries.
    
    Interval under test: [100.0, 200.0]
    Points: 99.0 (outside left), 100.0 (start), 150.0 (middle), 200.0 (stop), 201.0 (outside right)
    """
    return pd.DataFrame({
        "TIME": [99.0, 100.0, 150.0, 200.0, 201.0],
        "COUNTS": [10.0, 11.0, 12.0, 13.0, 14.0],
    })


@pytest.fixture
def fixture_synthetic_gti_interval() -> list:
    """Return a single test GTI interval."""
    return [{"START": 100.0, "STOP": 200.0}]


def test_gti_boundary_start_inclusive_stop_exclusive(
    fixture_synthetic_boundary_data, fixture_synthetic_gti_interval
):
    """Verify START_INCLUSIVE_STOP_EXCLUSIVE retains start (100.0) but excludes stop (200.0)."""
    df = fixture_synthetic_boundary_data
    gti = fixture_synthetic_gti_interval

    filtered_df, excl_log = apply_gti(
        df, time_col="TIME", gti_intervals=gti, boundary="START_INCLUSIVE_STOP_EXCLUSIVE"
    )

    # Retained: 100.0, 150.0 (2 samples)
    assert list(filtered_df["TIME"]) == [100.0, 150.0]
    assert filtered_df["gti_flag"].all()

    # Excluded: 99.0, 200.0, 201.0 (3 samples)
    assert list(excl_log["time"]) == [99.0, 200.0, 201.0]
    assert set(excl_log["reason"]) == {"OUTSIDE_GTI"}
    assert len(filtered_df) + len(excl_log) == len(df)


def test_gti_boundary_start_exclusive_stop_inclusive(
    fixture_synthetic_boundary_data, fixture_synthetic_gti_interval
):
    """Verify START_EXCLUSIVE_STOP_INCLUSIVE excludes start (100.0) but retains stop (200.0)."""
    df = fixture_synthetic_boundary_data
    gti = fixture_synthetic_gti_interval

    filtered_df, excl_log = apply_gti(
        df, time_col="TIME", gti_intervals=gti, boundary="START_EXCLUSIVE_STOP_INCLUSIVE"
    )

    # Retained: 150.0, 200.0 (2 samples)
    assert list(filtered_df["TIME"]) == [150.0, 200.0]

    # Excluded: 99.0, 100.0, 201.0 (3 samples)
    assert list(excl_log["time"]) == [99.0, 100.0, 201.0]
    assert len(filtered_df) + len(excl_log) == len(df)


def test_gti_boundary_both_inclusive(
    fixture_synthetic_boundary_data, fixture_synthetic_gti_interval
):
    """Verify BOTH_INCLUSIVE retains both start (100.0) and stop (200.0)."""
    df = fixture_synthetic_boundary_data
    gti = fixture_synthetic_gti_interval

    filtered_df, excl_log = apply_gti(
        df, time_col="TIME", gti_intervals=gti, boundary="BOTH_INCLUSIVE"
    )

    # Retained: 100.0, 150.0, 200.0 (3 samples)
    assert list(filtered_df["TIME"]) == [100.0, 150.0, 200.0]

    # Excluded: 99.0, 201.0 (2 samples)
    assert list(excl_log["time"]) == [99.0, 201.0]
    assert len(filtered_df) + len(excl_log) == len(df)


def test_gti_empty_intervals_retains_no_samples():
    """Verify that an empty GTI table retains 0 samples and logs the empty GTI explanation."""
    df = pd.DataFrame({
        "TIME": [10.0, 20.0, 30.0],
        "COUNTS": [1.0, 2.0, 3.0],
    })

    filtered_df, excl_log = apply_gti(
        df, time_col="TIME", gti_intervals=[], boundary="START_INCLUSIVE_STOP_EXCLUSIVE"
    )

    assert len(filtered_df) == 0
    assert len(excl_log) == 3
    assert set(excl_log["reason"]) == {"OUTSIDE_GTI"}
    assert "GTI EMPTY" in excl_log.iloc[0]["details"]
    assert len(filtered_df) + len(excl_log) == len(df)


def test_gti_invalid_boundary_raises_error(fixture_synthetic_boundary_data):
    """Verify that an invalid boundary convention raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        apply_gti(fixture_synthetic_boundary_data, time_col="TIME", gti_intervals=[], boundary="INVALID_BOUNDARY")
    assert "Invalid GTI boundary convention" in str(exc_info.value)
