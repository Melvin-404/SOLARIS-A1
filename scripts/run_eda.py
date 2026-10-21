"""CLI runner for SOLARIS-A1 Stage 5 Exploratory Data Analysis (EDA).

Generates variability metrics, robust running baselines, candidate transient intervals,
diagnostic plots (PNG and PDF), parameter audit logs, and run manifests.
All candidate intervals are strictly tagged 'CANDIDATE — UNVERIFIED'.
No output represents a flare label, ground truth, or training target.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import yaml
from astropy.io import fits

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from solar_flare.config import load_config
from solar_flare.eda.variability import variability_stats, rolling_summary
from solar_flare.eda.bursts import robust_baseline, candidate_intervals
from solar_flare.eda.event_comparison import compare_candidates_to_events
from solar_flare.eda.plots import (
    plot_light_curve,
    plot_count_distribution,
    plot_coverage_timeline,
    plot_burst_gallery,
)
from solar_flare.quality.gti_coverage import load_gti_intervals


def write_eda_log(
    log_path: Path,
    stem: str,
    parameters: Dict[str, Any],
    candidate_count: int,
    gti_status: str,
    event_comp_status: str,
) -> None:
    """Write human-readable parameter audit log."""
    lines = [
        f"SOLARIS-A1 EDA EXECUTION AUDIT LOG: {stem}",
        f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        "",
        "EXPLORATORY STATUS: ALL CANDIDATES ARE UNVERIFIED.",
        "Nothing in this directory represents a flare label, ground truth, or training target.",
        "",
        "--- Parameter Audit Table ---",
        f"- baseline_span_seconds: {parameters.get('baseline_span_seconds')} s (Status: PROVISIONAL)",
        f"- burst_threshold_sigma: {parameters.get('burst_threshold_sigma')} sigma (Status: PROVISIONAL)",
        f"- burst_min_duration_seconds: {parameters.get('burst_min_duration_seconds')} s (Status: PROVISIONAL)",
        f"- gallery_max_panels: {parameters.get('gallery_max_panels')} (Status: PROVISIONAL)",
        f"- rolling_window_seconds: {parameters.get('rolling_window_seconds')} s (Status: PROVISIONAL)",
        "",
        "--- Execution Observations ---",
        f"- GTI Status: {gti_status}",
        f"- Candidate Burst Intervals Detected: {candidate_count} (Status: CANDIDATE — UNVERIFIED)",
        f"- Event Comparison Status: {event_comp_status}",
        "",
        "CRITICAL SCIENTIFIC NOTICE:",
        "No candidate interval may be utilized as ground truth without human researcher",
        "verification against independent solar flare catalogs at Gate G3.",
    ]
    log_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SOLARIS-A1 Stage 5 Exploratory Data Analysis.")
    parser.add_argument("--stem", type=str, default=None, help="Target file stem (optional).")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Path to raw FITS directory.")
    parser.add_argument("--quality-dir", type=str, default="results/quality", help="Path to Stage 4 quality directory.")
    parser.add_argument("--out-dir", type=str, default="results/eda", help="Output directory for EDA artifacts.")
    parser.add_argument("--config", type=str, default="config/default.yaml", help="Path to default.yaml.")
    parser.add_argument("--column-roles", type=str, default="config/column_roles.yaml", help="Path to column_roles.yaml.")

    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    quality_dir = Path(args.quality_dir)
    config_path = Path(args.config)
    roles_path = Path(args.column_roles)

    out_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("solaris_a1.eda")
    logger.info("Initializing Stage 5 Exploratory Data Analysis (EDA)...")

    # Load configuration
    cfg = load_config(config_path)
    eda_cfg = cfg.get("eda", {})
    span_s = float(eda_cfg.get("baseline_span_seconds", 600.0))
    thresh_sigma = float(eda_cfg.get("burst_threshold_sigma", 5.0))
    min_dur_s = float(eda_cfg.get("burst_min_duration_seconds", 10.0))
    max_panels = int(eda_cfg.get("gallery_max_panels", 9))
    roll_win_s = float(eda_cfg.get("rolling_window_seconds", 60.0))

    # Load column roles
    time_col = "TIME"
    count_col = "COUNTS"
    gti_start_col = "START"
    gti_stop_col = "STOP"
    if roles_path.is_file():
        with open(roles_path, "r", encoding="utf-8") as rf:
            roles_dict = yaml.safe_load(rf) or {}
            lc_r = roles_dict.get("roles", {}).get("lightcurve", {})
            time_col = lc_r.get("time_column", {}).get("name", "TIME")
            count_col = lc_r.get("count_column", {}).get("name", "COUNTS")
            gti_r = roles_dict.get("roles", {}).get("gti", {})
            gti_start_col = gti_r.get("start_column", {}).get("name", "START")
            gti_stop_col = gti_r.get("stop_column", {}).get("name", "STOP")

    logger.info(f"Loaded EDA parameters: baseline_span={span_s}s, threshold={thresh_sigma}sigma, min_duration={min_dur_s}s")

    # Find light curve files
    lc_files = sorted(list(raw_dir.glob("*.lc.gz")) + list(raw_dir.glob("*.lc.fits")))
    if not lc_files:
        # Fallback to any lc
        lc_files = [f for f in raw_dir.iterdir() if ".lc" in f.name.lower()]

    if args.stem:
        lc_files = [f for f in lc_files if args.stem in f.name]

    logger.info(f"Identified {len(lc_files)} light-curve files for exploratory analysis.")

    for f in lc_files:
        stem = f.name.replace(".gz", "").replace(".fits", "")
        file_out_dir = out_dir / stem
        file_out_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Processing light curve: {f.name} (stem: {stem})...")

        with fits.open(f, mode="readonly", memmap=True) as hdul:
            table_hdu = hdul[1]
            times = np.asarray(table_hdu.data[time_col], dtype=np.float64)
            counts = np.asarray(table_hdu.data[count_col], dtype=np.float64)

        # Pair with GTI file
        gti_name = f.name.replace(".lc.", ".gti.")
        gti_path = raw_dir / gti_name
        gti_status_str = "NOT_PAIRED"
        gti_data: Dict[str, Any] = {"status": "EMPTY", "intervals": []}
        if gti_path.is_file():
            try:
                gti_data = load_gti_intervals(gti_path, start_col=gti_start_col, stop_col=gti_stop_col)
                gti_status_str = gti_data.get("message", "VALID")
            except Exception as ge:
                logger.warning(f"Could not load GTI for {f.name}: {ge}")
                gti_status_str = f"ERROR: {str(ge)}"

        # 1. Variability statistics
        logger.info("Computing variability statistics...")
        v_stats = variability_stats(counts)
        v_df = pd.DataFrame([v_stats])
        v_df.to_csv(file_out_dir / "variability_summary.csv", index=False)

        # 2. Robust baseline & Candidate Burst Intervals
        logger.info("Computing running median baseline and candidate burst intervals...")
        base = robust_baseline(times, counts, span_seconds=span_s)
        candidates_df = candidate_intervals(
            times,
            counts,
            baseline=base,
            threshold_sigma=thresh_sigma,
            min_duration_seconds=min_dur_s,
        )

        cand_csv_path = file_out_dir / "candidate_bursts.csv"
        candidates_df.to_csv(cand_csv_path, index=False)
        n_cands = len(candidates_df)
        logger.info(f"Detected {n_cands} candidate burst intervals (status: CANDIDATE — UNVERIFIED).")

        # 3. Event comparison (strictly NOT PERFORMED)
        event_comp = compare_candidates_to_events(candidates_df, events_df=None)
        logger.info(f"Event comparison check: {event_comp['status']}")

        # 4. Generate Diagnostic Figures
        logger.info("Generating diagnostic EDA plots...")
        plot_light_curve(
            times,
            counts,
            gti=gti_data,
            candidates=candidates_df,
            baseline=base,
            output_path=file_out_dir / "light_curve.png",
            title=f"{stem} — Exploratory Light Curve & Candidates",
        )

        plot_count_distribution(
            counts,
            output_path=file_out_dir / "count_distribution.png",
            title=f"{stem} — Count Distribution",
        )

        plot_coverage_timeline(
            gti=gti_data,
            times=times,
            output_path=file_out_dir / "coverage_timeline.png",
            title=f"{stem} — Coverage Timeline",
        )

        plot_burst_gallery(
            times,
            counts,
            candidates=candidates_df,
            max_panels=max_panels,
            output_path=file_out_dir / "burst_gallery.png",
            title=f"{stem} — Candidate Burst Gallery",
        )

        # 5. Write eda_log.txt
        write_eda_log(
            file_out_dir / "eda_log.txt",
            stem=stem,
            parameters={
                "baseline_span_seconds": span_s,
                "burst_threshold_sigma": thresh_sigma,
                "burst_min_duration_seconds": min_dur_s,
                "gallery_max_panels": max_panels,
                "rolling_window_seconds": roll_win_s,
            },
            candidate_count=n_cands,
            gti_status=gti_status_str,
            event_comp_status=event_comp["status"],
        )

        # 6. Write run_manifest.json
        run_manifest = {
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "file_stem": stem,
            "raw_file": str(f.resolve()),
            "gti_file": str(gti_path.resolve()) if gti_path.is_file() else None,
            "parameters": {
                "baseline_span_seconds": span_s,
                "burst_threshold_sigma": thresh_sigma,
                "burst_min_duration_seconds": min_dur_s,
                "gallery_max_panels": max_panels,
                "rolling_window_seconds": roll_win_s,
            },
            "candidate_count": n_cands,
            "event_comparison_status": event_comp["status"],
            "artifacts_generated": [
                "variability_summary.csv",
                "candidate_bursts.csv",
                "light_curve.png",
                "light_curve.pdf",
                "count_distribution.png",
                "coverage_timeline.png",
                "burst_gallery.png",
                "eda_log.txt",
                "run_manifest.json",
            ],
            "status": "COMPLETED — ALL CANDIDATES UNVERIFIED",
        }
        with open(file_out_dir / "run_manifest.json", "w", encoding="utf-8") as mf:
            json.dump(run_manifest, mf, indent=2)

    logger.info("Stage 5 Exploratory Data Analysis completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
