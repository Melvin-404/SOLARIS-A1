"""Unit tests for solar_flare.quality.roles module.

Uses synthetic FITS fixtures created strictly inside pytest tmp_path.
Never creates or modifies any file in data/raw/.
"""

from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pytest
from astropy.io import fits

from solar_flare.quality.roles import compile_file_role_evidence, generate_column_role_evidence


@pytest.fixture
def fixture_synthetic_lc_fits(tmp_path: Path) -> Path:
    """Create a synthetic LC FITS file with TIME and COUNTS."""
    file_path = tmp_path / "synthetic_test_SDD2_L1.lc.fits"
    times = np.arange(1000.0, 1050.0, 1.0)
    counts = np.ones(50) * 12.0
    counts[10] = np.nan
    counts[20] = 0.0

    col1 = fits.Column(name="TIME", format="D", array=times)
    col2 = fits.Column(name="COUNTS", format="D", array=counts)
    table_hdu = fits.BinTableHDU.from_columns([col1, col2], name="RATE")

    primary_hdu = fits.PrimaryHDU()
    primary_hdu.header["TELESCOP"] = "AL1"
    primary_hdu.header["INSTRUME"] = "SoLEXS"
    primary_hdu.header["FILTER"] = "SDD2"
    primary_hdu.header["NUMBAND"] = 4
    primary_hdu.header["TIMESYS"] = "UTC"
    primary_hdu.header["MJDREFI"] = 40587

    hdul = fits.HDUList([primary_hdu, table_hdu])
    hdul.writeto(file_path, overwrite=True)
    return file_path


@pytest.fixture
def fixture_synthetic_gti_fits(tmp_path: Path) -> Path:
    """Create a synthetic GTI FITS file with START and STOP."""
    file_path = tmp_path / "synthetic_test_SDD2_L1.gti.fits"
    starts = np.array([1000.0, 1025.0], dtype=np.float64)
    stops = np.array([1020.0, 1045.0], dtype=np.float64)

    col1 = fits.Column(name="START", format="D", array=starts)
    col2 = fits.Column(name="STOP", format="D", array=stops)
    table_hdu = fits.BinTableHDU.from_columns([col1, col2], name="GTI")
    primary_hdu = fits.PrimaryHDU()
    hdul = fits.HDUList([primary_hdu, table_hdu])
    hdul.writeto(file_path, overwrite=True)
    return file_path


def test_compile_file_role_evidence_lc(fixture_synthetic_lc_fits):
    """Verify evidence compilation extracts candidate roles with PROVISIONAL status."""
    ev = compile_file_role_evidence(fixture_synthetic_lc_fits)
    assert ev["file_type"] == "LIGHTCURVE"
    roles = ev["candidate_roles"]

    # TIME role
    assert "time" in roles
    assert roles["time"]["candidate_column"] == "TIME"
    assert roles["time"]["status"] == "PROVISIONAL"
    assert "requires human confirmation (G1)" in roles["time"]["note"]
    assert roles["time"]["monotonic"] is True

    # COUNT role
    assert "count_or_rate" in roles
    assert roles["count_or_rate"]["candidate_column"] == "COUNTS"
    assert roles["count_or_rate"]["status"] == "PROVISIONAL"
    assert roles["count_or_rate"]["n_nan"] == 1
    assert roles["count_or_rate"]["n_zeros"] == 1

    # Quality flag role
    assert "quality_flag" in roles
    assert roles["quality_flag"]["status"] == "UNRESOLVED"


def test_generate_column_role_evidence_pipeline(tmp_path, fixture_synthetic_lc_fits, fixture_synthetic_gti_fits):
    """Verify full column-role evidence compilation generates JSON and MD outputs."""
    raw_synthetic_dir = tmp_path / "raw_syn"
    raw_synthetic_dir.mkdir()
    # Move or copy fixtures
    import shutil
    shutil.copy(fixture_synthetic_lc_fits, raw_synthetic_dir / fixture_synthetic_lc_fits.name)
    shutil.copy(fixture_synthetic_gti_fits, raw_synthetic_dir / fixture_synthetic_gti_fits.name)

    out_json = tmp_path / "out" / "column_role_evidence.json"
    out_md = tmp_path / "out" / "column_role_evidence.md"

    res = generate_column_role_evidence(raw_synthetic_dir, out_json, out_md)

    assert out_json.is_file()
    assert out_md.is_file()

    with open(out_json, "r", encoding="utf-8") as jf:
        data = json.load(jf)
    assert len(data) == 2

    md_content = out_md.read_text(encoding="utf-8")
    assert "CRITICAL NOTICE (Gate G1)" in md_content
    assert "Gate G1 Action Checklist" in md_content
