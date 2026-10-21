"""CLI runner for SOLARIS-A1 Stage 4 Data Quality Assessment.

Runs non-destructive quality checks, cadence analysis, GTI coverage quantification,
per-file reporting and figures, summary table, and column-role evidence compilation.
All checks execute in PROVISIONAL mode until Gate G1 confirmation.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import logging
from pathlib import Path
import sys

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from typing import Any, Dict, List, Optional
import numpy as np
import yaml
from astropy.io import fits

from solar_flare.config import load_config
from solar_flare.quality.checks import (
    check_non_finite,
    check_negative_values,
    check_duplicate_timestamps,
    check_time_ordering,
    check_zero_runs,
    check_quality_flags,
    check_candidate_spikes,
)
from solar_flare.quality.cadence import estimate_cadence, find_cadence_gaps
from solar_flare.quality.gti_coverage import load_gti_intervals, compute_coverage
from solar_flare.quality.report import (
    plot_time_coverage,
    plot_cadence_histogram,
    plot_count_distribution,
    plot_flagged_samples,
    generate_file_report,
)
from solar_flare.quality.roles import generate_column_role_evidence


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_awaiting_g1_report(out_path: Path, column_roles_path: Path) -> None:
    """Generate AWAITING_G1.md listing human confirmation requirements."""
    content = [
        "# SOLARIS-A1: AWAITING GATE G1 HUMAN CONFIRMATION",
        "",
        "> **STATUS: PROVISIONAL EXECUTION COMPLETE**",
        "> Stage 4 data quality assessment has completed in **PROVISIONAL mode**.",
        "> No data has been modified, clipped, or removed. No scientific conclusions are declared.",
        "> Completion is strictly PROVISIONAL until the student researcher confirms Gate G1 items.",
        "",
        "---",
        "",
        "## Required Human Confirmations (Gate G1)",
        "",
        "The student researcher must review official SoLEXS instrument documentation and confirm:",
        "",
        "1. **Column Roles in Light-Curve Data (`AL1_SOLEXS_20261018_SDD2_L1.lc.gz`):**",
        "   - Confirm column `TIME` represents elapsed observation seconds.",
        "   - Confirm column `COUNTS` represents integrated detector counts or count rate (c/s).",
        "   - Confirm whether a quality flag column exists or if data points are unflagged.",
        "",
        "2. **Time System Alignment (Decision D-10):**",
        "   - Confirm `TIMESYS = 'UTC'`, `MJDREFI = 40587` corresponds to Unix epoch (1970-01-01 00:00:00 UTC).",
        "   - Confirm `TSTART = 1792281600.0` corresponds to `2026-10-18 00:00:00 UTC`.",
        "",
        "3. **GTI Table Columns and Observation State:**",
        "   - Confirm `START` and `STOP` in `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` represent valid observation intervals.",
        "   - Confirm why detector SDD1 (`AL1_SOLEXS_20261018_SDD1_L1.gti.gz`) has **0 intervals** (instrument status).",
        "",
        "4. **Thresholds Confirmation (Gate G2 / Decision D-13):**",
        "   - Review cadence tolerance factor: `1.5`.",
        "   - Review robust MAD candidate spike threshold: `z > 5.0`.",
        "   - Review minimum contiguous zero run length: `5` samples.",
        "",
        "---",
        "",
        "## How to Confirm Gate G1",
        "",
        f"1. Inspect [`column_role_evidence.md`](column_role_evidence.md) and [`summary.csv`](summary.csv).",
        f"2. Update [`{column_roles_path.as_posix()}`](file:///{column_roles_path.resolve().as_posix()}) to set status from `PROVISIONAL` to `CONFIRMED`.",
        "3. Record confirmation in `config/decisions.yaml` (D-09, D-10, D-13) and `docs/01_decision_log.md`.",
        "",
    ]
    out_path.write_text("\n".join(content), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SOLARIS-A1 Stage 4 Data Quality Assessment.")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Directory containing raw FITS files.")
    parser.add_argument("--manifest", type=str, default="data/manifests/manifest.csv", help="Path to manifest.csv.")
    parser.add_argument("--out-dir", type=str, default="results/quality", help="Output directory for quality results.")
    parser.add_argument("--config", type=str, default="config/default.yaml", help="Path to default.yaml.")
    parser.add_argument("--column-roles", type=str, default="config/column_roles.yaml", help="Path to column_roles.yaml.")

    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    config_path = Path(args.config)
    roles_path = Path(args.column_roles)
    manifest_path = Path(args.manifest)

    out_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("solaris_a1.quality")
    logger.info("Initializing Stage 4 Data Quality Assessment...")

    # Load configuration
    cfg = load_config(config_path)
    quality_cfg = cfg.get("quality", {})
    cadence_tol = float(quality_cfg.get("cadence_tolerance_factor", 1.5))
    spike_z_thresh = float(quality_cfg.get("spike_z_score_threshold", 5.0))
    min_zero_len = int(quality_cfg.get("min_zero_run_length", 5))

    # Load column roles
    if not roles_path.is_file():
        logger.error(f"Column roles file not found: {roles_path}")
        return 1

    with open(roles_path, "r", encoding="utf-8") as rf:
        roles_cfg = yaml.safe_load(rf) or {}

    lc_roles = roles_cfg.get("roles", {}).get("lightcurve", {})
    time_col = lc_roles.get("time_column", {}).get("name", "TIME")
    count_col = lc_roles.get("count_column", {}).get("name", "COUNTS")
    time_role_status = lc_roles.get("time_column", {}).get("status", "PROVISIONAL")
    count_role_status = lc_roles.get("count_column", {}).get("status", "PROVISIONAL")

    gti_roles = roles_cfg.get("roles", {}).get("gti", {})
    gti_start_col = gti_roles.get("start_column", {}).get("name", "START")
    gti_stop_col = gti_roles.get("stop_column", {}).get("name", "STOP")

    overall_role_status = (
        "CONFIRMED"
        if time_role_status == "CONFIRMED" and count_role_status == "CONFIRMED"
        else "PROVISIONAL"
    )

    logger.info(f"Loaded thresholds: cadence_tol={cadence_tol}, spike_z={spike_z_thresh}, min_zero={min_zero_len}")
    logger.info(f"Column role status: {overall_role_status}")

    # 1. Column-role evidence compilation
    evidence_json = out_dir / "column_role_evidence.json"
    evidence_md = out_dir / "column_role_evidence.md"
    logger.info("Compiling column-role evidence...")
    generate_column_role_evidence(raw_dir, evidence_json, evidence_md)

    # 2. Identify files from raw_dir and manifest
    raw_files = sorted(list(raw_dir.glob("*.gz")) + list(raw_dir.glob("*.fits")))
    logger.info(f"Found {len(raw_files)} files in {raw_dir}")

    summary_rows: List[Dict[str, Any]] = []

    # Process files
    for f in raw_files:
        name_lower = f.name.lower()

        # Classification for spectrum / OTHER files
        if ".pi" in name_lower:
            stem = f.name.replace(".gz", "").replace(".fits", "")
            logger.info(f"Classifying {f.name} as OTHER (read-only inspection)...")
            summary_rows.append({
                "file_stem": stem,
                "n_samples": "N/A",
                "n_nan": "N/A",
                "n_pos_inf": "N/A",
                "n_neg_inf": "N/A",
                "n_negative": "N/A",
                "n_zero": "N/A",
                "n_duplicate_timestamps": "N/A",
                "n_backward_steps": "N/A",
                "n_cadence_gaps": "N/A",
                "gti_status": "NOT_APPLICABLE",
                "gti_covered_fraction": "N/A",
                "n_samples_outside_gti": "N/A",
                "n_candidate_spikes": "N/A",
                "role_status": "UNRESOLVED",
                "overall_status": "OTHER — inspected read-only, not used in quality checks",
            })
            continue

        # Skip GTI files as primary targets (they are paired with LC)
        if ".gti" in name_lower:
            # Check if this GTI was paired with any LC
            sdd_detector = "SDD2" if "sdd2" in name_lower else ("SDD1" if "sdd1" in name_lower else "")
            paired_lc_exists = any("lc" in other.name.lower() and sdd_detector.lower() in other.name.lower() for other in raw_files)
            if not paired_lc_exists:
                stem = f.name.replace(".gz", "").replace(".fits", "")
                summary_rows.append({
                    "file_stem": stem,
                    "n_samples": "N/A",
                    "n_nan": "N/A",
                    "n_pos_inf": "N/A",
                    "n_neg_inf": "N/A",
                    "n_negative": "N/A",
                    "n_zero": "N/A",
                    "n_duplicate_timestamps": "N/A",
                    "n_backward_steps": "N/A",
                    "n_cadence_gaps": "N/A",
                    "gti_status": "GTI EMPTY FOR THIS OBSERVATION",
                    "gti_covered_fraction": "N/A",
                    "n_samples_outside_gti": "N/A",
                    "n_candidate_spikes": "N/A",
                    "role_status": "PROVISIONAL",
                    "overall_status": "UNPAIRED_GTI — inspected read-only",
                })
            continue

        # Process Light Curve files
        if ".lc" in name_lower:
            stem = f.name.replace(".gz", "").replace(".fits", "")
            file_out_dir = out_dir / stem
            logger.info(f"Processing light curve: {f.name} (stem: {stem})...")

            try:
                with fits.open(f, mode="readonly", memmap=True) as hdul:
                    table_hdu = hdul[1]
                    col_names = table_hdu.columns.names

                    if time_col not in col_names or count_col not in col_names:
                        raise ValueError(f"Required columns ({time_col}, {count_col}) missing in {f.name}")

                    times = np.asarray(table_hdu.data[time_col], dtype=np.float64)
                    counts = np.asarray(table_hdu.data[count_col], dtype=np.float64)

                # Pair with GTI file
                gti_name = f.name.replace(".lc.", ".gti.")
                gti_path = raw_dir / gti_name
                if gti_path.is_file():
                    logger.info(f"Loading paired GTI file: {gti_name}")
                    gti_data = load_gti_intervals(gti_path, start_col=gti_start_col, stop_col=gti_stop_col)
                else:
                    logger.warning(f"No paired GTI file found for {f.name}")
                    gti_data = {"status": "EMPTY", "intervals": [], "n_intervals": 0}

                # Run pure quality checks
                check_res_non_finite = check_non_finite(counts)
                check_res_negatives = check_negative_values(counts)
                check_res_dups = check_duplicate_timestamps(times)
                check_res_ordering = check_time_ordering(times)
                check_res_zeros = check_zero_runs(counts, times, min_run_length=min_zero_len)
                check_res_flags = check_quality_flags(None)
                check_res_spikes = check_candidate_spikes(counts, times, z_threshold=spike_z_thresh)

                all_checks = {
                    "check_non_finite": check_res_non_finite,
                    "check_negative_values": check_res_negatives,
                    "check_duplicate_timestamps": check_res_dups,
                    "check_time_ordering": check_res_ordering,
                    "check_zero_runs": check_res_zeros,
                    "check_quality_flags": check_res_flags,
                    "check_candidate_spikes": check_res_spikes,
                }

                # Run cadence analysis
                cadence_stats = estimate_cadence(times)
                cadence_gaps = find_cadence_gaps(
                    times,
                    expected_cadence=cadence_stats.get("cadence_median"),
                    tolerance_factor=cadence_tol,
                )
                cadence_summary = {**cadence_stats, **cadence_gaps}

                # Run GTI coverage quantification
                coverage = compute_coverage(times, gti_data)

                # Generate Diagnostic Plots
                file_out_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Generating diagnostic plots in {file_out_dir}...")
                plot_time_coverage(
                    times,
                    counts,
                    gti_data.get("intervals", []),
                    cadence_gaps.get("gaps", []),
                    file_out_dir / "time_coverage.png",
                    title=f"{stem} — Time Coverage & GTI Intervals",
                )
                plot_cadence_histogram(
                    times,
                    cadence_stats,
                    file_out_dir / "cadence_histogram.png",
                    title=f"{stem} — Sampling Cadence Histogram",
                )
                plot_count_distribution(
                    counts,
                    file_out_dir / "count_distribution.png",
                    title=f"{stem} — Raw Count Distribution",
                )

                spike_indices = [
                    ex["index"]
                    for ex in check_res_spikes.get("detail", {}).get("examples", [])
                ]
                plot_flagged_samples(
                    times,
                    counts,
                    spike_indices,
                    file_out_dir / "flagged_samples.png",
                    title=f"{stem} — Classified Samples",
                )

                # Generate per-file report
                generate_file_report(
                    file_stem=stem,
                    output_dir=file_out_dir,
                    checks_results=all_checks,
                    cadence_results=cadence_summary,
                    gti_results=coverage,
                    role_status=overall_role_status,
                )

                # Append to summary rows
                n_samples = len(times)
                n_nan = check_res_non_finite["counts"]["n_nan"]
                n_pos_inf = check_res_non_finite["counts"]["n_pos_inf"]
                n_neg_inf = check_res_non_finite["counts"]["n_neg_inf"]
                n_neg = check_res_negatives["counts"]["n_negative"]
                n_zero = check_res_zeros["counts"]["n_zero_samples"]
                n_dup = check_res_dups["counts"]["n_duplicates"]
                n_back = check_res_ordering["counts"]["n_backward_steps"]
                n_gaps = cadence_gaps["n_cadence_gaps"]
                gti_stat = coverage["gti_status"]
                gti_cov_frac = f"{coverage['gti_covered_fraction']:.4f}"
                n_outside = coverage["n_samples_outside_gti"]
                n_spikes = check_res_spikes["counts"]["n_candidate_spikes"]

                summary_rows.append({
                    "file_stem": stem,
                    "n_samples": n_samples,
                    "n_nan": n_nan,
                    "n_pos_inf": n_pos_inf,
                    "n_neg_inf": n_neg_inf,
                    "n_negative": n_neg,
                    "n_zero": n_zero,
                    "n_duplicate_timestamps": n_dup,
                    "n_backward_steps": n_back,
                    "n_cadence_gaps": n_gaps,
                    "gti_status": gti_stat,
                    "gti_covered_fraction": gti_cov_frac,
                    "n_samples_outside_gti": n_outside,
                    "n_candidate_spikes": n_spikes,
                    "role_status": overall_role_status,
                    "overall_status": "PROVISIONAL",
                })

            except Exception as e:
                logger.error(f"Error processing {f.name}: {e}", exc_info=True)
                summary_rows.append({
                    "file_stem": stem,
                    "n_samples": "ERROR",
                    "n_nan": "ERROR",
                    "n_pos_inf": "ERROR",
                    "n_neg_inf": "ERROR",
                    "n_negative": "ERROR",
                    "n_zero": "ERROR",
                    "n_duplicate_timestamps": "ERROR",
                    "n_backward_steps": "ERROR",
                    "n_cadence_gaps": "ERROR",
                    "gti_status": "ERROR",
                    "gti_covered_fraction": "ERROR",
                    "n_samples_outside_gti": "ERROR",
                    "n_candidate_spikes": "ERROR",
                    "role_status": overall_role_status,
                    "overall_status": f"FAIL: {str(e)}",
                })

    # Write summary.csv
    summary_csv_path = out_dir / "summary.csv"
    logger.info(f"Writing summary table to {summary_csv_path}...")
    fieldnames = [
        "file_stem",
        "n_samples",
        "n_nan",
        "n_pos_inf",
        "n_neg_inf",
        "n_negative",
        "n_zero",
        "n_duplicate_timestamps",
        "n_backward_steps",
        "n_cadence_gaps",
        "gti_status",
        "gti_covered_fraction",
        "n_samples_outside_gti",
        "n_candidate_spikes",
        "role_status",
        "overall_status",
    ]
    with open(summary_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary_rows:
            writer.writerow(row)

    # Write AWAITING_G1.md
    awaiting_path = out_dir / "AWAITING_G1.md"
    logger.info(f"Writing awaiting G1 document to {awaiting_path}...")
    write_awaiting_g1_report(awaiting_path, roles_path)

    # Write run_manifest.json
    run_manifest_path = out_dir / "run_manifest.json"
    run_meta = {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "command": " ".join(sys.argv),
        "raw_dir": str(raw_dir.resolve()),
        "manifest": str(manifest_path.resolve()),
        "out_dir": str(out_dir.resolve()),
        "config": str(config_path.resolve()),
        "column_roles": str(roles_path.resolve()),
        "thresholds": {
            "cadence_tolerance_factor": cadence_tol,
            "spike_z_score_threshold": spike_z_thresh,
            "min_zero_run_length": min_zero_len,
        },
        "files_processed": [r["file_stem"] for r in summary_rows],
        "overall_status": "PROVISIONAL pending G1",
        "exit_code": 0,
    }
    with open(run_manifest_path, "w", encoding="utf-8") as rmf:
        json.dump(run_meta, rmf, indent=2)

    logger.info("Stage 4 Data Quality Assessment completed successfully in PROVISIONAL mode.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
