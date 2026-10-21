"""Unit tests for solar_flare.preprocessing.filters module.

Tests filter exclusions, exact counts, duplicate resolution policies, and chronological sorting.
All synthetic fixtures are named fixture_synthetic_*.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from solar_flare.preprocessing.filters import (
    exclude_non_finite,
    exclude_negative,
    exclude_flagged,
    resolve_duplicate_timestamps,
    sort_by_time,
    DuplicateTimestampError,
)


@pytest.fixture
def fixture_synthetic_observations() -> pd.DataFrame:
    """Create a synthetic DataFrame with controlled anomalies."""
    times = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0]
    counts = [10.0, np.nan, np.inf, -5.0, 20.0, 0.0, 15.0, 30.0]
    flags = [0, 0, 0, 0, 1, 0, 2, 0]
    return pd.DataFrame({
        "TIME": times,
        "COUNTS": counts,
        "FLAG": flags,
    })


@pytest.fixture
def fixture_synthetic_duplicate_observations() -> pd.DataFrame:
    """Create a synthetic DataFrame containing duplicate timestamps."""
    return pd.DataFrame({
        "TIME": [10.0, 11.0, 11.0, 12.0, 13.0, 13.0, 13.0, 14.0],
        "COUNTS": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0],
    })


def test_exclude_non_finite_exact_counts(fixture_synthetic_observations):
    """Verify that NaN and inf are excluded with exact counts and reason 'NON_FINITE'."""
    df = fixture_synthetic_observations
    filtered_df, excl_log = exclude_non_finite(df, value_col="COUNTS", time_col="TIME")

    assert len(filtered_df) == 6
    assert len(excl_log) == 2
    assert set(excl_log["reason"]) == {"NON_FINITE"}
    assert list(excl_log["original_index"]) == [1, 2]
    assert np.all(np.isfinite(filtered_df["COUNTS"]))


def test_exclude_negative_exact_counts(fixture_synthetic_observations):
    """Verify that negative count values are excluded without clipping."""
    df = fixture_synthetic_observations
    filtered_df, excl_log = exclude_negative(df, value_col="COUNTS", time_col="TIME")

    assert len(filtered_df) == 7
    assert len(excl_log) == 1
    assert excl_log.iloc[0]["reason"] == "NEGATIVE_VALUE"
    assert excl_log.iloc[0]["original_index"] == 3
    assert excl_log.iloc[0]["value"] == -5.0
    assert np.all(filtered_df["COUNTS"].dropna() >= 0.0)


def test_exclude_flagged_exact_counts(fixture_synthetic_observations):
    """Verify that specified quality flags are excluded and logged."""
    df = fixture_synthetic_observations
    filtered_df, excl_log = exclude_flagged(df, flag_col="FLAG", excluded_values=[1, 2], time_col="TIME")

    assert len(filtered_df) == 6
    assert len(excl_log) == 2
    assert set(excl_log["reason"]) == {"QUALITY_FLAG"}
    assert list(excl_log["original_index"]) == [4, 6]
    assert not any(filtered_df["FLAG"].isin([1, 2]))


def test_resolve_duplicates_error_policy(fixture_synthetic_duplicate_observations):
    """Verify that policy='ERROR' raises DuplicateTimestampError when duplicates exist."""
    df = fixture_synthetic_duplicate_observations
    with pytest.raises(DuplicateTimestampError) as exc_info:
        resolve_duplicate_timestamps(df, time_col="TIME", policy="ERROR")
    assert "Detected 5 duplicate timestamp records" in str(exc_info.value)


def test_resolve_duplicates_keep_first(fixture_synthetic_duplicate_observations):
    """Verify that policy='KEEP_FIRST' preserves the first occurrence and logs removals."""
    df = fixture_synthetic_duplicate_observations
    filtered_df, excl_log = resolve_duplicate_timestamps(df, time_col="TIME", policy="KEEP_FIRST")

    assert len(filtered_df) == 5
    assert len(excl_log) == 3
    assert set(excl_log["reason"]) == {"DUPLICATE_TIMESTAMP"}
    assert list(filtered_df["TIME"]) == [10.0, 11.0, 12.0, 13.0, 14.0]
    # Dropped indices were 2 (second 11.0), 5 (second 13.0), 6 (third 13.0)
    assert list(excl_log["original_index"]) == [2, 5, 6]


def test_resolve_duplicates_keep_last(fixture_synthetic_duplicate_observations):
    """Verify that policy='KEEP_LAST' preserves the last occurrence and logs removals."""
    df = fixture_synthetic_duplicate_observations
    filtered_df, excl_log = resolve_duplicate_timestamps(df, time_col="TIME", policy="KEEP_LAST")

    assert len(filtered_df) == 5
    assert len(excl_log) == 3
    assert set(excl_log["reason"]) == {"DUPLICATE_TIMESTAMP"}
    assert list(filtered_df["TIME"]) == [10.0, 11.0, 12.0, 13.0, 14.0]
    # Dropped indices were 1 (first 11.0), 4 (first 13.0), 5 (second 13.0)
    assert list(excl_log["original_index"]) == [1, 4, 5]


def test_sort_by_time_detects_reordering():
    """Verify that sort_by_time sorts correctly and records reordering state."""
    df_unsorted = pd.DataFrame({
        "TIME": [105.0, 101.0, 103.0, 102.0],
        "COUNTS": [50.0, 10.0, 30.0, 20.0],
    })
    sorted_df, log_df = sort_by_time(df_unsorted, time_col="TIME")
    assert list(sorted_df["TIME"]) == [101.0, 102.0, 103.0, 105.0]
    assert log_df.attrs.get("was_reordered") is True

    # Already sorted
    df_sorted = pd.DataFrame({"TIME": [1.0, 2.0, 3.0], "COUNTS": [1.0, 1.0, 1.0]})
    sorted_df2, log_df2 = sort_by_time(df_sorted, time_col="TIME")
    assert log_df2.attrs.get("was_reordered") is False
