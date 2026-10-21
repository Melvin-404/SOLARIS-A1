"""Unit tests for solar_flare.manifest and scripts/check_manifest.py.

All tests utilize synthetic dummy test fixtures (named test_fixture_*.bin)
created inside pytest tmp_path fixtures. No scientific data is created.
"""

import hashlib
from pathlib import Path
import pytest
import pandas as pd

from solar_flare.manifest import (
    load_manifest,
    compute_sha256,
    verify_manifest_against_disk,
    ManifestError,
    REQUIRED_MANIFEST_COLUMNS,
)
from scripts.check_manifest import main as cli_main


def _create_csv_manifest(path: Path, rows: list[dict]) -> Path:
    """Helper to write rows into a valid manifest CSV."""
    df = pd.DataFrame(rows)
    # Ensure all required columns exist
    for col in REQUIRED_MANIFEST_COLUMNS:
        if col not in df.columns:
            df[col] = "N/A"
    df.to_csv(path, index=False)
    return path


def test_compute_sha256_correctness(tmp_path):
    """Verify compute_sha256 matches hashlib output byte-for-byte."""
    dummy_file = tmp_path / "test_fixture_payload.bin"
    sample_bytes = b"SolarisA1-Test-Payload-Binary-Data-For-Chunking-Verification-12345" * 1000
    dummy_file.write_bytes(sample_bytes)

    expected_hash = hashlib.sha256(sample_bytes).hexdigest().lower()
    actual_hash = compute_sha256(dummy_file)

    assert actual_hash == expected_hash
    assert len(actual_hash) == 64


def test_load_manifest_valid(tmp_path):
    """Verify loading a valid manifest DataFrame."""
    manifest_file = tmp_path / "manifest.csv"
    _create_csv_manifest(manifest_file, [{
        "file_name": "test_fixture_01.bin",
        "file_type": "LIGHTCURVE",
        "observation_id": "OBS_001",
        "sha256": "abc123",
        "pairing_verified": "yes",
    }])

    df = load_manifest(manifest_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert "file_name" in df.columns
    assert df.iloc[0]["observation_id"] == "OBS_001"


def test_load_manifest_missing_column(tmp_path):
    """Verify load_manifest raises ManifestError if required columns are absent."""
    manifest_file = tmp_path / "bad_manifest.csv"
    manifest_file.write_text("file_name,file_type\ntest.bin,LIGHTCURVE\n", encoding="utf-8")

    with pytest.raises(ManifestError) as exc_info:
        load_manifest(manifest_file)
    assert "missing required columns" in str(exc_info.value)


def test_load_manifest_not_found():
    """Verify load_manifest raises FileNotFoundError for non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_manifest("non_existent_manifest.csv")


def test_verify_manifest_clean(tmp_path):
    """Verify clean manifest with matched lightcurve and GTI exits with 0 errors."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    lc_file = raw_dir / "test_fixture_lc.bin"
    gti_file = raw_dir / "test_fixture_gti.bin"

    lc_bytes = b"Lightcurve-Fixture-Bytes"
    gti_bytes = b"GTI-Fixture-Bytes"

    lc_file.write_bytes(lc_bytes)
    gti_file.write_bytes(gti_bytes)

    lc_hash = hashlib.sha256(lc_bytes).hexdigest()
    gti_hash = hashlib.sha256(gti_bytes).hexdigest()

    manifest_file = tmp_path / "manifest.csv"
    _create_csv_manifest(manifest_file, [
        {
            "file_name": "test_fixture_lc.bin",
            "file_type": "LIGHTCURVE",
            "sha256": lc_hash,
            "paired_gti_file": "test_fixture_gti.bin",
            "pairing_verified": "yes",
        },
        {
            "file_name": "test_fixture_gti.bin",
            "file_type": "GTI",
            "sha256": gti_hash,
            "paired_gti_file": "test_fixture_gti.bin",
            "pairing_verified": "yes",
        },
    ])

    df = load_manifest(manifest_file)
    report = verify_manifest_against_disk(df, raw_dir)

    assert report["error_count"] == 0
    assert len(report["valid_files"]) == 2
    assert len(report["missing_on_disk"]) == 0
    assert len(report["untracked_on_disk"]) == 0


def test_verify_manifest_missing_file_on_disk(tmp_path):
    """Verify detection of file listed in manifest but absent on disk."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    manifest_file = tmp_path / "manifest.csv"
    _create_csv_manifest(manifest_file, [{
        "file_name": "test_fixture_missing.bin",
        "file_type": "LIGHTCURVE",
        "sha256": "dummyhash",
        "paired_gti_file": "none",
        "pairing_verified": "yes",
    }])

    df = load_manifest(manifest_file)
    report = verify_manifest_against_disk(df, raw_dir)

    assert report["error_count"] > 0
    assert "test_fixture_missing.bin" in report["missing_on_disk"]


def test_verify_manifest_untracked_file_on_disk(tmp_path):
    """Verify detection of unexpected untracked file on disk."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    untracked = raw_dir / "test_fixture_untracked.bin"
    untracked.write_bytes(b"Untracked file")

    manifest_file = tmp_path / "manifest.csv"
    _create_csv_manifest(manifest_file, [])

    df = load_manifest(manifest_file)
    report = verify_manifest_against_disk(df, raw_dir)

    assert report["error_count"] > 0
    assert any("test_fixture_untracked.bin" in f for f in report["untracked_on_disk"])


def test_verify_manifest_checksum_mismatch(tmp_path):
    """Verify detection of SHA-256 hash discrepancy."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    disk_file = raw_dir / "test_fixture_mismatch.bin"
    disk_file.write_bytes(b"Content-A")

    manifest_file = tmp_path / "manifest.csv"
    _create_csv_manifest(manifest_file, [{
        "file_name": "test_fixture_mismatch.bin",
        "file_type": "GTI",
        "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
        "paired_gti_file": "test_fixture_mismatch.bin",
        "pairing_verified": "yes",
    }])

    df = load_manifest(manifest_file)
    report = verify_manifest_against_disk(df, raw_dir)

    assert report["error_count"] > 0
    assert len(report["checksum_mismatches"]) == 1
    assert report["checksum_mismatches"][0]["file_name"] == "test_fixture_mismatch.bin"


def test_verify_manifest_unpaired_lightcurve(tmp_path):
    """Verify error flag when LIGHTCURVE lacks valid paired GTI."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    disk_file = raw_dir / "test_fixture_lone_lc.bin"
    disk_file.write_bytes(b"Content")
    h = hashlib.sha256(b"Content").hexdigest()

    manifest_file = tmp_path / "manifest.csv"
    _create_csv_manifest(manifest_file, [{
        "file_name": "test_fixture_lone_lc.bin",
        "file_type": "LIGHTCURVE",
        "sha256": h,
        "paired_gti_file": "",  # Missing pairing
        "pairing_verified": "no",
    }])

    df = load_manifest(manifest_file)
    report = verify_manifest_against_disk(df, raw_dir)

    assert report["error_count"] > 0
    assert len(report["unpaired_entries"]) == 1


def test_verify_manifest_unverified_pairing_warning(tmp_path):
    """Verify pairing_verified != 'yes' registers as warning without incrementing errors."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    lc = raw_dir / "test_fixture_lc.bin"
    gti = raw_dir / "test_fixture_gti.bin"
    lc.write_bytes(b"LC")
    gti.write_bytes(b"GTI")

    manifest_file = tmp_path / "manifest.csv"
    _create_csv_manifest(manifest_file, [
        {
            "file_name": "test_fixture_lc.bin",
            "file_type": "LIGHTCURVE",
            "sha256": hashlib.sha256(b"LC").hexdigest(),
            "paired_gti_file": "test_fixture_gti.bin",
            "pairing_verified": "no",  # Warning condition
        },
        {
            "file_name": "test_fixture_gti.bin",
            "file_type": "GTI",
            "sha256": hashlib.sha256(b"GTI").hexdigest(),
            "paired_gti_file": "test_fixture_gti.bin",
            "pairing_verified": "yes",
        },
    ])

    df = load_manifest(manifest_file)
    report = verify_manifest_against_disk(df, raw_dir)

    assert report["error_count"] == 0
    assert report["warning_count"] > 0
    assert len(report["unverified_pairings"]) == 1


def test_cli_exit_codes(tmp_path, monkeypatch):
    """Verify check_manifest CLI returns 0 on clean, 1 on errors, 2 on malformed manifest."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    # Case 2: Missing / malformed manifest -> exit 2
    monkeypatch.setattr("sys.argv", ["check_manifest.py", str(tmp_path / "missing.csv")])
    assert cli_main() == 2

    # Case 1: Manifest with missing files -> exit 1
    err_manifest = tmp_path / "err_manifest.csv"
    _create_csv_manifest(err_manifest, [{
        "file_name": "non_existent_file.bin",
        "file_type": "GTI",
        "sha256": "dummy",
        "paired_gti_file": "N/A",
        "pairing_verified": "yes",
    }])
    monkeypatch.setattr("sys.argv", [
        "check_manifest.py", str(err_manifest), "--raw-dir", str(raw_dir)
    ])
    assert cli_main() == 1

    # Case 0: Clean manifest -> exit 0
    clean_manifest = tmp_path / "clean_manifest.csv"
    dummy_disk = raw_dir / "test_fixture_clean.bin"
    dummy_disk.write_bytes(b"Clean-Disk-Data")
    h = hashlib.sha256(b"Clean-Disk-Data").hexdigest()

    _create_csv_manifest(clean_manifest, [{
        "file_name": "test_fixture_clean.bin",
        "file_type": "GTI",
        "sha256": h,
        "paired_gti_file": "test_fixture_clean.bin",
        "pairing_verified": "yes",
    }])
    monkeypatch.setattr("sys.argv", [
        "check_manifest.py", str(clean_manifest), "--raw-dir", str(raw_dir)
    ])
    assert cli_main() == 0
