"""Manifest loading, cryptographic verification, and disk validation for SOLARIS-A1.

Provides functionality to parse provenance manifests, compute streaming SHA-256
hashes, and verify that records in the manifest match physical files on disk
without modifying any files.
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import pandas as pd

REQUIRED_MANIFEST_COLUMNS: List[str] = [
    "file_name",
    "file_type",
    "observation_id",
    "start_time_as_displayed",
    "end_time_as_displayed",
    "time_system_as_displayed",
    "portal_url",
    "product_label_as_displayed",
    "download_date",
    "sha256",
    "file_size_bytes",
    "paired_gti_file",
    "pairing_verified",
    "notes",
]

ALLOWED_FILE_TYPES: Set[str] = {"LIGHTCURVE", "GTI", "OTHER"}
IGNORED_DISK_NAMES: Set[str] = {"README.md", ".gitignore", ".gitkeep"}


class ManifestError(ValueError):
    """Raised when a manifest file is missing, unreadable, or malformed."""
    pass


def load_manifest(path: Path | str) -> pd.DataFrame:
    """Load a CSV manifest file and validate its required schema.

    Args:
        path: Path to the CSV manifest file.

    Returns:
        pd.DataFrame: Validated manifest DataFrame with string dtypes.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        ManifestError: If the CSV is empty, malformed, or missing required columns.
    """
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    try:
        # Read all columns as string to prevent numeric coercion of IDs or timestamps
        df = pd.read_csv(
            manifest_path,
            dtype=str,
            keep_default_na=False,
            skipinitialspace=True,
        )
    except Exception as exc:
        raise ManifestError(f"Failed to parse manifest CSV '{manifest_path}': {exc}") from exc

    if df.empty and len(df.columns) == 0:
        raise ManifestError(f"Manifest '{manifest_path}' is completely empty.")

    # Check for missing required columns
    missing_cols = [c for c in REQUIRED_MANIFEST_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ManifestError(
            f"Manifest '{manifest_path}' is missing required columns: {missing_cols}"
        )

    # Clean whitespace from column strings
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()

    return df


def compute_sha256(path: Path | str, chunk_size: int = 65536) -> str:
    """Compute the SHA-256 cryptographic hash of a file streaming in chunks.

    Does not load the entire file into memory, ensuring safe processing of large FITS files.

    Args:
        path: Path to the target file.
        chunk_size: Byte size of chunks read per iteration. Defaults to 64KB.

    Returns:
        str: Lowercase 64-character hexadecimal SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If an error occurs reading the file.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found for hash calculation: {file_path}")

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)

    return hasher.hexdigest().lower()


def find_file_in_dir(filename: str, search_dir: Path) -> Optional[Path]:
    """Locate a filename within a directory or its immediate subdirectories.

    Args:
        filename: Filename to search for.
        search_dir: Root directory to search within.

    Returns:
        Optional[Path]: Absolute path to the file if found, else None.
    """
    direct_match = search_dir / filename
    if direct_match.is_file():
        return direct_match

    # Search in immediate subdirectories (e.g., data/raw/gti/)
    for item in search_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            sub_match = item / filename
            if sub_match.is_file():
                return sub_match

    return None


def verify_manifest_against_disk(
    manifest_df: pd.DataFrame,
    raw_dir: Path | str,
) -> Dict[str, Any]:
    """Verify manifest entries against physical files on disk without modifying any files.

    Checks:
    1. Files listed in the manifest but missing on disk.
    2. Files present on disk in raw_dir but not indexed in the manifest.
    3. Checksum (SHA-256) mismatches between manifest records and disk files.
    4. Unpaired LIGHTCURVE or GTI files.
    5. Rows where pairing_verified is not 'yes'.
    6. Presence of template/example rows.

    Args:
        manifest_df: Parsed manifest DataFrame.
        raw_dir: Directory containing raw downloaded files.

    Returns:
        Dict[str, Any]: Detailed verification report dictionary.
    """
    raw_path = Path(raw_dir)
    report: Dict[str, Any] = {
        "missing_on_disk": [],
        "untracked_on_disk": [],
        "checksum_mismatches": [],
        "checksum_errors": [],
        "unpaired_entries": [],
        "unverified_pairings": [],
        "example_rows": [],
        "valid_files": [],
        "error_count": 0,
        "warning_count": 0,
    }

    # Set of all manifest files (normalized filenames)
    manifest_files: Set[str] = set()
    manifest_by_name: Dict[str, Dict[str, Any]] = {}

    for _, row in manifest_df.iterrows():
        fname = row["file_name"]
        if not fname:
            continue

        # Check for placeholder / example rows
        if "EXAMPLE" in fname.upper() or "DELETE" in fname.upper():
            report["example_rows"].append(fname)
            report["warning_count"] += 1

        manifest_files.add(fname)
        manifest_by_name[fname] = row.to_dict()

    # 1. Check each manifest entry against disk
    for fname, row in manifest_by_name.items():
        disk_file = find_file_in_dir(fname, raw_path)
        if disk_file is None:
            report["missing_on_disk"].append(fname)
            report["error_count"] += 1
            continue

        # Verify checksum if sha256 is recorded
        expected_sha = row.get("sha256", "").strip().lower()
        if expected_sha and "EXAMPLE" not in expected_sha.upper():
            try:
                actual_sha = compute_sha256(disk_file)
                if actual_sha != expected_sha:
                    report["checksum_mismatches"].append({
                        "file_name": fname,
                        "path": str(disk_file),
                        "expected": expected_sha,
                        "actual": actual_sha,
                    })
                    report["error_count"] += 1
                else:
                    report["valid_files"].append(fname)
            except Exception as exc:
                report["checksum_errors"].append({
                    "file_name": fname,
                    "error": str(exc),
                })
                report["error_count"] += 1

        # 2. Check pairing rules
        ftype = row.get("file_type", "").strip().upper()
        paired_gti = row.get("paired_gti_file", "").strip()
        pairing_verified = row.get("pairing_verified", "").strip().lower()

        if ftype == "LIGHTCURVE":
            if not paired_gti or paired_gti.upper() in ("NONE", "N/A", "EXAMPLE — DELETE", ""):
                report["unpaired_entries"].append({
                    "file_name": fname,
                    "reason": "LIGHTCURVE has no paired_gti_file specified",
                })
                report["error_count"] += 1
            elif paired_gti not in manifest_files:
                report["unpaired_entries"].append({
                    "file_name": fname,
                    "reason": f"paired_gti_file '{paired_gti}' is not recorded in manifest",
                })
                report["error_count"] += 1

        if pairing_verified != "yes":
            report["unverified_pairings"].append({
                "file_name": fname,
                "status": row.get("pairing_verified", "unspecified"),
            })
            report["warning_count"] += 1

    # 3. Find files on disk not tracked in manifest
    if raw_path.is_dir():
        for item in raw_path.rglob("*"):
            if item.is_file():
                if item.name in IGNORED_DISK_NAMES or item.name.startswith("."):
                    continue
                if item.name not in manifest_files and item.relative_to(raw_path).as_posix() not in manifest_files:
                    report["untracked_on_disk"].append(str(item.relative_to(raw_path)))
                    report["error_count"] += 1

    return report
