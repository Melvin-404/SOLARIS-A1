"""CLI runner for SOLARIS-A1 Stage 8 Sliding Windows and Feature Engineering.

Processes segmented observation CSV files from Stage 7, generates strictly
intra-segment sliding windows, extracts causal time-series features, estimates
local pre-window baseline flux, enforces the temporal leakage guard, and exports
auditable feature matrices.
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

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from solar_flare.paths import project_root
from solar_flare.config import load_config
from solar_flare.manifest import compute_sha256
from solar_flare.preprocessing.segmentation import ParameterPendingError
from solar_flare.features.windows import generate_windows
from solar_flare.features.baseline import causal_baseline
from solar_flare.features.registry import compute_features, GLOBAL_REGISTRY
from solar_flare.features.leakage_guard import check_no_future_samples, LeakageError


def check_gate_g5_approvals(decisions_path: Path) -> Tuple[bool, List[str]]:
    """Check whether Gate G5 decisions are APPROVED in decisions.yaml."""
    missing: List[str] = []
    if not decisions_path.is_file():
        missing.append(f"Decisions register not found: {decisions_path}")
        return False, missing

    with open(decisions_path, "r", encoding="utf-8") as f:
        decs_data = yaml.safe_load(f) or {}

    decs = decs_data.get("decisions", {})

    # Check G5 decisions: D-05, D-06, D-18, D-19, D-20
    for dec_id, desc in [
        ("D-05", "Window length W"),
        ("D-06", "Window stride S"),
        ("D-18", "Causal baseline lookback window duration"),
        ("D-19", "Rolling trend duration K"),
        ("D-20", "Minimum window coverage fraction"),
    ]:
        entry = decs.get(dec_id, {})
        if entry.get("status") != "APPROVED" or not entry.get("approved_by"):
            missing.append(f"Gate G5 / {dec_id}: {desc} is {entry.get('status', 'MISSING')}")

    return len(missing) == 0, missing


def build_features_for_stem(
    stem: str,
    segment_files: List[Path],
    features_cfg: Dict[str, Any],
    is_final: bool,
    out_features_dir: Path,
    out_results_dir: Path,
    logger: logging.Logger,
) -> Dict[str, Any]:
    """Execute window generation and feature extraction for all segments belonging to a stem."""
    logger.info(f"Building features for stem '{stem}' across {len(segment_files)} segment(s)...")

    w_sec = features_cfg.get("window_seconds", 60.0)
    s_sec = features_cfg.get("stride_seconds", 10.0)
    min_cov = features_cfg.get("min_coverage_fraction", 0.80)
    inc_low_cov = features_cfg.get("include_low_coverage", True)
    lookback = features_cfg.get("baseline_lookback_seconds", 600.0)
    min_base_samples = features_cfg.get("baseline_min_samples", 30)
    k_sec = features_cfg.get("rolling_trend_seconds_k", 15.0)
    pct_levels = features_cfg.get("percentiles", [5, 25, 75, 95])
    enabled_features = features_cfg.get("enabled_features", None)

    all_window_records: List[pd.DataFrame] = []
    all_feature_records: List[Dict[str, Any]] = []
    segment_hashes_before: Dict[str, str] = {}
    segment_summaries: List[Dict[str, Any]] = []

    for seg_file in segment_files:
        seg_id = seg_file.stem
        h_before = compute_sha256(seg_file)
        segment_hashes_before[seg_file.name] = h_before

        df_seg = pd.read_csv(seg_file)

        # 1. Generate sliding windows
        win_df, win_sum = generate_windows(
            segment_df=df_seg,
            segment_id=seg_id,
            window_seconds=w_sec,
            stride_seconds=s_sec,
            time_col="TIME",
            value_col="COUNTS",
            min_coverage_fraction=min_cov,
            include_low_coverage=inc_low_cov,
            is_final=is_final,
        )
        segment_summaries.append(win_sum)

        if win_df.empty:
            logger.warning(f"No windows produced for {seg_id}: {win_sum.get('reason')}")
            continue

        all_window_records.append(win_df)

        # 2. Extract features per window
        times_seg = df_seg["TIME"].to_numpy(dtype=np.float64)
        counts_seg = df_seg["COUNTS"].to_numpy(dtype=np.float64)

        for _, w_row in win_df.iterrows():
            w_id = w_row["window_id"]
            w_start = float(w_row["window_start"])
            w_end = float(w_row["window_end"])
            n_exp = int(w_row["n_expected_samples"])

            # Slice window samples
            s_idx = int(w_row["start_index"])
            e_idx = int(w_row["end_index"]) + 1

            w_times = times_seg[s_idx:e_idx]
            w_vals = counts_seg[s_idx:e_idx]

            # 3. Estimate local causal baseline
            base_val, base_rsn = causal_baseline(
                segment_df=df_seg,
                window_start=w_start,
                lookback_seconds=lookback,
                time_col="TIME",
                value_col="COUNTS",
                min_samples=min_base_samples,
                is_final=is_final,
            )

            # 4. Compute feature vector
            feat_vals, feat_rsns = compute_features(
                window_values=w_vals,
                window_times=w_times,
                baseline_value=base_val,
                enabled_features=enabled_features,
                n_expected_samples=n_exp,
                rolling_trend_k=k_sec,
                percentile_levels=pct_levels,
            )

            row_dict: Dict[str, Any] = {
                "window_id": w_id,
                "segment_id": seg_id,
                "file_stem": stem,
                "window_start": w_start,
                "window_end": w_end,  # Reference time t_ref
                "baseline_value": base_val,
                "baseline_reason": base_rsn,
            }
            row_dict.update(feat_vals)
            all_feature_records.append(row_dict)

    if not all_window_records:
        logger.warning(f"No windows generated for stem '{stem}' across all segments.")
        return {
            "stem": stem,
            "status": "ZERO_WINDOWS",
            "n_windows": 0,
            "leakage_guard_passed": True,
        }

    full_window_df = pd.concat(all_window_records, ignore_index=True)
    full_feature_df = pd.DataFrame(all_feature_records)

    # 5. Run temporal leakage guard
    try:
        check_no_future_samples(full_window_df, tolerance_seconds=1e-6)
        leakage_passed = True
        logger.info(f"Leakage guard PASSED for {stem}: zero future observations accessed.")
    except LeakageError as le:
        logger.error(f"Leakage guard FAILED for {stem}:\n{le}")
        return {
            "stem": stem,
            "status": "FAIL_LEAKAGE",
            "error": str(le),
            "n_windows": len(full_window_df),
            "leakage_guard_passed": False,
        }

    # 6. Verify segment immutability after processing
    for seg_file in segment_files:
        h_after = compute_sha256(seg_file)
        if h_after != segment_hashes_before[seg_file.name]:
            raise RuntimeError(f"Segment file mutated during feature extraction: {seg_file.name}")

    # 7. Write outputs to data/processed/features/<stem>/
    stem_feat_dir = out_features_dir / stem
    stem_feat_dir.mkdir(parents=True, exist_ok=True)

    win_index_path = stem_feat_dir / "window_index.csv"
    win_feat_path = stem_feat_dir / "window_features.csv"

    full_window_df.to_csv(win_index_path, index=False)
    full_feature_df.to_csv(win_feat_path, index=False)
    logger.info(f"Exported {len(full_feature_df)} window features to: {win_feat_path}")

    # 8. Write build log JSON to results/features/<stem>/
    stem_res_dir = out_results_dir / stem
    stem_res_dir.mkdir(parents=True, exist_ok=True)
    build_log_path = stem_res_dir / "build_log.json"

    n_low_cov = int((full_window_df["quality_flag"] == "LOW_COVERAGE").sum())
    low_cov_pct = float(n_low_cov / len(full_window_df) * 100.0) if len(full_window_df) > 0 else 0.0

    build_log = {
        "file_stem": stem,
        "mode": "APPROVED (FINAL)" if is_final else "PROVISIONAL (DEVELOPMENT)",
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "parameters": {
            "window_seconds": w_sec,
            "stride_seconds": s_sec,
            "min_coverage_fraction": min_cov,
            "include_low_coverage": inc_low_cov,
            "baseline_lookback_seconds": lookback,
            "baseline_min_samples": min_base_samples,
            "rolling_trend_seconds_k": k_sec,
            "percentiles": pct_levels,
        },
        "parameter_statuses": {
            "D-05": "PROVISIONAL",
            "D-06": "PROVISIONAL",
            "D-18": "PENDING (Gate G5)",
            "D-19": "PENDING (Gate G5)",
            "D-20": "PENDING (Gate G5)",
        },
        "metrics": {
            "n_segments_processed": len(segment_files),
            "n_total_windows": len(full_window_df),
            "n_low_coverage": n_low_cov,
            "low_coverage_percentage": round(low_cov_pct, 4),
            "leakage_guard_passed": leakage_passed,
        },
        "segment_hashes_before": segment_hashes_before,
        "output_hashes": {
            "window_index.csv": compute_sha256(win_index_path),
            "window_features.csv": compute_sha256(win_feat_path),
        },
    }

    with open(build_log_path, "w", encoding="utf-8") as blf:
        json.dump(build_log, blf, indent=2)

    return {
        "stem": stem,
        "status": "SUCCESS",
        "is_final": is_final,
        "n_windows": len(full_window_df),
        "n_low_coverage": n_low_cov,
        "low_coverage_percentage": round(low_cov_pct, 4),
        "leakage_guard_passed": leakage_passed,
        "window_index_path": str(win_index_path.as_posix()),
        "window_features_path": str(win_feat_path.as_posix()),
        "build_log_path": str(build_log_path.as_posix()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SOLARIS-A1 Stage 8 Feature Engineering Runner")
    parser.add_argument("--stem", default="all", help="Target file stem or 'all' (default: all)")
    parser.add_argument("--final", action="store_true", default=False, help="Run in final mode (refuses if Gate G5 pending)")
    parser.add_argument("--config", default="config/default.yaml", help="Path to config file")
    parser.add_argument("--decisions", default="config/decisions.yaml", help="Path to decisions file")
    parser.add_argument("--segments-dir", default="data/processed/segments", help="Path to segments directory")
    parser.add_argument("--features-dir", default="data/processed/features", help="Path to features directory")
    parser.add_argument("--results-dir", default="results/features", help="Path to results directory")

    args = parser.parse_args()

    root = project_root()
    segments_dir = root / args.segments_dir
    features_dir = root / args.features_dir
    results_dir = root / args.results_dir
    config_path = root / args.config
    decisions_path = root / args.decisions

    results_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("solaris_a1.features")

    logger.info("======================================================================")
    logger.info("SOLARIS-A1 STAGE 8: SLIDING WINDOWS & FEATURE ENGINEERING")
    logger.info(f"Mode: {'FINAL (APPROVED ONLY)' if args.final else 'DEVELOPMENT (PROVISIONAL)'}")
    logger.info("======================================================================")

    # Check Gate G5 approvals if final mode requested
    if args.final:
        is_approved, missing_g5 = check_gate_g5_approvals(decisions_path)
        if not is_approved:
            logger.error("Final run refused: The following Gate G5 decisions remain PENDING:")
            for m in missing_g5:
                logger.error(f"  - {m}")
            return 1

    # Load configuration
    cfg = load_config(config_path)
    features_cfg = cfg.get("features", {})

    # Discover stems under segments_dir
    if not segments_dir.is_dir():
        logger.error(f"Segments directory not found: {segments_dir}")
        blocked_md = results_dir / "BLOCKED.md"
        blocked_md.write_text("# Stage 8 BLOCKED: Missing segments directory\n", encoding="utf-8")
        return 1

    stem_dirs = [d for d in segments_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if not stem_dirs:
        logger.error(f"No segment folders found in {segments_dir}")
        blocked_md = results_dir / "BLOCKED.md"
        blocked_md.write_text("# Stage 8 BLOCKED: No continuous segment files found\n", encoding="utf-8")
        return 1

    summary_records: List[Dict[str, Any]] = []

    for s_dir in sorted(stem_dirs):
        stem_name = s_dir.name
        if args.stem != "all" and args.stem not in stem_name:
            continue

        seg_files = sorted(list(s_dir.glob("*.csv")))
        if not seg_files:
            logger.warning(f"No CSV files found in {s_dir}")
            continue

        res = build_features_for_stem(
            stem=stem_name,
            segment_files=seg_files,
            features_cfg=features_cfg,
            is_final=args.final,
            out_features_dir=features_dir,
            out_results_dir=results_dir,
            logger=logger,
        )
        summary_records.append(res)

    # Write overall summary.csv
    summary_csv = results_dir / "summary.csv"
    with open(summary_csv, "w", newline="", encoding="utf-8") as sf:
        fieldnames = [
            "stem",
            "status",
            "is_final",
            "n_windows",
            "n_low_coverage",
            "low_coverage_percentage",
            "leakage_guard_passed",
        ]
        writer = csv.DictWriter(sf, fieldnames=fieldnames)
        writer.writeheader()
        for r in summary_records:
            writer.writerow({
                "stem": r["stem"],
                "status": r["status"],
                "is_final": r.get("is_final", False),
                "n_windows": r.get("n_windows", 0),
                "n_low_coverage": r.get("n_low_coverage", 0),
                "low_coverage_percentage": r.get("low_coverage_percentage", 0.0),
                "leakage_guard_passed": r.get("leakage_guard_passed", False),
            })

    logger.info("======================================================================")
    logger.info("STAGE 8 FEATURE EXTRACTION COMPLETED")
    logger.info(f"Summary written to: {summary_csv}")
    logger.info("======================================================================")

    return 0


if __name__ == "__main__":
    sys.exit(main())
