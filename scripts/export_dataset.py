"""SOLARIS-A1 Dataset Export Command-Line Tool (Stage 9).

Integrates validated sliding feature windows with independently verified ground-truth labels,
and exports segregated tabular datasets for ML training and validation.

Tasks supported:
- detection (Task A): Solar flare event detection in observation windows
- prediction (Task B): Pre-flare activity forecasting within a future horizon

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Detection export requires Gate G3 approval (docs/08_labelling_policy.md and decisions D-01..D-15).
2. Prediction export requires Gate G6 approval (docs/22_forecasting_policy.md and decision D-07).
3. If prerequisites are not met, the script strictly REFUSES execution, logs exact reasons,
   writes a BLOCKED report to results/exports/BLOCKED_<TASK>.md, and exits with code 1.
4. Real candidate bursts from Stage 5 are strictly prohibited from being used as labels.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import yaml
import pandas as pd

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from solar_flare.logging_setup import setup_logging
from solar_flare.paths import project_root
from solar_flare.labels.policy import assert_labelling_approved, LabellingNotApprovedError
from solar_flare.export.targets import assert_forecasting_approved, ForecastingNotApprovedError
from solar_flare.export.join_labels import load_approved_events, label_windows_detection
from solar_flare.export.targets import prediction_target
from solar_flare.export.export import export_dataset, compute_export_id


logger = logging.getLogger("solaris_a1.export")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SOLARIS-A1 Stage 9: Policy-Guarded Dataset Export"
    )
    parser.add_argument(
        "--task",
        required=True,
        choices=["detection", "prediction"],
        help="Scientific task to export ('detection' for Task A, 'prediction' for Task B).",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional path to configuration YAML (defaults to config/default.yaml).",
    )
    parser.add_argument(
        "--events",
        default=None,
        help="Optional path to approved event records CSV (defaults to data/manifests/event_records_approved.csv).",
    )
    parser.add_argument(
        "--features-dir",
        default=None,
        help="Optional path to directory containing Stage 8 window features.",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Optional destination path for exported datasets (defaults to data/processed/datasets).",
    )
    parser.add_argument(
        "--cohort",
        default="all",
        choices=["all", "pilot", "july2024"],
        help="Observation cohort to export ('all', 'pilot', or 'july2024'). Defaults to 'all'.",
    )
    parser.add_argument(
        "--export-id",
        default=None,
        help="Optional explicit dataset export identifier (e.g. 'exp_det_july2024').",
    )
    return parser.parse_args(argv)


def update_export_log(log_path: Path, entry: Dict[str, Any]) -> None:
    """Append or update entries in results/exports/export_log.json."""
    data = []
    if log_path.is_file():
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = [data]
        except Exception:
            data = []
    data.append(entry)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def check_detection_prerequisites(root: Path) -> List[str]:
    """Inspect and return missing prerequisites for detection export."""
    missing: List[str] = []
    policy_path = root / "docs" / "08_labelling_policy.md"
    decisions_path = root / "config" / "decisions.yaml"

    try:
        assert_labelling_approved(policy_path=policy_path, decisions_path=decisions_path)
    except LabellingNotApprovedError as e:
        missing.append(str(e))

    # Check approved event record existence
    event_path = root / "data" / "manifests" / "event_records_approved.csv"
    if not event_path.is_file():
        missing.append(
            f"Approved event records file does not exist at '{event_path.relative_to(root)}'. "
            "Gate G3 requires human verification and placement of approved independent flare event records."
        )

    # Check Stage 8 features
    feat_dir = root / "data" / "processed" / "features"
    feat_files = list(feat_dir.glob("**/window_features.csv")) if feat_dir.is_dir() else []
    if not feat_files:
        missing.append("No Stage 8 feature tables found under 'data/processed/features/'.")

    return missing


def check_prediction_prerequisites(root: Path) -> List[str]:
    """Inspect and return missing prerequisites for prediction export."""
    missing: List[str] = []
    policy_path = root / "docs" / "22_forecasting_policy.md"
    decisions_path = root / "config" / "decisions.yaml"

    try:
        assert_forecasting_approved(policy_path=policy_path, decisions_path=decisions_path)
    except ForecastingNotApprovedError as e:
        missing.append(str(e))

    event_path = root / "data" / "manifests" / "event_records_approved.csv"
    if not event_path.is_file():
        missing.append(
            f"Approved event records file does not exist at '{event_path.relative_to(root)}'. "
            "Gate G6 requires human-verified flare event onsets."
        )

    feat_dir = root / "data" / "processed" / "features"
    feat_files = list(feat_dir.glob("**/window_features.csv")) if feat_dir.is_dir() else []
    if not feat_files:
        missing.append("No Stage 8 feature tables found under 'data/processed/features/'.")

    return missing


def main(argv: Optional[List[str]] = None) -> int:
    setup_logging()
    args = parse_args(argv)
    root = project_root()
    task = args.task.lower()

    logger.info("=" * 70)
    logger.info("SOLARIS-A1 STAGE 9: DATASET EXPORT")
    logger.info("Task: %s", task.upper())
    logger.info("=" * 70)

    log_path = root / "results" / "exports" / "export_log.json"
    ts_now = datetime.now(timezone.utc).isoformat()

    # 1. Evaluate Prerequisites per Task
    if task == "detection":
        missing_prereqs = check_detection_prerequisites(root)
        blocked_file = root / "results" / "exports" / "BLOCKED_DETECTION.md"
        gate_name = "Gate G3 (Ground-Truth Labelling Policy)"
    else:
        missing_prereqs = check_prediction_prerequisites(root)
        blocked_file = root / "results" / "exports" / "BLOCKED_PREDICTION.md"
        gate_name = "Gate G6 (Pre-Flare Forecasting Policy)"

    if missing_prereqs:
        logger.error("Dataset export for %s is strictly BLOCKED pending %s:", task.upper(), gate_name)
        for p in missing_prereqs:
            logger.error("  - %s", p)

        # Write BLOCKED report
        blocked_content = (
            f"# DATASET EXPORT BLOCKED: {task.upper()} ({gate_name})\n\n"
            f"**Execution Timestamp:** `{ts_now}`  \n"
            f"**Task:** `{task}`  \n"
            f"**Status:** `BLOCKED — PREREQUISITES NOT MET`  \n\n"
            f"--- \n\n"
            f"## Missing Scientific Prerequisites:\n\n"
        )
        for p in missing_prereqs:
            blocked_content += f"- {p}\n"
        blocked_content += (
            f"\n--- \n\n"
            f"## Next Required Human Action:\n"
            f"1. Review and formally approve the labelling policy in `docs/`.\n"
            f"2. Confirm all pending decisions in `config/decisions.yaml` with status `APPROVED` and non-null values.\n"
            f"3. Place approved independent flare event records in `data/manifests/event_records_approved.csv`.\n"
            f"4. Re-run `python scripts/export_dataset.py --task {task}`.\n"
        )
        blocked_file.parent.mkdir(parents=True, exist_ok=True)
        blocked_file.write_text(blocked_content, encoding="utf-8")
        logger.info("Wrote BLOCKED report to: %s", blocked_file)

        # Record to export_log.json
        log_entry = {
            "timestamp_utc": ts_now,
            "task": task,
            "status": "BLOCKED",
            "gate": gate_name,
            "refusal_reasons": missing_prereqs,
            "blocked_report_path": str(blocked_file.relative_to(root)),
        }
        update_export_log(log_path, log_entry)
        return 1

    # 2. Prerequisites Met Branch (Live Export)
    # When all prerequisites are approved by human researcher:
    events_path = Path(args.events) if args.events else (root / "data" / "manifests" / "event_records_approved.csv")
    events_df = load_approved_events(events_path)

    features_root = Path(args.features_dir) if args.features_dir else (root / "data" / "processed" / "features")
    out_root = Path(args.out_dir) if args.out_dir else (root / "data" / "processed" / "datasets")

    # Load decisions and config
    with open(root / "config" / "decisions.yaml", "r", encoding="utf-8") as f:
        decs_yaml = yaml.safe_load(f) or {}

    policy_file = (root / "docs" / "08_labelling_policy.md") if task == "detection" else (root / "docs" / "22_forecasting_policy.md")
    policy_text = policy_file.read_text(encoding="utf-8")

    # Gather feature windows
    feat_paths = list(features_root.glob("**/window_features.csv"))
    idx_paths = list(features_root.glob("**/window_index.csv"))
    if not feat_paths:
        raise RuntimeError("No window_features.csv files found to export.")

    # Filter by cohort if requested
    if args.cohort == "pilot":
        feat_paths = [p for p in feat_paths if "20261018" in p.parent.name]
        idx_paths = [p for p in idx_paths if "20261018" in p.parent.name]
        events_df = events_df[events_df["event_id"].str.contains("20261018")].copy()
    elif args.cohort == "july2024":
        feat_paths = [p for p in feat_paths if "202407" in p.parent.name]
        idx_paths = [p for p in idx_paths if "202407" in p.parent.name]
        events_df = events_df[events_df["event_id"].str.contains("202407")].copy()

    feat_paths = sorted(feat_paths)
    idx_paths = sorted(idx_paths)

    logger.info("Exporting cohort '%s' with %d feature stems (%d events).", args.cohort, len(feat_paths), len(events_df))

    all_feat_list = [pd.read_csv(p) for p in feat_paths]
    all_idx_list = [pd.read_csv(p) for p in idx_paths]
    features_df = pd.concat(all_feat_list, ignore_index=True)
    window_index_df = pd.concat(all_idx_list, ignore_index=True)

    # Target parameters
    d15_val = decs_yaml.get("decisions", {}).get("D-15", {}).get("value", 10)
    min_events_req = int(d15_val) if d15_val else 10
    event_count = len(events_df["event_id"].unique()) if "event_id" in events_df.columns else len(events_df)

    if task == "detection":
        try:
            tol_sec = float(decs_yaml.get("decisions", {}).get("D-02", {}).get("value", 30.0))
        except (ValueError, TypeError):
            tol_sec = 30.0
        try:
            emb_sec = float(decs_yaml.get("decisions", {}).get("D-08", {}).get("value", 300.0))
        except (ValueError, TypeError):
            emb_sec = 300.0
        params = {
            "tolerance_seconds": tol_sec,
            "embargo_seconds": emb_sec,
            "min_overlap_fraction": 0.50,
            "min_coverage_fraction": 0.80,
        }
        labels_df = label_windows_detection(window_index=window_index_df, events=events_df, params=params)
    else:
        try:
            h_sec = float(decs_yaml.get("decisions", {}).get("D-07", {}).get("value", 300.0))
        except (ValueError, TypeError):
            h_sec = 300.0
        try:
            emb_sec = float(decs_yaml.get("decisions", {}).get("D-08", {}).get("value", 300.0))
        except (ValueError, TypeError):
            emb_sec = 300.0
        labels_df = prediction_target(
            window_index=window_index_df,
            onsets=events_df,
            horizon_seconds=h_sec,
            embargo_seconds=emb_sec,
        )

    decs_yaml["cohort"] = args.cohort
    export_path = export_dataset(
        task=task,
        features_df=features_df,
        labels_df=labels_df,
        window_index_df=window_index_df,
        out_root=out_root,
        config_snapshot=decs_yaml,
        policy_text=policy_text,
        event_count=event_count,
        min_events_required=min_events_req,
        export_id=args.export_id,
    )

    logger.info("Successfully exported %s dataset to: %s", task.upper(), export_path)

    log_entry = {
        "timestamp_utc": ts_now,
        "task": task,
        "status": "SUCCESS",
        "export_id": export_path.name,
        "export_path": str(export_path.relative_to(root)),
        "n_samples": len(labels_df),
        "n_positive": int((labels_df.iloc[:, 1] == 1).sum()),
        "n_verified_negative": int((labels_df.iloc[:, 1] == 0).sum()),
        "n_excluded_na": int(labels_df.iloc[:, 1].isna().sum()),
        "event_count": event_count,
    }
    update_export_log(log_path, log_entry)
    return 0


if __name__ == "__main__":
    sys.exit(main())
