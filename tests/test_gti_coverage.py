"""Unit tests for solar_flare.quality.gti_coverage module.

Uses synthetic FITS files created strictly inside pytest tmp_path.
Never creates or modifies any file in data/raw/.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pytest
from astropy.io import fits

from solar_flare.quality.gti_coverage import (
    load_gti_intervals,
    compute_coverage,
    GTIColumnError,
)


@pytest.fixture
def fixture_synthetic_valid_gti_fits(tmp_path: Path) -> Path:
    """Create a synthetic GTI FITS file with two valid intervals."""
    file_path = tmp_path / "synthetic_valid.gti.fits"
    starts = np.array([100.0, 200.0], dtype=np.float64)
    stops = np.array([150.0, 250.0], dtype=np.float64)

    col1 = fits.Column(name="START", format="D", array=starts)
    col2 = fits.Column(name="STOP", format="D", array=stops)
    table_hdu = fits.BinTableHDU.from_columns([col1, col2], name="GTI")
    primary_hdu = fits.PrimaryHDU()
    hdul = fits.HDUList([primary_hdu, table_hdu])
    hdul.writeto(file_path, overwrite=True)
    return file_path


@pytest.fixture
def fixture_synthetic_empty_gti_fits(tmp_path: Path) -> Path:
    """Create a synthetic GTI FITS file with zero rows."""
    file_path = tmp_path / "synthetic_empty.gti.fits"
    col1 = fits.Column(name="START", format="D", array=np.array([], dtype=np.float64))
    col2 = fits.Column(name="STOP", format="D", array=np.array([], dtype=np.float64))
    table_hdu = fits.BinTableHDU.from_columns([col1, col2], name="GTI")
    primary_hdu = fits.PrimaryHDU()
    hdul = fits.HDUList([primary_hdu, table_hdu])
    hdul.writeto(file_path, overwrite=True)
    return file_path


@pytest.fixture
def fixture_synthetic_wrong_cols_gti_fits(tmp_path: Path) -> Path:
    """Create a synthetic GTI FITS file with missing START/STOP columns."""
    file_path = tmp_path / "synthetic_wrong_cols.gti.fits"
    col1 = fits.Column(name="T_BEGIN", format="D", array=np.array([10.0]))
    col2 = fits.Column(name="T_END", format="D", array=np.array([20.0]))
    table_hdu = fits.BinTableHDU.from_columns([col1, col2], name="GTI")
    primary_hdu = fits.PrimaryHDU()
    hdul = fits.HDUList([primary_hdu, table_hdu])
    hdul.writeto(file_path, overwrite=True)
    return file_path


def test_load_gti_intervals_valid(fixture_synthetic_valid_gti_fits):
    """Verify loading valid GTI file returns intervals."""
    gti_data = load_gti_intervals(fixture_synthetic_valid_gti_fits, start_col="START", stop_col="STOP")
    assert gti_data["status"] == "VALID"
    assert gti_data["n_intervals"] == 2
    assert gti_data["intervals"][0]["start"] == 100.0
    assert gti_data["intervals"][0]["stop"] == 150.0
    assert len(gti_data["inverted"]) == 0
    assert len(gti_data["overlaps"]) == 0


def test_compute_coverage_known_fraction(fixture_synthetic_valid_gti_fits):
    """Verify compute_coverage calculates exact covered fraction."""
    gti_data = load_gti_intervals(fixture_synthetic_valid_gti_fits)
    # Observation from 100 to 299 (200 points, 1s step)
    times = np.arange(100.0, 300.0, 1.0)
    # Interval 1: [100, 150] -> 51 points (100..150)
    # Interval 2: [200, 250] -> 51 points (200..250)
    # Total inside = 102 points out of 200 = 0.51
    res = compute_coverage(times, gti_data)

    assert res["gti_status"] == "VALID"
    assert res["n_intervals"] == 2
    assert res["n_samples_inside_gti"] == 102
    assert res["n_samples_outside_gti"] == 98
    assert pytest.approx(res["gti_covered_fraction"], 0.001) == 0.51


def test_empty_gti_produces_empty_observation_status(fixture_synthetic_empty_gti_fits):
    """Verify empty GTI file records 'GTI EMPTY FOR THIS OBSERVATION' and does not substitute."""
    gti_data = load_gti_intervals(fixture_synthetic_empty_gti_fits)
    assert gti_data["status"] == "EMPTY"
    assert gti_data["message"] == "GTI EMPTY FOR THIS OBSERVATION"
    assert gti_data["n_intervals"] == 0

    times = np.arange(100.0, 200.0, 1.0)
    cov = compute_coverage(times, gti_data)
    assert cov["gti_status"] == "GTI EMPTY FOR THIS OBSERVATION"
    assert cov["gti_covered_fraction"] == 0.0
    assert cov["n_samples_inside_gti"] == 0
    assert cov["n_samples_outside_gti"] == 100


def test_missing_gti_column_names_refuses(fixture_synthetic_wrong_cols_gti_fits):
    """Verify missing GTI column names produces a clear refusal via GTIColumnError."""
    with pytest.raises(GTIColumnError) as exc_info:
        load_gti_intervals(fixture_synthetic_wrong_cols_gti_fits, start_col="START", stop_col="STOP")

    assert "not found in" in str(exc_info.value)
    assert "Refusing to execute with unconfirmed column names" in str(exc_info.value)
