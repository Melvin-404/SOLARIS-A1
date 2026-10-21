"""Unit tests for solar_flare.labels.schema module.

Uses synthetic fixtures named fixture_synthetic_*.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

from solar_flare.labels.schema import validate_event_records


@pytest.fixture
def fixture_synthetic_sources_csv(tmp_path: Path) -> Path:
    """Create a temporary event_sources.csv for testing."""
    csv_path = tmp_path / "event_sources.csv"
    csv_path.write_text(
        "source_id,source_name,url_accessed,access_date,version,instrument,energy_band_as_stated,time_system_as_stated,coverage_start,coverage_end,event_definition_as_stated,classification_method_as_stated,licence_or_terms_as_stated,independent_of_solarsoft_heuristic,verified_by_human,notes\n"
        "SRC_TEST_GOES,Test GOES Source,https://example.com/goes,2026-10-21,v1.0,GOES,0.1-0.8 nm,UTC,1975,2026,begin/max/end,peak flux,public,yes,no,test\n",
        encoding="utf-8"
    )
    return csv_path


@pytest.fixture
def fixture_synthetic_valid_event_df():
    """Create a valid event records DataFrame."""
    return pd.DataFrame([
        {
            "event_id": "EVT_001",
            "source_id": "SRC_TEST_GOES",
            "onset_time": 1000.0,
            "peak_time": 1020.0,
            "end_time": 1050.0,
            "time_system": "UTC",
            "classification": "M1.2",
            "classification_method": "GOES_PEAK_FLUX",
        }
    ])


@pytest.fixture
def fixture_synthetic_config():
    """Config dictionary with approved time systems."""
    return {
        "labels": {
            "allowed_time_systems": ["UTC", "TAI"],
        }
    }


def test_validate_event_records_valid(fixture_synthetic_valid_event_df, fixture_synthetic_config, fixture_synthetic_sources_csv):
    """Verify that a valid record passes validation."""
    assert validate_event_records(
        fixture_synthetic_valid_event_df,
        config=fixture_synthetic_config,
        event_sources_path=fixture_synthetic_sources_csv,
    ) is True


def test_validate_event_records_onset_greater_than_peak(fixture_synthetic_valid_event_df, fixture_synthetic_config, fixture_synthetic_sources_csv):
    """Verify that onset > peak raises ValueError."""
    bad_df = fixture_synthetic_valid_event_df.copy()
    bad_df["onset_time"] = 1030.0
    bad_df["peak_time"] = 1020.0  # onset > peak!

    with pytest.raises(ValueError) as exc:
        validate_event_records(bad_df, config=fixture_synthetic_config, event_sources_path=fixture_synthetic_sources_csv)
    assert "violates temporal sequence" in str(exc.value)


def test_validate_event_records_missing_time_system(fixture_synthetic_valid_event_df, fixture_synthetic_config, fixture_synthetic_sources_csv):
    """Verify that missing time_system column raises ValueError."""
    bad_df = fixture_synthetic_valid_event_df.drop(columns=["time_system"])
    with pytest.raises(ValueError) as exc:
        validate_event_records(bad_df, config=fixture_synthetic_config, event_sources_path=fixture_synthetic_sources_csv)
    assert "missing required field" in str(exc.value).lower()


def test_validate_event_records_unrecognised_time_system(fixture_synthetic_valid_event_df, fixture_synthetic_config, fixture_synthetic_sources_csv):
    """Verify that unrecognised time_system raises ValueError."""
    bad_df = fixture_synthetic_valid_event_df.copy()
    bad_df["time_system"] = "MARTIAN_LOCAL_TIME"
    with pytest.raises(ValueError) as exc:
        validate_event_records(bad_df, config=fixture_synthetic_config, event_sources_path=fixture_synthetic_sources_csv)
    assert "unapproved time_system" in str(exc.value)


def test_validate_event_records_duplicate_event_id(fixture_synthetic_valid_event_df, fixture_synthetic_config, fixture_synthetic_sources_csv):
    """Verify that duplicate event_id raises ValueError."""
    dup_df = pd.concat([fixture_synthetic_valid_event_df, fixture_synthetic_valid_event_df], ignore_index=True)
    with pytest.raises(ValueError) as exc:
        validate_event_records(dup_df, config=fixture_synthetic_config, event_sources_path=fixture_synthetic_sources_csv)
    assert "Duplicate event_id" in str(exc.value)


def test_validate_event_records_unknown_source_id(fixture_synthetic_valid_event_df, fixture_synthetic_config, fixture_synthetic_sources_csv):
    """Verify that unknown source_id raises ValueError."""
    bad_df = fixture_synthetic_valid_event_df.copy()
    bad_df["source_id"] = "SRC_FABRICATED_MYTH"
    with pytest.raises(ValueError) as exc:
        validate_event_records(bad_df, config=fixture_synthetic_config, event_sources_path=fixture_synthetic_sources_csv)
    assert "unknown source_id" in str(exc.value)
