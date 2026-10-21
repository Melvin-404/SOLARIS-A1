"""SOLARIS-A1 Automated Model Training CLI (Stage 10).

Executes reproducible, protocol-guarded model training and validation-only hyperparameter tuning.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Strictly refuses execution unless config/training_protocol.yaml has status FROZEN or PILOT,
   formally approved with approved_by and approved_date by the human researcher (Gate G7).
2. Seals the test set BEFORE any selection or tuning starts. Test data is never scored or tuned on.
3. Preprocessors are fitted strictly on training data; validation or test indices raise TestLeakageError.
4. Model evaluation on the test set is strictly DEFERRED to Stage 11 under Gate G8.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import platform
import sys
from typing import Any, Dict, List, Optional
import yaml
import numpy as np
import pandas as pd

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from solar_flare.logging_setup import setup_logging
from solar_flare.paths import project_root
from solar_flare.modelling.guards import (
    assert_protocol_frozen,
    assert_no_test_in_fit,
    assert_selection_uses_validation_only,
    ProtocolNotFrozenError,
    TestLeakageError,
)
from solar_flare.modelling.splits import chronological_split, event_grouped_split
from solar_flare.modelling.lock import seal_test_set, verify_lock
from solar_flare.modelling.preprocessing_fit import TrainingOnlyPreprocessor
from solar_flare.modelling.training import run_selection

logger = logging.getLogger("solaris_a1.training")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SOLARIS-A1 Stage 10: Protocol-Guarded Model Training"
    )
    parser.add_argument(
        "--protocol",
        default="config/training_protocol.yaml",
        help="Path to training protocol YAML.",
    )
    parser.add_argument(
        "--experiments-dir",
        default="results/experiments",
        help="Destination directory for experiment runs.",
    )
    return parser.parse_args(argv)


def write_awaiting_g7_report(out_path: Path, missing_reasons: List[str]) -> None:
    """Generate results/experiments/AWAITING_G7.md report."""
    ts_now = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# STAGE 10 TRAINING BLOCKED: AWAITING GATE G7 APPROVAL",
        f"",
        f"**Timestamp:** `{ts_now}`  ",
        f"**Status:** `BLOCKED — GATE G7 PROTOCOL NOT FROZEN`  ",
        f"",
        f"---",
        f"",
        f"## Missing Scientific Approvals (Gate G7):",
        f"",
    ]
    for r in missing_reasons:
        lines.append(f"- {r}")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## Next Required Human Action:",
        f"1. Review `config/training_protocol.yaml`.",
        f"2. Confirm splitting strategy (chronological vs event-grouped), embargo buffer, model search spaces, and selection metric.",
        f"3. Change status from `DRAFT` to `FROZEN` (for main experiment) or `PILOT` (for pilot run).",
        f"4. Record `approved_by: <name>` and `approved_date: <YYYY-MM-DD>`.",
        f"5. Ensure Stage 9 dataset export has completed for the target task.",
        f"6. Re-run `python scripts/train_models.py --protocol config/training_protocol.yaml`.",
        f"",
    ])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    setup_logging()
    args = parse_args(argv)
    root = project_root()

    logger.info("=" * 70)
    logger.info("SOLARIS-A1 STAGE 10: AUTOMATED MODEL TRAINING")
    logger.info("=" * 70)

    proto_path = Path(args.protocol)
    if not proto_path.is_absolute():
        proto_path = root / proto_path

    # 1. Inspect and Assert Training Protocol
    if not proto_path.is_file():
        logger.error("Training protocol not found: %s", proto_path)
        write_awaiting_g7_report(
            root / "results" / "experiments" / "AWAITING_G7.md",
            [f"Training protocol file '{proto_path.name}' does not exist."],
        )
        return 1

    with open(proto_path, "r", encoding="utf-8") as f:
        protocol = yaml.safe_load(f) or {}

    missing_reasons = []
    try:
        assert_protocol_frozen(protocol, protocol_path=proto_path)
    except ProtocolNotFrozenError as exc:
        missing_reasons.append(str(exc))

    # 2. Check Dataset Availability & Hashes
    dataset_hashes_file = root / "results" / "experiments" / "dataset_hashes.json"
    dataset_info = {}
    if dataset_hashes_file.is_file():
        try:
            dataset_info = json.loads(dataset_hashes_file.read_text(encoding="utf-8"))
        except Exception:
            dataset_info = {}

    if not dataset_info.get("datasets_present", False):
        missing_reasons.append(
            "Stage 9 dataset export is missing or blocked. No exported datasets found in data/processed/datasets/."
        )

    if missing_reasons:
        logger.error("Training execution strictly BLOCKED pending Gate G7:")
        for r in missing_reasons:
            logger.error("  - %s", r)
        awaiting_file = root / "results" / "experiments" / "AWAITING_G7.md"
        write_awaiting_g7_report(awaiting_file, missing_reasons)
        logger.info("Wrote blocked notice to: %s", awaiting_file)
        return 1

    # 3. Live Training Execution Branch (Exercised when Gate G7 is approved)
    proto_id = protocol.get("protocol_id", "PROTO_001")
    task = protocol.get("task", "detection")
    export_id = protocol.get("dataset_export_id")

    exp_id = f"exp_{proto_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    exp_dir = root / args.experiments_dir / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    # Copy protocol snapshot and compute protocol hash
    proto_raw = proto_path.read_text(encoding="utf-8")
    proto_hash = hashlib.sha256(proto_raw.encode("utf-8")).hexdigest()[:16]
    (exp_dir / "protocol_snapshot.yaml").write_text(proto_raw, encoding="utf-8")

    # Load dataset
    ds_root = root / "data" / "processed" / "datasets" / task / str(export_id)
    X_full = pd.read_csv(ds_root / "X_features.csv")
    y_full = pd.read_csv(ds_root / "y_labels.csv")
    meta_full = pd.read_csv(ds_root / "metadata.csv")

    # Filter unverified NA labels for training/validation
    valid_mask = ~y_full["label"].isna()
    X_valid = X_full[valid_mask].reset_index(drop=True)
    y_valid = y_full[valid_mask]["label"].astype(int).reset_index(drop=True)
    meta_valid = meta_full[valid_mask].reset_index(drop=True)

    # 4. Partition Split
    strategy = protocol.get("split_strategy", "chronological")
    split_params = protocol.get("split_parameters", {})

    if strategy == "chronological":
        train_idx, val_idx, test_idx, split_rep = chronological_split(
            metadata=meta_valid,
            train_end=split_params["train_end"],
            val_end=split_params["val_end"],
            embargo_seconds=split_params.get("embargo_seconds", 300.0),
            labels=y_valid,
        )
    else:
        train_idx, val_idx, test_idx, split_rep = event_grouped_split(
            metadata=meta_valid,
            group_col=split_params.get("group_column", "segment_id"),
            fractions=split_params.get("fractions", (0.60, 0.20, 0.20)),
            random_state=split_params.get("random_state", 42),
            embargo_seconds=split_params.get("embargo_seconds", 0.0),
            labels=y_valid,
        )

    # Write split reports
    (exp_dir / "split_report.json").write_text(json.dumps(split_rep.to_dict(), indent=2), encoding="utf-8")

    # 5. Cryptographically Seal Test Set BEFORE tuning
    X_test = X_valid.iloc[test_idx].reset_index(drop=True)
    y_test = pd.DataFrame({"label": y_valid.iloc[test_idx].values})
    meta_test = meta_valid.iloc[test_idx].reset_index(drop=True)

    seal_record = seal_test_set(
        X_test=X_test,
        y_test=y_test,
        metadata_test=meta_test,
        out_dir=exp_dir,
        protocol_hash=proto_hash,
        dataset_export_id=str(export_id),
    )
    logger.info("Sealed test partition with %d samples (SHA-256: %s)", seal_record["row_count"], seal_record["sha256"])

    # 6. Fit Preprocessor on Training Only
    prep_cfg = protocol.get("preprocessing", {})
    preprocessor = TrainingOnlyPreprocessor(
        scaler=prep_cfg.get("scaler", "StandardScaler"),
        imputer=prep_cfg.get("imputer", "NONE"),
        feature_selection=prep_cfg.get("feature_selection", "NONE"),
    )
    preprocessor.fit(
        X=X_valid,
        y=y_valid,
        fit_indices=train_idx,
        val_indices=val_idx,
        test_indices=test_idx,
    )

    X_train_trans = preprocessor.transform(X_valid.iloc[train_idx])
    y_train = y_valid.iloc[train_idx]

    X_val_trans = preprocessor.transform(X_valid.iloc[val_idx])
    y_val = y_valid.iloc[val_idx]

    # Save preprocessor artifact
    joblib.dump(preprocessor, exp_dir / "preprocessor.joblib")

    # 7. Model Selection on Validation Only
    selection_results = run_selection(
        protocol=protocol,
        X_train=X_train_trans,
        y_train=y_train,
        X_val=X_val_trans,
        y_val=y_val,
        out_dir=exp_dir,
    )

    # 8. Post-Selection Access Guard
    verify_lock(exp_dir / "sealed")
    assert_selection_uses_validation_only(exp_dir / "sealed" / "access_log.jsonl")

    # 9. Record Environment & Run Manifest
    env_info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "sklearn_version": __import__("sklearn").__version__,
        "xgboost_version": getattr(__import__("xgboost"), "__version__", "UNAVAILABLE"),
        "joblib_version": joblib.__version__,
    }
    (exp_dir / "environment.json").write_text(json.dumps(env_info, indent=2), encoding="utf-8")

    manifest = {
        "experiment_id": exp_id,
        "protocol_id": proto_id,
        "status": "TRAINED_PENDING_TEST_EVALUATION",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_export_id": export_id,
        "test_lock_status": "SEALED",
        "selected_models": selection_results,
    }
    (exp_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    logger.info("Stage 10 model training completed successfully. Experiment status: TRAINED_PENDING_TEST_EVALUATION.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
