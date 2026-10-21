"""Unit tests for solar_flare.inspection module.

All test fixtures use synthetic FITS files created strictly in pytest tmp_path
(named fixture_synthetic_*.fits). No scientific data is created or modified.
"""

import hashlib
from pathlib import Path
import numpy as np
import pytest
from astropy.io import fits
import pandas as pd

from solar_flare.inspection.fits_inspect import (
    list_hdus,
    describe_columns,
    summarise_numeric_columns,
    summarise_time_columns,
    read_header_dict,
    InspectionError,
)
from solar_flare.inspection.time_systems import extract_time_system_metadata
from solar_flare.inspection.inventory import build_inventory, _detect_candidate_roles


def _create_synthetic_fits(
    path: Path,
    rows: int = 50,
    add_nan: bool = True,
    add_inf: bool = True,
) -> Path:
    """Helper to generate a clean synthetic FITS fixture."""
    primary = fits.PrimaryHDU()
    primary.header["TELESCOP"] = "SYNTHETIC_TEL"
    primary.header["INSTRUME"] = "SYNTHETIC_INST"
    primary.header["OBS_ID"] = "TEST_OBS_999"

    times = np.arange(rows, dtype=np.float64) * 2.0  # 2-second spacing
    rates = np.linspace(10.0, 100.0, rows)

    if add_nan and rows > 5:
        rates[2] = np.nan
        rates[4] = np.nan
    if add_inf and rows > 6:
        rates[6] = np.inf

    col1 = fits.Column(name="TIME", format="D", unit="s", array=times)
    col2 = fits.Column(name="COUNTS", format="D", unit="count", array=rates)
    cols = fits.ColDefs([col1, col2])
    table_hdu = fits.BinTableHDU.from_columns(cols, name="RATE")

    table_hdu.header["TIMESYS"] = "UTC"
    table_hdu.header["MJDREFI"] = 40587
    table_hdu.header["TSTART"] = 0.0
    table_hdu.header["TSTOP"] = float(times[-1])
    table_hdu.header["TIMEUNIT"] = "s"

    hdul = fits.HDUList([primary, table_hdu])
    hdul.writeto(str(path), overwrite=True)
    return path


def test_list_hdus(tmp_path):
    """Verify list_hdus reports correct extension names, types, and counts."""
    fpath = tmp_path / "fixture_synthetic_structure.fits"
    _create_synthetic_fits(fpath, rows=20)

    hdus = list_hdus(fpath)
    assert len(hdus) == 2
    assert hdus[0]["name"] == "PRIMARY"
    assert hdus[0]["type"] == "PrimaryHDU"
    assert hdus[1]["name"] == "RATE"
    assert hdus[1]["type"] == "BinTableHDU"
    assert hdus[1]["rows"] == 20
    assert hdus[1]["columns_count"] == 2


def test_describe_columns(tmp_path):
    """Verify describe_columns extracts names, formats, and units."""
    fpath = tmp_path / "fixture_synthetic_cols.fits"
    _create_synthetic_fits(fpath, rows=10)

    cols = describe_columns(fpath, hdu=1)
    assert len(cols) == 2
    assert cols[0]["name"] == "TIME"
    assert cols[0]["unit"] == "s"
    assert cols[1]["name"] == "COUNTS"
    assert cols[1]["unit"] == "count"


def test_summarise_numeric_columns(tmp_path):
    """Verify numeric summaries correctly count NaN, Inf, and finite extremes."""
    fpath = tmp_path / "fixture_synthetic_stats.fits"
    _create_synthetic_fits(fpath, rows=30, add_nan=True, add_inf=True)

    stats = summarise_numeric_columns(fpath, hdu=1)
    assert "COUNTS" in stats
    c_stats = stats["COUNTS"]
    assert c_stats["count"] == 30
    assert c_stats["nan_count"] == 2
    assert c_stats["inf_count"] == 1
    assert c_stats["finite_count"] == 27
    assert c_stats["min"] is not None
    assert c_stats["max"] is not None


def test_summarise_time_columns(tmp_path):
    """Verify time column diagnostics detect candidate time axis and spacing."""
    fpath = tmp_path / "fixture_synthetic_time.fits"
    _create_synthetic_fits(fpath, rows=25, add_nan=False, add_inf=False)

    time_stats = summarise_time_columns(fpath, hdu=1)
    assert len(time_stats) >= 1
    ts = time_stats[0]
    assert ts["column_name"] == "TIME"
    assert ts["median_spacing"] == pytest.approx(2.0)
    assert ts["is_monotonic"] is True
    assert ts["unique_count"] == 25


def test_time_system_metadata(tmp_path):
    """Verify extraction of time keywords and candidate interpretations."""
    fpath = tmp_path / "fixture_synthetic_time_meta.fits"
    _create_synthetic_fits(fpath)

    meta = extract_time_system_metadata(fpath)
    assert "TIMESYS" in meta["consolidated_keywords"]
    assert meta["consolidated_keywords"]["TIMESYS"] == "UTC"
    assert "MJDREFI" in meta["consolidated_keywords"]
    assert meta["consolidated_keywords"]["MJDREFI"] == 40587
    assert any("candidate interpretation" in interp for interp in meta["candidate_interpretations"])


def test_non_fits_file_raises_inspection_error(tmp_path):
    """Verify opening a non-FITS file raises InspectionError."""
    fake_file = tmp_path / "fixture_synthetic_corrupt.txt"
    fake_file.write_text("This is not a FITS file.", encoding="utf-8")

    with pytest.raises(InspectionError):
        list_hdus(fake_file)


def test_missing_hdu_raises_inspection_error(tmp_path):
    """Verify requesting an invalid HDU raises InspectionError gracefully."""
    fpath = tmp_path / "fixture_synthetic_missing_hdu.fits"
    _create_synthetic_fits(fpath)

    with pytest.raises(InspectionError) as exc_info:
        describe_columns(fpath, hdu="NON_EXISTENT_EXTENSION")
    assert "not found" in str(exc_info.value)


def test_read_only_guarantee_hash_unchanged(tmp_path):
    """Verify that all inspection functions preserve the exact byte hash of the target file."""
    fpath = tmp_path / "fixture_synthetic_readonly.fits"
    _create_synthetic_fits(fpath, rows=40)

    hash_before = hashlib.sha256(fpath.read_bytes()).hexdigest()

    # Run all inspection routines
    list_hdus(fpath)
    read_header_dict(fpath, hdu=0)
    read_header_dict(fpath, hdu=1)
    describe_columns(fpath, hdu=1)
    summarise_numeric_columns(fpath, hdu=1)
    summarise_time_columns(fpath, hdu=1)
    extract_time_system_metadata(fpath)

    hash_after = hashlib.sha256(fpath.read_bytes()).hexdigest()
    assert hash_after == hash_before


def test_inventory_ambiguous_columns_marked_unresolved(tmp_path):
    """Verify that multiple candidate columns in the same category are marked UNRESOLVED."""
    fpath = tmp_path / "fixture_synthetic_ambiguous.fits"

    primary = fits.PrimaryHDU()
    col1 = fits.Column(name="TIME_UTC", format="D", array=[1.0, 2.0])
    col2 = fits.Column(name="TIME_MET", format="D", array=[10.0, 20.0])
    col3 = fits.Column(name="RATE_CHANNEL_A", format="D", array=[100.0, 105.0])
    col4 = fits.Column(name="RATE_CHANNEL_B", format="D", array=[200.0, 210.0])

    cols = fits.ColDefs([col1, col2, col3, col4])
    table = fits.BinTableHDU.from_columns(cols, name="RATE")
    fits.HDUList([primary, table]).writeto(str(fpath), overwrite=True)

    cols_desc = describe_columns(fpath, hdu=1)
    roles = _detect_candidate_roles(cols_desc)

    assert "UNRESOLVED" in roles["time_candidates"]
    assert "UNRESOLVED" in roles["count_rate_candidates"]

    # Test within build_inventory
    manifest_df = pd.DataFrame([{
        "file_name": fpath.name,
        "file_type": "LIGHTCURVE",
        "observation_id": "OBS_AMBIGUOUS",
        "paired_gti_file": "",
        "pairing_verified": "no",
    }])

    inv = build_inventory(tmp_path, manifest_df)
    assert len(inv) == 1
    assert "UNRESOLVED" in inv.iloc[0]["detected_time_candidates"]
    assert "UNRESOLVED" in inv.iloc[0]["detected_count_rate_candidates"]
