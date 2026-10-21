"""Command-line verification tool for SOLARIS-A1 data manifests.

Validates a data manifest against physical files stored in data/raw/.
Exit codes:
    0: Verification passed with 0 errors (warnings may be present).
    1: Validation errors detected (missing files, untracked files, hash mismatches, unpaired products).
    2: Manifest is malformed, missing required columns, or not found.
"""

import argparse
from pathlib import Path
import sys

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from solar_flare.manifest import (
    load_manifest,
    verify_manifest_against_disk,
    ManifestError,
)
from solar_flare.paths import get_raw_dir


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Verify SOLARIS-A1 data manifest against raw directory on disk."
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        default="data/manifests/manifest.csv",
        help="Path to manifest CSV file (default: data/manifests/manifest.csv).",
    )
    parser.add_argument(
        "--raw-dir",
        default=None,
        help="Path to raw files directory (default: data/raw).",
    )
    return parser


def main() -> int:
    """Execute manifest check and return appropriate exit code."""
    parser = build_parser()
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = _REPO_ROOT / manifest_path

    raw_dir = Path(args.raw_dir) if args.raw_dir else get_raw_dir()
    if not raw_dir.is_absolute():
        raw_dir = _REPO_ROOT / raw_dir

    print("=" * 70)
    print("SOLARIS-A1 MANIFEST INTEGRITY CHECK")
    print("=" * 70)
    print(f"Manifest Path : {manifest_path}")
    print(f"Raw Directory : {raw_dir}")
    print("-" * 70)

    # 1. Load and validate manifest schema
    try:
        manifest_df = load_manifest(manifest_path)
    except FileNotFoundError:
        print(f"\n[ERROR - EXIT 2] Manifest file not found: {manifest_path}")
        print("Tip: If you have not created manifest.csv yet, copy manifest_template.csv to get started.")
        return 2
    except ManifestError as exc:
        print(f"\n[ERROR - EXIT 2] Malformed or invalid manifest: {exc}")
        return 2
    except Exception as exc:
        print(f"\n[ERROR - EXIT 2] Unexpected error loading manifest: {exc}")
        return 2

    # 2. Verify against disk
    report = verify_manifest_against_disk(manifest_df, raw_dir)

    total_records = len(manifest_df)
    valid_count = len(report["valid_files"])
    errors = report["error_count"]
    warnings = report["warning_count"]

    # Print warnings
    if report["example_rows"]:
        print("\n[WARNING] Template / Example rows detected (must be deleted before Stage 3):")
        for ex in report["example_rows"]:
            print(f"    - {ex}")

    if report["unverified_pairings"]:
        print("\n[WARNING] Unverified light-curve / GTI pairings (pairing_verified != 'yes'):")
        for unv in report["unverified_pairings"]:
            print(f"    - {unv['file_name']}: status='{unv['status']}'")

    # Print errors
    if report["missing_on_disk"]:
        print("\n[ERROR] Files listed in manifest but MISSING on disk:")
        for miss in report["missing_on_disk"]:
            print(f"    - {miss}")

    if report["untracked_on_disk"]:
        print("\n[ERROR] Files found on disk but NOT recorded in manifest:")
        for untracked in report["untracked_on_disk"]:
            print(f"    - {untracked}")

    if report["checksum_mismatches"]:
        print("\n[ERROR] SHA-256 Checksum mismatches detected:")
        for mm in report["checksum_mismatches"]:
            print(f"    - {mm['file_name']}:")
            print(f"        Expected: {mm['expected']}")
            print(f"        Actual  : {mm['actual']}")

    if report["unpaired_entries"]:
        print("\n[ERROR] Unpaired or invalid GTI references:")
        for unp in report["unpaired_entries"]:
            print(f"    - {unp['file_name']}: {unp['reason']}")

    if report["checksum_errors"]:
        print("\n[ERROR] Files that could not be read for hash calculation:")
        for ce in report["checksum_errors"]:
            print(f"    - {ce['file_name']}: {ce['error']}")

    # Print summary
    print("\n" + "=" * 70)
    print(f"SUMMARY: {total_records} manifest records | {valid_count} verified files on disk")
    print(f"Errors   : {errors}")
    print(f"Warnings : {warnings}")
    print("=" * 70)

    if errors > 0:
        print("[FAIL] Manifest check finished with errors. Exit code: 1")
        return 1

    print("[SUCCESS] Manifest check passed with zero errors. Exit code: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
