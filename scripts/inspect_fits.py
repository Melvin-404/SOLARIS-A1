"""CLI tool to inspect SoLEXS FITS files and produce detailed inventory reports.

Generates:
1. results/inventory/inventory.csv & inventory.json
2. results/inventory/inspection_report.md
3. results/inventory/open_questions.md

Guarantees read-only access and verifies SHA-256 hashes before and after inspection.
"""

import argparse
from pathlib import Path
import sys
from typing import Any, Dict, List

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from solar_flare.manifest import (
    load_manifest,
    compute_sha256,
    find_file_in_dir,
)
from solar_flare.paths import get_raw_dir, get_results_dir
from solar_flare.inspection.fits_inspect import (
    list_hdus,
    describe_columns,
    summarise_time_columns,
    summarise_numeric_columns,
    read_header_dict,
)
from solar_flare.inspection.time_systems import extract_time_system_metadata
from solar_flare.inspection.inventory import build_inventory


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Inspect SoLEXS FITS files and generate metadata inventory."
    )
    parser.add_argument(
        "--raw-dir",
        default=None,
        help="Path to raw FITS directory (default: data/raw).",
    )
    parser.add_argument(
        "--manifest",
        default="data/manifests/manifest.csv",
        help="Path to manifest CSV (default: data/manifests/manifest.csv).",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Path to output directory (default: results/inventory).",
    )
    return parser


def generate_inspection_report(
    files_to_inspect: List[Path],
    out_file: Path,
) -> int:
    """Generate detailed markdown report per file.

    Returns:
        int: Number of unresolved questions identified.
    """
    lines: List[str] = [
        "# SOLARIS-A1: FITS Metadata Inspection Report",
        "",
        "> **Note:** All observed values in this report are extracted directly from FITS headers and tables. "
        "Any interpretations are explicitly marked as candidate interpretations and require student review.",
        "",
        "---",
        "",
    ]

    for fpath in files_to_inspect:
        lines.append(f"## File: `{fpath.name}`")
        lines.append(f"- **File Path:** `{fpath}`")
        lines.append(f"- **Size:** {fpath.stat().st_size:,} bytes")
        lines.append("")

        # 1. HDU Table
        hdus = list_hdus(fpath)
        lines.append("### HDU Structure")
        lines.append("| Index | Name | Ver | Type | Shape | Rows | Columns |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for h in hdus:
            lines.append(
                f"| {h['index']} | `{h['name']}` | {h['ver']} | {h['type']} | {h['shape']} | {h['rows']:,} | {h['columns_count']} |"
            )
        lines.append("")

        # 2. Time Systems
        time_meta = extract_time_system_metadata(fpath)
        lines.append("### Observed Time-System Keywords")
        ckw = time_meta["consolidated_keywords"]
        if ckw:
            lines.append("| Keyword | Observed Value | Description / Context |")
            lines.append("| :--- | :--- | :--- |")
            for k, v in ckw.items():
                lines.append(f"| `{k}` | `{v}` | Extracted from FITS header |")
        else:
            lines.append("*No standard time keywords observed.*")
        lines.append("")

        if time_meta["candidate_interpretations"]:
            lines.append("#### Candidate Time Interpretations")
            for interp in time_meta["candidate_interpretations"]:
                lines.append(f"- {interp}")
            lines.append("")

        # 3. Table Column Details & Numerical Summaries
        for h in hdus:
            if h["columns_count"] > 0:
                lines.append(f"### Extension `{h['name']}` (HDU {h['index']}) Columns")
                cols = describe_columns(fpath, hdu=h["index"])
                lines.append("| Column Name | Format | Unit | Dimension |")
                lines.append("| :--- | :--- | :--- | :--- |")
                for c in cols:
                    unit_str = f"`{c['unit']}`" if c['unit'] else "*None recorded*"
                    lines.append(f"| `{c['name']}` | `{c['format']}` | {unit_str} | {c['dim']} |")
                lines.append("")

                # Numeric summaries
                num_sums = summarise_numeric_columns(fpath, hdu=h["index"])
                if num_sums:
                    lines.append("#### Column Statistics")
                    lines.append("| Column | Rows | NaN Count | Inf Count | Min | Max | Mean | Median |")
                    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
                    for cname, stats in num_sums.items():
                        c_min = f"{stats['min']:.4g}" if stats['min'] is not None else "None"
                        c_max = f"{stats['max']:.4g}" if stats['max'] is not None else "None"
                        c_mean = f"{stats['mean']:.4g}" if stats['mean'] is not None else "None"
                        c_med = f"{stats['median']:.4g}" if stats['median'] is not None else "None"
                        lines.append(
                            f"| `{cname}` | {stats['count']:,} | {stats['nan_count']:,} | {stats['inf_count']:,} | {c_min} | {c_max} | {c_mean} | {c_med} |"
                        )
                    lines.append("")

                # Time column summaries
                time_sums = summarise_time_columns(fpath, hdu=h["index"])
                if time_sums:
                    lines.append("#### Time Column Diagnostics")
                    lines.append("| Column | Valid Pts | Min | Max | Median Spacing | Monotonic? | Unique Count |")
                    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
                    for ts in time_sums:
                        t_min = f"{ts['min']:.4g}" if ts['min'] is not None else "None"
                        t_max = f"{ts['max']:.4g}" if ts['max'] is not None else "None"
                        t_sp = f"{ts['median_spacing']:.4g} s" if ts['median_spacing'] is not None else "None"
                        lines.append(
                            f"| `{ts['column_name']}` | {ts['valid_count']:,} | {t_min} | {t_max} | {t_sp} | {ts['is_monotonic']} | {ts['unique_count']:,} |"
                        )
                    lines.append("")

        lines.append("---")
        lines.append("")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(lines), encoding="utf-8")
    return len(files_to_inspect)


def generate_open_questions(
    files_to_inspect: List[Path],
    manifest_df: Any,
    out_file: Path,
) -> int:
    """Generate comprehensive list of open questions and unresolved items.

    Returns:
        int: Total number of unresolved items.
    """
    questions: List[Dict[str, str]] = []

    for fpath in files_to_inspect:
        hdus = list_hdus(fpath)
        time_meta = extract_time_system_metadata(fpath)

        for q in time_meta.get("unresolved_questions", []):
            questions.append({"file": fpath.name, "category": "Time System", "question": q})

        for h in hdus:
            if h["columns_count"] > 0:
                cols = describe_columns(fpath, hdu=h["index"])
                for c in cols:
                    if not c["unit"]:
                        questions.append({
                            "file": fpath.name,
                            "category": "Missing Physical Unit",
                            "question": f"Column `{c['name']}` in `{h['name']}` has no recorded unit keyword (TUNIT). Confirm whether counts, count rate (c/s), or flux.",
                        })

                # Check for empty tables
                if h["rows"] == 0:
                    questions.append({
                        "file": fpath.name,
                        "category": "Zero Rows Table",
                        "question": f"Extension `{h['name']}` has 0 rows. Verify detector status (e.g., SDD1 vs SDD2 operational state).",
                    })

    # Lightcurve vs GTI check from manifest
    for _, row in manifest_df.iterrows():
        fname = row.get("file_name", "")
        ftype = row.get("file_type", "")
        if ftype == "LIGHTCURVE":
            paired = row.get("paired_gti_file", "")
            if not paired or row.get("pairing_verified", "").lower() != "yes":
                questions.append({
                    "file": fname,
                    "category": "Pairing",
                    "question": f"LIGHTCURVE `{fname}` does not have a verified paired GTI file in the manifest.",
                })

    lines: List[str] = [
        "# SOLARIS-A1: Unresolved Questions and Observation Anomalies",
        "",
        "This document lists all ambiguous roles, missing units, time-system questions, and observational anomalies",
        "identified during the automated Stage 3 inspection. Each item requires review by the student researcher",
        "against official SoLEXS instrument manuals before Stage 4 validation.",
        "",
        f"**Total Unresolved Items Identified:** {len(questions)}",
        "",
        "---",
        "",
        "| File | Category | Unresolved Question / Action Required |",
        "| :--- | :--- | :--- |",
    ]

    for q in questions:
        lines.append(f"| `{q['file']}` | {q['category']} | {q['question']} |")

    lines.append("")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(lines), encoding="utf-8")
    return len(questions)


def main() -> int:
    """Execute FITS metadata inspection pipeline."""
    parser = build_parser()
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir) if args.raw_dir else get_raw_dir()
    if not raw_dir.is_absolute():
        raw_dir = _REPO_ROOT / raw_dir

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = _REPO_ROOT / manifest_path

    out_dir = Path(args.out_dir) if args.out_dir else (get_results_dir(create=True) / "inventory")
    if not out_dir.is_absolute():
        out_dir = _REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("SOLARIS-A1 FITS DATA INVENTORY & METADATA INSPECTION (Stage 3)")
    print("=" * 70)
    print(f"Raw Directory  : {raw_dir}")
    print(f"Manifest Path  : {manifest_path}")
    print(f"Output Directory: {out_dir}")
    print("-" * 70)

    # 1. Load manifest
    manifest_df = load_manifest(manifest_path)
    print(f"Loaded {len(manifest_df)} records from manifest.")

    # 2. Record initial SHA-256 hashes to guarantee immutability
    print("\n[Step 1] Recording pre-inspection SHA-256 hashes...")
    pre_hashes: Dict[str, str] = {}
    files_to_inspect: List[Path] = []

    for _, row in manifest_df.iterrows():
        fname = row.get("file_name", "")
        if not fname or "EXAMPLE" in fname.upper():
            continue
        disk_file = find_file_in_dir(fname, raw_dir)
        if disk_file:
            h = compute_sha256(disk_file)
            pre_hashes[fname] = h
            files_to_inspect.append(disk_file)
            print(f"  [FOUND] {fname} ({disk_file.stat().st_size:,} bytes) -> {h[:16]}...")
        else:
            print(f"  [MISSING] {fname} not found in {raw_dir}")

    if not files_to_inspect:
        print("\n[ERROR] No FITS files found on disk to inspect.")
        return 1

    # 3. Build tabular inventory
    print("\n[Step 2] Building dataset inventory...")
    inv_df = build_inventory(raw_dir, manifest_df, out_dir=out_dir)
    print(f"  Saved: {out_dir / 'inventory.csv'}")
    print(f"  Saved: {out_dir / 'inventory.json'}")

    # 4. Generate inspection report
    print("\n[Step 3] Generating detailed inspection report...")
    report_file = out_dir / "inspection_report.md"
    generate_inspection_report(files_to_inspect, report_file)
    print(f"  Saved: {report_file}")

    # 5. Generate open questions
    print("\n[Step 4] Generating open questions register...")
    questions_file = out_dir / "open_questions.md"
    num_questions = generate_open_questions(files_to_inspect, manifest_df, questions_file)
    print(f"  Saved: {questions_file}")
    print(f"  Unresolved questions identified: {num_questions}")

    # 6. Verify SHA-256 hashes after inspection to guarantee immutability
    print("\n[Step 5] Verifying post-inspection SHA-256 hashes (Immutability Check)...")
    hash_mismatches = 0
    for fpath in files_to_inspect:
        post_h = compute_sha256(fpath)
        pre_h = pre_hashes[fpath.name]
        if post_h != pre_h:
            print(f"  [ALERT MUTATION] Hash mismatch for {fpath.name}!")
            hash_mismatches += 1
        else:
            print(f"  [VERIFIED UNCHANGED] {fpath.name}")

    print("\n" + "=" * 70)
    if hash_mismatches > 0:
        print(f"[FATAL ERROR] {hash_mismatches} files were modified during inspection!")
        return 1

    print("STAGE 3 INSPECTION COMPLETE: All files verified strictly unchanged.")
    print(f"Reports available in: {out_dir}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
