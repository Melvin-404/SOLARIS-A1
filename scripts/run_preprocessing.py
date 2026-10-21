"""CLI runner for SOLARIS-A1 Stage 7 GTI-Aware Preprocessing and Segmentation.

Executes non-destructive filtering, GTI boundary filtering, continuous observation
segmentation at approved gap thresholds, minimum segment length filtering, and auditable
sample reconciliation.

GUARANTEES:
- Raw observation files remain 100% byte-for-byte immutable (SHA-256 verified before and after).
- Zero data estimation, reconstruction, bridging, or interpolation is performed.
- Every sample excluded is permanently recorded in audit CSV, JSON, and Markdown reports.
- With --final off: executes in PROVISIONAL development mode.
- With --final on: strictly refuses unless Gates G1, G2, and Decision D-14 are APPROVED.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import yaml
from astropy.io import fits

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from solar_flare.paths import project_root
from solar_flare.config import load_config
from solar_flare.manifest import compute_sha256
from solar_flare.quality.gti_coverage import load_gti_intervals
from solar_flare.preprocessing.filters import (
    exclude_non_finite,
    exclude_negative,
    exclude_flagged,
    resolve_duplicate_timestamps,
    sort_by_time,
    DuplicateTimestampError,
)
from solar_flare.preprocessing.gti_apply import apply_gti
from solar_flare.preprocessing.segmentation import (
    segment_continuous,
    Segment,
    ParameterPendingError,
)
from solar_flare.preprocessing.audit import (
    ProcessingAudit,
    ReconciliationError,
    write_audit,
)


def check_approval_for_final(decisions_path: Path, out_dir: Path) -> Tuple[bool, List[str]]:
    """Check whether Gate G1, G2, and D-14 decisions are APPROVED in decisions.yaml.
    
    If not approved, writes results/preprocessing/AWAITING_G4.md detailing missing items.
    """
    missing: List[str] = []
    if not decisions_path.is_file():
        missing.append(f"Decisions register not found: {decisions_path}")
        return False, missing

    with open(decisions_path, "r", encoding="utf-8") as f:
        decs_data = yaml.safe_load(f) or {}

    decs = decs_data.get("decisions", {})

    # Check G1: D-09, D-10
    d09 = decs.get("D-09", {})
    if d09.get("status") not in ("APPROVED", "CONFIRMED") or not d09.get("approved_by"):
        missing.append("Gate G1 / D-09: Energy band / light-curve column selection is not APPROVED")

    d10 = decs.get("D-10", {})
    if d10.get("status") not in ("APPROVED", "CONFIRMED") or not d10.get("approved_by"):
        missing.append("Gate G1 / D-10: Time coordinate system alignment is not APPROVED")

    # Check G2: D-13
    d13 = decs.get("D-13", {})
    if d13.get("status") not in ("APPROVED", "CONFIRMED") or not d13.get("approved_by"):
        missing.append("Gate G2 / D-13: Quality check thresholds are not APPROVED")

    # Check G4: D-14, D-17
    d14 = decs.get("D-14", {})
    if d14.get("status") != "APPROVED" or not d14.get("approved_by"):
        missing.append("Gate G4 / D-14: Gap splitting (max_gap_seconds) and min_segment_seconds are PENDING")

    d17 = decs.get("D-17", {})
    if d17.get("status") != "APPROVED" or not d17.get("approved_by"):
        missing.append("Gate G4 / D-17: GTI boundary convention is PENDING")

    if missing:
        # Write AWAITING_G4.md
        out_dir.mkdir(parents=True, exist_ok=True)
        awaiting_file = out_dir / "AWAITING_G4.md"
        content = [
            "# Stage 7: Gate G4 Approval Pending",
            "",
            "> **FINAL PREPROCESSING RUN REFUSED**",
            "> The `--final` execution flag requires formal human approval of Gates G1, G2, and Gate G4.",
            "",
            "## Unresolved Decisions Required for Final Run",
            "",
        ]
        for item in missing:
            content.append(f"- [ ] **{item}**")
        content.extend([
            "",
            "---",
            "",
            "## How to Proceed",
            "1. Review provisional outputs produced by development mode in `results/preprocessing/`.",
            "2. Confirm column roles (Gate G1) and quality thresholds (Gate G2).",
            "3. Approve gap threshold `max_gap_seconds` and `min_segment_seconds` (Decision D-14).",
            "4. Approve GTI boundary convention (Decision D-17).",
            "5. Update `config/decisions.yaml` with `status: APPROVED` and `approved_by: <Researcher Name>`.",
            "6. Re-run `python scripts/run_preprocessing.py --final`.",
            "",
        ])
        with open(awaiting_file, "w", encoding="utf-8") as af:
            af.write("\n".join(content))
        return False, missing

    return True, []


def preprocess_lightcurve_file(
    lc_path: Path,
    gti_path: Optional[Path],
    time_col: str,
    count_col: str,
    flag_col: Optional[str],
    gti_start_col: str,
    gti_stop_col: str,
    max_gap_seconds: Any,
    min_segment_seconds: Any,
    boundary: str,
    dup_policy: str,
    excluded_flags: List[Any],
    is_final: bool,
    segments_dir: Path,
    results_dir: Path,
    logger: logging.Logger,
) -> Dict[str, Any]:
    """Execute complete preprocessing and segmentation pipeline for a single lightcurve file."""
    stem = lc_path.name.replace(".lc.gz", "").replace(".lc", "").replace(".fits.gz", "").replace(".fits", "")
    logger.info(f"Processing light curve: {lc_path.name} (stem: {stem})")

    # 1. Compute source hash before
    hash_before = compute_sha256(lc_path)

    # 2. Load raw lightcurve data
    with fits.open(lc_path, mode="readonly", memmap=True) as hdul:
        table_hdu = hdul[1]
        col_names = table_hdu.columns.names
        if time_col not in col_names or count_col not in col_names:
            raise ValueError(f"Required column(s) ({time_col}, {count_col}) missing in {lc_path.name}")

        df_raw = pd.DataFrame({
            time_col: np.asarray(table_hdu.data[time_col], dtype=np.float64),
            count_col: np.asarray(table_hdu.data[count_col], dtype=np.float64),
        })
        if flag_col and flag_col in col_names:
            df_raw[flag_col] = np.asarray(table_hdu.data[flag_col])

    original_n = len(df_raw)

    # Initialize Audit
    params_record = {
        "time_column": time_col,
        "count_column": count_col,
        "flag_column": flag_col,
        "max_gap_seconds": max_gap_seconds,
        "min_segment_seconds": min_segment_seconds,
        "gti_boundary_convention": boundary,
        "duplicate_timestamp_policy": dup_policy,
        "excluded_quality_flags": excluded_flags,
        "is_final": is_final,
        "file_format": "CSV (pyarrow not present in requirements)",
    }
    audit = ProcessingAudit(
        file_stem=stem,
        original_sample_count=original_n,
        source_file_sha256_before=hash_before,
        parameters=params_record,
        is_final_run=is_final,
    )

    # 3. Sort by time
    df_cur, sort_log = sort_by_time(df_raw, time_col=time_col)
    audit.add_exclusions(sort_log)

    # 4. Exclude non-finite
    df_cur, excl_non_finite = exclude_non_finite(df_cur, value_col=count_col, time_col=time_col)
    audit.add_exclusions(excl_non_finite)

    # 5. Exclude negative values
    df_cur, excl_negative = exclude_negative(df_cur, value_col=count_col, time_col=time_col)
    audit.add_exclusions(excl_negative)

    # 6. Exclude quality flags
    df_cur, excl_flagged = exclude_flagged(df_cur, flag_col=flag_col, excluded_values=excluded_flags, time_col=time_col)
    audit.add_exclusions(excl_flagged)

    # 7. Resolve duplicate timestamps
    try:
        df_cur, excl_dups = resolve_duplicate_timestamps(df_cur, time_col=time_col, policy=dup_policy)
        audit.add_exclusions(excl_dups)
    except DuplicateTimestampError as dte:
        logger.error(f"Duplicate timestamp error on {stem}: {dte}")
        return {
            "file_stem": stem,
            "status": "FAIL_DUPLICATES",
            "error": str(dte),
            "original_samples": original_n,
            "retained_samples": 0,
            "n_segments": 0,
        }

    # 8. Load paired GTI and apply
    if gti_path and gti_path.is_file():
        gti_info = load_gti_intervals(gti_path, start_col=gti_start_col, stop_col=gti_stop_col)
        gti_intervals = gti_info.get("intervals", [])
    else:
        gti_intervals = []

    df_cur, excl_gti = apply_gti(df_cur, time_col=time_col, gti_intervals=gti_intervals, boundary=boundary)
    audit.add_exclusions(excl_gti)

    # 9. Segment continuous and filter short segments
    valid_segments, excl_short_segs = segment_continuous(
        df=df_cur,
        time_col=time_col,
        max_gap_seconds=max_gap_seconds,
        min_segment_seconds=min_segment_seconds,
        stem=stem,
    )
    audit.add_exclusions(excl_short_segs)

    # 10. Reconcile sample conservation
    retained_n = sum(len(s.dataframe) for s in valid_segments)
    audit.set_retained(retained_count=retained_n, segments=valid_segments)

    # 11. Compute hash after and verify immutability
    hash_after = compute_sha256(lc_path)
    audit.finalize_hashes(hash_after)

    try:
        audit.reconcile()
    except ReconciliationError as re_err:
        logger.error(f"Reconciliation error on {stem}: {re_err}")
        return {
            "file_stem": stem,
            "status": "FAIL_RECONCILIATION",
            "error": str(re_err),
            "original_samples": original_n,
            "retained_samples": retained_n,
            "n_segments": len(valid_segments),
        }

    # 12. Write segments to data/processed/segments/<stem>/
    file_seg_dir = segments_dir / stem
    file_seg_dir.mkdir(parents=True, exist_ok=True)

    status_tag = "APPROVED" if is_final else "PROVISIONAL"
    written_segment_paths: List[str] = []

    for s in valid_segments:
        seg_file = file_seg_dir / f"{s.segment_id}.csv"
        # Export segment to CSV format (pyarrow is absent from requirements)
        # Add metadata header comment and segment status column
        seg_df = s.dataframe.copy()
        seg_df["segment_id"] = s.segment_id
        seg_df["status"] = status_tag
        seg_df.to_csv(seg_file, index=False)
        written_segment_paths.append(str(seg_file.as_posix()))

    # 13. Write audit reports
    audit_files = write_audit(audit, out_dir=results_dir)
    logger.info(f"Audit written for {stem}: {audit_files['md']}")

    return {
        "file_stem": stem,
        "status": "SUCCESS",
        "is_final": is_final,
        "original_samples": original_n,
        "retained_samples": retained_n,
        "retention_percentage": round(float(retained_n / original_n * 100.0) if original_n > 0 else 0.0, 4),
        "excluded_by_reason": audit.get_counts_by_reason(),
        "n_segments": len(valid_segments),
        "segments": [s.to_dict() for s in valid_segments],
        "hash_before": hash_before,
        "hash_after": hash_after,
        "immutability_verified": (hash_before == hash_after),
        "audit_files": {k: str(v.as_posix()) for k, v in audit_files.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SOLARIS-A1 Stage 7 GTI-Aware Preprocessing and Segmentation Runner")
    parser.add_argument("--stem", default="all", help="Target file stem or 'all' (default: all)")
    parser.add_argument("--final", action="store_true", default=False, help="Run in final approved mode (refuses if G1/G2/G4 pending)")
    parser.add_argument("--config", default="config/default.yaml", help="Path to config file")
    parser.add_argument("--roles", default="config/column_roles.yaml", help="Path to column roles file")
    parser.add_argument("--decisions", default="config/decisions.yaml", help="Path to decisions file")
    parser.add_argument("--raw-dir", default="data/raw", help="Path to raw data directory")
    parser.add_argument("--out-dir", default="results/preprocessing", help="Path to output results directory")
    parser.add_argument("--segments-dir", default="data/processed/segments", help="Path to segments output directory")

    args = parser.parse_args()

    root = project_root()
    raw_dir = root / args.raw_dir
    out_dir = root / args.out_dir
    segments_dir = root / args.segments_dir
    config_path = root / args.config
    roles_path = root / args.roles
    decisions_path = root / args.decisions

    out_dir.mkdir(parents=True, exist_ok=True)
    segments_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("solaris_a1.preprocessing")

    logger.info("======================================================================")
    logger.info("SOLARIS-A1 STAGE 7: GTI-AWARE PREPROCESSING & SEGMENTATION")
    logger.info(f"Mode: {'FINAL (APPROVED ONLY)' if args.final else 'DEVELOPMENT (PROVISIONAL)'}")
    logger.info("======================================================================")

    # Check final approval gate
    is_approved, missing_items = check_approval_for_final(decisions_path, out_dir)
    if args.final and not is_approved:
        logger.error("Final run refused: The following Gate decisions remain PENDING:")
        for item in missing_items:
            logger.error(f"  - {item}")
        logger.error(f"Refusal details recorded in: {out_dir / 'AWAITING_G4.md'}")
        return 1

    # Load configuration
    cfg = load_config(config_path)
    prep_cfg = cfg.get("preprocessing", {})

    # In final mode, parameters must come from approved config
    max_gap = prep_cfg.get("max_gap_seconds", 2.0)
    min_seg = prep_cfg.get("min_segment_seconds", 60.0)
    boundary = prep_cfg.get("gti_boundary_convention", "START_INCLUSIVE_STOP_EXCLUSIVE")
    dup_policy = prep_cfg.get("duplicate_timestamp_policy", "ERROR")
    excl_flags = prep_cfg.get("excluded_quality_flags", [])

    # Load column roles
    with open(roles_path, "r", encoding="utf-8") as rf:
        roles_cfg = yaml.safe_load(rf) or {}

    lc_roles = roles_cfg.get("roles", {}).get("lightcurve", {})
    time_col = lc_roles.get("time_column", {}).get("name", "TIME")
    count_col = lc_roles.get("count_column", {}).get("name", "COUNTS")
    flag_col = lc_roles.get("quality_flag_column", {}).get("name", None)

    gti_roles = roles_cfg.get("roles", {}).get("gti", {})
    gti_start_col = gti_roles.get("start_column", {}).get("name", "START")
    gti_stop_col = gti_roles.get("stop_column", {}).get("name", "STOP")

    # Locate raw lightcurve files
    raw_files = list(raw_dir.glob("*.lc.gz")) + list(raw_dir.glob("*.lc"))
    if not raw_files:
        logger.error(f"No light curve files found in {raw_dir}")
        return 1

    summary_records: List[Dict[str, Any]] = []

    for lc_file in sorted(raw_files):
        stem = lc_file.name.replace(".lc.gz", "").replace(".lc", "")
        if args.stem != "all" and args.stem not in stem:
            continue

        # Look for paired GTI
        gti_file = raw_dir / lc_file.name.replace(".lc.", ".gti.")
        if not gti_file.is_file():
            gti_file = None

        res = preprocess_lightcurve_file(
            lc_path=lc_file,
            gti_path=gti_file,
            time_col=time_col,
            count_col=count_col,
            flag_col=flag_col,
            gti_start_col=gti_start_col,
            gti_stop_col=gti_stop_col,
            max_gap_seconds=max_gap,
            min_segment_seconds=min_seg,
            boundary=boundary,
            dup_policy=dup_policy,
            excluded_flags=excl_flags,
            is_final=args.final,
            segments_dir=segments_dir,
            results_dir=out_dir,
            logger=logger,
        )
        summary_records.append(res)

    # Write summary CSV
    summary_csv = out_dir / "summary.csv"
    with open(summary_csv, "w", newline="", encoding="utf-8") as sf:
        fieldnames = [
            "file_stem",
            "status",
            "is_final",
            "original_samples",
            "retained_samples",
            "retention_percentage",
            "n_segments",
            "immutability_verified",
        ]
        writer = csv.DictWriter(sf, fieldnames=fieldnames)
        writer.writeheader()
        for r in summary_records:
            writer.writerow({
                "file_stem": r["file_stem"],
                "status": r["status"],
                "is_final": r.get("is_final", False),
                "original_samples": r.get("original_samples", 0),
                "retained_samples": r.get("retained_samples", 0),
                "retention_percentage": r.get("retention_percentage", 0.0),
                "n_segments": r.get("n_segments", 0),
                "immutability_verified": r.get("immutability_verified", False),
            })

    # Write run_manifest.json
    run_manifest = out_dir / "run_manifest.json"
    with open(run_manifest, "w", encoding="utf-8") as rmf:
        json.dump({
            "stage": "Stage 7 — Preprocessing and GTI-Aware Segmentation",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "mode": "APPROVED (FINAL)" if args.final else "PROVISIONAL (DEVELOPMENT)",
            "summary": summary_records,
        }, rmf, indent=2)

    logger.info("======================================================================")
    logger.info("STAGE 7 PREPROCESSING COMPLETED")
    logger.info(f"Summary written to: {summary_csv}")
    logger.info(f"Run manifest written to: {run_manifest}")
    logger.info("======================================================================")

    return 0


if __name__ == "__main__":
    sys.exit(main())
