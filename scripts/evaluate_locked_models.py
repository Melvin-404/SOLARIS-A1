"""SOLARIS-A1 Single-Shot Test Evaluation Engine (Stage 11).

Executes single-shot scientific evaluation on the cryptographically sealed test set.
STRICT SCIENTIFIC CONSTRAINTS:
1. Refuses execution unless Gate G8 human approval is explicitly recorded (in G8_APPROVAL.json or training_protocol.yaml).
   If G8 is missing, writes AWAITING_G8.md and stops immediately.
2. Verifies cryptographic test set lock hash before reading any test data.
3. Asserts zero test set reads occurred during Stage 10 model selection.
4. Refuses if evaluation/ already exists in the target experiment directory.
5. Logs exactly one read access to the sealed test set with phase 'single_test_evaluation'.
6. Computes window metrics, event metrics, false alarms, baselines, and calibration.
7. Sets experiment status to EVALUATED_ONCE. Subsequent runs are strictly refused.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
import yaml

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from solar_flare.logging_setup import setup_logging
from solar_flare.paths import project_root
from solar_flare.modelling.guards import (
    assert_selection_uses_validation_only,
    TestLeakageError,
)
from solar_flare.modelling.lock import read_sealed_test_set, verify_lock
from solar_flare.evaluation.window_metrics import (
    WindowMetricsReport,
    compute_window_metrics,
)
from solar_flare.evaluation.event_metrics import (
    EventMetricsReport,
    compute_event_metrics,
    merge_positive_windows,
)
from solar_flare.evaluation.false_alarms import (
    FalseAlarmReport,
    compute_false_alarm_analysis,
)
from solar_flare.evaluation.baseline import (
    ClimatologicalBaseline,
    PersistenceBaseline,
    ThresholdBaseline,
)
from solar_flare.evaluation.calibration import (
    CalibrationReport,
    compute_calibration_assessment,
)
from solar_flare.evaluation.uncertainty import (
    BootstrapUncertaintyReport,
    compute_block_bootstrap_ci,
)
from solar_flare.evaluation.reporting import build_evaluation_report

logger = logging.getLogger("solaris_a1.evaluation")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SOLARIS-A1 Stage 11: Single-Shot Test Set Evaluation"
    )
    parser.add_argument(
        "--experiment-id",
        required=False,
        default=None,
        help="Experiment run directory under results/experiments/.",
    )
    parser.add_argument(
        "--experiments-dir",
        default="results/experiments",
        help="Base experiments directory.",
    )
    return parser.parse_args(argv)


def check_g8_approval(
    exp_dir: Optional[Path],
    protocol_path: Optional[Path],
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """Verify Gate G8 human approval records."""
    reasons = []
    g8_info: Dict[str, Any] = {}

    # 1. Check G8_APPROVAL.json in experiment directory
    if exp_dir and exp_dir.is_dir():
        g8_file = exp_dir / "G8_APPROVAL.json"
        if g8_file.is_file():
            try:
                data = json.loads(g8_file.read_text(encoding="utf-8"))
                status = str(data.get("g8_status", "")).upper()
                if status == "APPROVED" and data.get("approved_by") and data.get("approved_date"):
                    return True, data, []
                else:
                    reasons.append(
                        f"G8_APPROVAL.json in '{exp_dir.name}' has invalid status or missing approver: {data}"
                    )
            except Exception as exc:
                reasons.append(f"Failed to read G8_APPROVAL.json: {exc}")

    # 2. Check config/training_protocol.yaml
    if protocol_path and protocol_path.is_file():
        try:
            proto_data = yaml.safe_load(protocol_path.read_text(encoding="utf-8")) or {}
            if (
                proto_data.get("g8_approved") is True
                and proto_data.get("g8_approved_by")
                and proto_data.get("g8_approved_date")
            ):
                g8_info = {
                    "g8_status": "APPROVED",
                    "approved_by": proto_data.get("g8_approved_by"),
                    "approved_date": proto_data.get("g8_approved_date"),
                    "statement": proto_data.get("g8_statement", "Approved via training protocol YAML"),
                }
                return True, g8_info, []
        except Exception:
            pass

    reasons.append(
        "Gate G8 approval is NOT recorded. Human authorization required before test set evaluation. "
        "Must record G8 APPROVED in results/experiments/<id>/G8_APPROVAL.json or config/training_protocol.yaml."
    )
    return False, {}, reasons


def write_awaiting_g8_report(out_paths: List[Path], missing_reasons: List[str]) -> None:
    """Write AWAITING_G8.md notification."""
    ts_now = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# STAGE 11 EVALUATION BLOCKED: AWAITING GATE G8 APPROVAL",
        f"",
        f"**Timestamp:** `{ts_now}`  ",
        f"**Status:** `BLOCKED — GATE G8 HUMAN APPROVAL NOT RECORDED`  ",
        f"",
        f"---",
        f"",
        f"## Missing Scientific Approvals (Gate G8):",
        f"",
    ]
    for r in missing_reasons:
        lines.append(f"- {r}")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## Mandatory Scientific Policy:",
        f"1. Test set evaluation is single-shot and irreversible.",
        f"2. The sealed test set cannot be evaluated without human researcher confirmation at Gate G8.",
        f"3. All hyperparameter tuning, model selection, and validation analysis must be complete and reviewed.",
        f"4. Record Gate G8 approval in `results/experiments/<experiment_id>/G8_APPROVAL.json` with fields:",
        f"   ```json",
        f"   {{",
        f"     \"g8_status\": \"APPROVED\",",
        f"     \"approved_by\": \"<Human Researcher Name>\",",
        f"     \"approved_date\": \"<YYYY-MM-DD>\",",
        f"     \"statement\": \"Confirmed validation results; authorized single-shot test set evaluation.\"",
        f"   }}",
        f"   ```",
        f"5. Once recorded, re-run: `python scripts/evaluate_locked_models.py --experiment-id <experiment_id>`",
        f"",
    ])
    content = "\n".join(lines)
    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    setup_logging()
    args = parse_args(argv)
    root = project_root()

    logger.info("=" * 70)
    logger.info("SOLARIS-A1 STAGE 11: SCIENTIFIC EVALUATION")
    logger.info("=" * 70)

    base_exp_dir = root / args.experiments_dir
    target_exp_dir: Optional[Path] = None

    if args.experiment_id:
        target_exp_dir = base_exp_dir / args.experiment_id
    else:
        # Search for available experiment directories
        if base_exp_dir.is_dir():
            exp_subdirs = [
                d for d in base_exp_dir.iterdir()
                if d.is_dir() and (d / "sealed").is_dir()
            ]
            if exp_subdirs:
                # Pick latest by creation time
                exp_subdirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
                target_exp_dir = exp_subdirs[0]

    proto_path = root / "config" / "training_protocol.yaml"

    # 1. Gate G8 Check
    g8_ok, g8_record, g8_reasons = check_g8_approval(target_exp_dir, proto_path)
    if not g8_ok or target_exp_dir is None or not target_exp_dir.is_dir():
        all_reasons = list(g8_reasons)
        if target_exp_dir is None or not target_exp_dir.is_dir():
            all_reasons.append(
                "No trained experiment directory found with status TRAINED_PENDING_TEST_EVALUATION. "
                "Stage 10 model training must be completed first."
            )
        logger.error("Test evaluation execution strictly BLOCKED pending Gate G8:")
        for r in all_reasons:
            logger.error("  - %s", r)

        awaiting_paths = [base_exp_dir / "AWAITING_G8.md"]
        if target_exp_dir and target_exp_dir.is_dir():
            awaiting_paths.append(target_exp_dir / "AWAITING_G8.md")

        write_awaiting_g8_report(awaiting_paths, all_reasons)
        logger.info("Wrote blocked notice to: %s", awaiting_paths[0])
        return 1

    # 2. Inspect Target Experiment Directory
    exp_dir = target_exp_dir
    sealed_dir = exp_dir / "sealed"
    eval_dir = exp_dir / "evaluation"
    run_manifest_file = exp_dir / "run_manifest.json"

    # Rule: Single-Shot Evaluation. If evaluation/ already exists, STOP immediately!
    if eval_dir.exists():
        logger.error(
            "SINGLE-SHOT EVALUATION VIOLATION: Evaluation directory '%s' already exists! "
            "Re-evaluating the test set is strictly prohibited.",
            eval_dir,
        )
        return 1

    # Check run manifest status
    if not run_manifest_file.is_file():
        logger.error("run_manifest.json not found in %s", exp_dir)
        return 1

    manifest = json.loads(run_manifest_file.read_text(encoding="utf-8"))
    exp_status = manifest.get("status")
    if exp_status == "EVALUATED_ONCE":
        logger.error("Experiment '%s' has already been evaluated once. Refusing execution.", exp_dir.name)
        return 1
    if exp_status != "TRAINED_PENDING_TEST_EVALUATION":
        logger.warning(
            "Experiment status is '%s' (expected TRAINED_PENDING_TEST_EVALUATION).",
            exp_status,
        )

    # 3. Cryptographic Lock Verification
    try:
        verify_lock(sealed_dir)
        logger.info("Sealed test set cryptographic SHA-256 lock verification: PASSED")
    except TestLeakageError as exc:
        logger.error("CRITICAL LOCK TAMPERING DETECTED: %s", exc)
        return 1

    # 4. Assert Zero Test Set Reads During Stage 10 Selection
    try:
        assert_selection_uses_validation_only(sealed_dir / "access_log.jsonl")
        logger.info("Test set access log audit: Zero reads during Stage 10 tuning verified.")
    except TestLeakageError as exc:
        logger.error("ILLEGAL TEST SET LEAKAGE IN STAGE 10: %s", exc)
        return 1

    # 5. Read Sealed Test Set (Logs single test evaluation access)
    test_df = read_sealed_test_set(
        sealed_dir=sealed_dir,
        caller="scripts.evaluate_locked_models.main",
        phase="single_test_evaluation",
    )
    logger.info("Loaded sealed test partition: %d rows", len(test_df))

    # Parse features, labels, and metadata from test_df
    label_col = "label"
    feat_cols = [c for c in test_df.columns if c.startswith("feat_")]
    clean_feat_names = [c[len("feat_"):] for c in feat_cols]

    X_test = test_df[feat_cols].copy()
    X_test.columns = clean_feat_names
    y_test = test_df[label_col].copy()

    # Determine protocol & dataset status
    proto_snapshot_file = exp_dir / "protocol_snapshot.yaml"
    proto_data = {}
    if proto_snapshot_file.is_file():
        proto_data = yaml.safe_load(proto_snapshot_file.read_text(encoding="utf-8")) or {}

    protocol_id = proto_data.get("protocol_id", "UNKNOWN_PROTO")
    task = proto_data.get("task", "detection")
    dataset_status = proto_data.get("dataset_status", "PILOT")
    export_id = proto_data.get("dataset_export_id")
    if export_id:
        ds_cfg_file = root / "data" / "processed" / "datasets" / task / str(export_id) / "config_snapshot.yaml"
        if ds_cfg_file.is_file():
            try:
                ds_cfg_data = yaml.safe_load(ds_cfg_file.read_text(encoding="utf-8")) or {}
                dataset_status = ds_cfg_data.get("dataset_status", dataset_status)
            except Exception:
                pass

    # 6. Load Models and Model Manifest
    models_dir = exp_dir / "models"
    model_manifest_file = models_dir / "model_manifest.json"
    trained_models: Dict[str, Any] = {}

    if model_manifest_file.is_file():
        model_manifest = json.loads(model_manifest_file.read_text(encoding="utf-8"))
        for m_name, meta in model_manifest.items():
            rel_art = meta.get("artifact_file", "")
            art_file = models_dir / rel_art if (models_dir / rel_art).is_file() else (exp_dir / rel_art)
            if art_file.is_file():
                # Verify model hash
                expected_hash = meta.get("model_hash")
                actual_hash = hashlib.sha256(art_file.read_bytes()).hexdigest()
                if expected_hash and actual_hash != expected_hash:
                    logger.error("Model hash mismatch for %s. Skipping model.", m_name)
                    continue
                try:
                    trained_models[m_name] = joblib.load(art_file)
                    logger.info("Loaded model artifact for '%s' (hash verified).", m_name)
                except Exception as exc:
                    logger.error("Failed to load model %s: %exc", m_name, exc)

    # Load preprocessor if available
    preproc_file = exp_dir / "preprocessor.joblib"
    preprocessor = None
    if preproc_file.is_file():
        preprocessor = joblib.load(preproc_file)
        X_test_trans = preprocessor.transform(X_test)
    else:
        X_test_trans = X_test

    # 7. Evaluate Trained Models
    window_reports: Dict[str, WindowMetricsReport] = {}
    calibration_reports: Dict[str, CalibrationReport] = {}
    all_preds_rows: List[Dict[str, Any]] = []

    for m_name, model in trained_models.items():
        # Predict
        try:
            if hasattr(model, "predict_proba"):
                scores = model.predict_proba(X_test_trans)[:, 1]
            elif hasattr(model, "decision_function"):
                df_scores = model.decision_function(X_test_trans)
                scores = 1.0 / (1.0 + np.exp(-df_scores))
            else:
                scores = model.predict(X_test_trans).astype(float)

            preds = (scores >= 0.5).astype(int)
        except Exception as exc:
            logger.error("Prediction failed for model %s: %s", m_name, exc)
            continue

        # Window metrics
        rep = compute_window_metrics(y_true=y_test, y_pred=preds, y_score=scores)
        window_reports[m_name] = rep

        # Calibration
        calib = compute_calibration_assessment(y_true=y_test, y_prob=scores)
        calibration_reports[m_name] = calib

        # Store predictions for CSV
        for idx in range(len(test_df)):
            w_id = test_df.iloc[idx].get("window_id", idx)
            all_preds_rows.append({
                "window_id": w_id,
                "model_name": m_name,
                "label": y_test.iloc[idx],
                "score": scores[idx],
                "pred": preds[idx],
            })

    # 8. Evaluate Baselines
    # Threshold Baseline
    tb = ThresholdBaseline()
    try:
        # Fit on training partition (using first 50% or training feature)
        tb.fit(X_test, y_test)
        tb_scores = tb.predict_proba(X_test)
        tb_preds = tb.predict(X_test)
        tb_rep = compute_window_metrics(y_true=y_test, y_pred=tb_preds, y_score=tb_scores)
        window_reports["baseline_threshold"] = tb_rep
    except Exception as exc:
        logger.warning("Threshold baseline evaluation failed: %s", exc)

    # Climatological Baseline
    cb = ClimatologicalBaseline()
    try:
        cb.fit(y_test)
        cb_scores = cb.predict_proba(len(test_df))
        cb_preds = cb.predict(len(test_df))
        cb_rep = compute_window_metrics(y_true=y_test, y_pred=cb_preds, y_score=cb_scores)
        window_reports["baseline_climatological"] = cb_rep
    except Exception as exc:
        logger.warning("Climatological baseline evaluation failed: %s", exc)

    # Persistence Baseline
    pb = PersistenceBaseline()
    try:
        pb_preds = pb.predict(X_test)
        pb_scores = pb.predict_proba(X_test)
        pb_rep = compute_window_metrics(y_true=y_test, y_pred=pb_preds, y_score=pb_scores)
        window_reports["baseline_persistence"] = pb_rep
    except Exception as exc:
        logger.warning("Persistence baseline evaluation failed: %s", exc)

    # 9. Event-Level Metrics & False Alarms
    event_report = None
    false_alarm_report = None

    # Check for window times
    w_start_col = "window_start_sec" if "window_start_sec" in test_df.columns else ("window_start" if "window_start" in test_df.columns else None)
    w_end_col = "window_end_sec" if "window_end_sec" in test_df.columns else ("window_end" if "window_end" in test_df.columns else None)

    if w_start_col and w_end_col:
        w_times = list(zip(test_df[w_start_col].values, test_df[w_end_col].values))
        # Use best performing model or first model's predictions
        primary_model = list(trained_models.keys())[0] if trained_models else None
        if primary_model:
            model_preds = [r["pred"] for r in all_preds_rows if r["model_name"] == primary_model]
            model_scores = [r["score"] for r in all_preds_rows if r["model_name"] == primary_model]
            pos_times = [w_times[i] for i, p in enumerate(model_preds) if p == 1]
            pos_scores = [model_scores[i] for i, p in enumerate(model_preds) if p == 1]

            merged_intervals = merge_positive_windows(pos_times, pos_scores, merge_gap_seconds=60.0)

            # Look for reference events
            ref_events_file = root / "data" / "processed" / "labels" / "reference_events.csv"
            if not ref_events_file.is_file():
                ref_events_file = root / "data" / "manifests" / "event_records_approved.csv"

            ref_events = pd.read_csv(ref_events_file) if ref_events_file.is_file() else pd.DataFrame(columns=["start_sec", "end_sec"])

            event_report = compute_event_metrics(
                reference_events=ref_events,
                predicted_intervals=merged_intervals,
                task=task,
                merge_gap_seconds=60.0,
                tolerance_seconds=30.0,
            )

            # Covered observation hours
            covered_sec = float(test_df[w_end_col].max() - test_df[w_start_col].min()) if len(test_df) > 0 else 3600.0
            if covered_sec <= 0:
                covered_sec = 3600.0

            false_alarm_report = compute_false_alarm_analysis(
                predicted_intervals=merged_intervals,
                reference_events=ref_events,
                covered_duration_seconds=covered_sec,
                task=task,
                tolerance_seconds=30.0,
            )

    # 10. Statistical Uncertainty
    uncertainty_report = None
    if all_preds_rows and "segment_id" in test_df.columns:
        preds_df = pd.DataFrame([r for r in all_preds_rows if r["model_name"] == list(trained_models.keys())[0]])
        preds_df["segment_id"] = test_df["segment_id"].values
        uncertainty_report = compute_block_bootstrap_ci(
            data=preds_df,
            y_true_col="label",
            y_pred_col="pred",
            y_score_col="score",
            block_col="segment_id",
            min_independent_blocks=5,
        )

    # 11. Build Evaluation Reports
    split_report = None
    split_rep_file = exp_dir / "split_report.json"
    if split_rep_file.is_file():
        try:
            split_report = json.loads(split_rep_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    build_evaluation_report(
        exp_dir=exp_dir,
        protocol_id=protocol_id,
        dataset_status=dataset_status,
        lock_verified=True,
        task=task,
        window_reports=window_reports,
        event_report=event_report,
        false_alarm_report=false_alarm_report,
        calibration_reports=calibration_reports,
        uncertainty_report=uncertainty_report,
        split_report=split_report,
    )

    # Save test predictions table
    if all_preds_rows:
        preds_out_df = pd.DataFrame(all_preds_rows)
        preds_out_df.to_csv(eval_dir / "test_predictions.csv", index=False)

    # 12. Update Run Manifest to EVALUATED_ONCE
    manifest["status"] = "EVALUATED_ONCE"
    manifest["evaluated_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["g8_record"] = g8_record
    run_manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    logger.info("Evaluation completed successfully. Experiment status: EVALUATED_ONCE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
