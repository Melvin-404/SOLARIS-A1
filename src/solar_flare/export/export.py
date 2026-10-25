"""Dataset Export Engine for SOLARIS-A1 (Stage 9).

Performs strict, audited export of segregated feature matrices (X), target labels (y),
provenance metadata, exclusion tables, configuration snapshots, and data dictionaries.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Strict 1-to-1 join assertion between features and labels; any mismatch halts execution.
2. X_features.csv contains STRICTLY feature columns: NO identifiers, NO labels, NO timestamps.
3. Complete separation: Detection and Prediction targets NEVER share directories or tables.
4. Exclusions are explicitly preserved in exclusions.csv. <NA> labels are NEVER imputed or converted to 0.
5. If independent event count is below Decision D-15 threshold, dataset status is set to INSUFFICIENT
   and INSUFFICIENT.md is written, blocking main-experiment ML training while allowing PILOT evaluation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import numpy as np
import pandas as pd
import yaml

from solar_flare.export.dictionary import generate_data_dictionary


class DatasetExportError(RuntimeError):
    """Raised when dataset export encounters an unhandled integrity or validation error."""
    pass


PROHIBITED_FEATURE_COLUMNS: Set[str] = {
    "window_id",
    "label",
    "label_detection",
    "label_prediction",
    "label_reason",
    "excluded_reason",
    "file_stem",
    "segment_id",
    "window_start",
    "window_end",
    "min_time_used",
    "max_time_used",
    "start_index",
    "end_index",
    "quality_flag",
    "include_flag",
    "event_id",
    "next_onset_time",
    "seconds_to_next_onset",
    "ongoing_event_at_t0",
    "horizon_coverage_fraction",
    "policy_version",
    "baseline_reason",
}


def compute_export_id(task: str, config_snapshot: Dict[str, Any], policy_text: str) -> str:
    """Generate a deterministic, content-hashed export identifier.
    
    Parameters
    ----------
    task : str
        "detection" or "prediction"
    config_snapshot : dict
        Parameters and metadata
    policy_text : str
        Text of the approved policy
        
    Returns
    -------
    str
        Deterministic ID, e.g. "exp_det_a1b2c3d4e5"
    """
    prefix = "exp_det" if "det" in task.lower() else "exp_pred"
    combined = json.dumps(config_snapshot, sort_keys=True) + policy_text
    h = hashlib.sha256(combined.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{h}"


def export_dataset(
    task: str,
    features_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    window_index_df: pd.DataFrame,
    out_root: Union[Path, str],
    config_snapshot: Dict[str, Any],
    policy_text: str,
    event_count: int = 0,
    min_events_required: int = 10,
    policy_version: str = "1.0",
    export_id: Optional[str] = None,
) -> Path:
    """Export segregated dataset tables, metadata, and documentation.
    
    Parameters
    ----------
    task : str
        "detection" or "prediction"
    features_df : pd.DataFrame
        Window features table (must include window_id for joining).
    labels_df : pd.DataFrame
        Target labels table (must include window_id).
    window_index_df : pd.DataFrame
        Window metadata table (window_start, window_end, file_stem, segment_id, etc.).
    out_root : Path or str
        Base export root (e.g. data/processed/datasets).
    config_snapshot : dict
        Parameters and policy statuses snapshot.
    policy_text : str
        Text of approved policy.
    event_count : int
        Number of independent verified events present in dataset.
    min_events_required : int
        Minimum events required by Decision D-15 for main experiment.
    policy_version : str
        Policy version string.
    export_id : Optional[str]
        Explicit export identifier. If None, deterministic compute_export_id() is used.
        
    Returns
    -------
    Path
        Directory path of the completed export.
        
    Raises
    -------
    DatasetExportError
        If 1-to-1 join fails, tasks are mixed, or feature columns violate constraints.
    """
    task_clean = task.strip().lower()
    if task_clean not in {"detection", "prediction"}:
        raise DatasetExportError(f"Invalid task '{task}'. Must be 'detection' or 'prediction'.")

    # 1. Compute deterministic export_id and isolate directory
    if export_id is None:
        export_id = compute_export_id(task=task_clean, config_snapshot=config_snapshot, policy_text=policy_text)
    out_dir = Path(out_root) / task_clean / export_id

    # Complete separation assertion
    opp_task = "prediction" if task_clean == "detection" else "detection"
    if opp_task in str(out_dir).lower().split(str(Path(out_root)).lower())[-1]:
        raise DatasetExportError(f"Task separation violation: {task_clean} export path contains {opp_task}")

    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Strict 1-to-1 join assertion
    if "window_id" not in features_df.columns:
        raise DatasetExportError("features_df missing mandatory primary key 'window_id'.")
    if "window_id" not in labels_df.columns:
        raise DatasetExportError("labels_df missing mandatory primary key 'window_id'.")

    n_feat = len(features_df)
    n_lab = len(labels_df)
    if n_feat != n_lab:
        raise DatasetExportError(
            f"1-to-1 join count mismatch: features_df has {n_feat} rows, labels_df has {n_lab} rows."
        )

    feat_ids = set(features_df["window_id"])
    lab_ids = set(labels_df["window_id"])
    if feat_ids != lab_ids:
        missing_in_lab = len(feat_ids - lab_ids)
        missing_in_feat = len(lab_ids - feat_ids)
        raise DatasetExportError(
            f"1-to-1 join ID mismatch: {missing_in_lab} in features not labels; {missing_in_feat} in labels not features."
        )

    # Sort both by window_id for determinism
    feat_sorted = features_df.sort_values("window_id").reset_index(drop=True)
    lab_sorted = labels_df.sort_values("window_id").reset_index(drop=True)

    # 3. Extract and validate X_features
    # Feature columns: all columns in features_df except PROHIBITED_FEATURE_COLUMNS
    feature_cols = [c for c in feat_sorted.columns if c not in PROHIBITED_FEATURE_COLUMNS]
    if not feature_cols:
        raise DatasetExportError("No valid feature columns identified in features_df.")

    # Strict check: X must contain NO identifiers, timestamps, or labels
    illegal_cols = set(feature_cols).intersection(PROHIBITED_FEATURE_COLUMNS)
    if illegal_cols:
        raise DatasetExportError(f"Illegal columns detected in X_features: {illegal_cols}")

    X_features = feat_sorted[feature_cols].copy()

    # 4. Extract y_labels
    label_col = "label_detection" if task_clean == "detection" else "label_prediction"
    if label_col not in lab_sorted.columns:
        raise DatasetExportError(f"labels_df missing expected target column '{label_col}'.")

    reason_col = "label_reason" if "label_reason" in lab_sorted.columns else "excluded_reason"

    y_labels = pd.DataFrame({
        "window_id": lab_sorted["window_id"],
        "label": lab_sorted[label_col].astype("Int8"),
        "label_reason": lab_sorted[reason_col],
    })

    # 5. Extract metadata
    if window_index_df is not None and not window_index_df.empty:
        win_meta = window_index_df.sort_values("window_id").reset_index(drop=True)
        # Verify alignment
        if list(win_meta["window_id"]) != list(feat_sorted["window_id"]):
            win_meta = win_meta.set_index("window_id").loc[feat_sorted["window_id"]].reset_index()
    else:
        win_meta = pd.DataFrame({"window_id": feat_sorted["window_id"]})

    # Add matched event or onset information to metadata
    metadata = win_meta.copy()
    for extra_col in ["event_id", "next_onset_time", "seconds_to_next_onset", "ongoing_event_at_t0"]:
        if extra_col in lab_sorted.columns:
            metadata[extra_col] = lab_sorted[extra_col]

    # 6. Extract exclusions (all <NA> labels)
    na_mask = y_labels["label"].isna()
    exclusions = y_labels[na_mask].copy()
    # Add metadata to exclusions for auditability
    avail_meta_cols = [c for c in ["window_id", "segment_id", "window_start", "window_end"] if c in metadata.columns]
    exclusions = exclusions.merge(
        metadata[avail_meta_cols],
        on="window_id",
        how="left",
    )

    # Strict assertion: exclusions count == NA count
    if len(exclusions) != int(na_mask.sum()):
        raise DatasetExportError(
            f"Exclusions count ({len(exclusions)}) does not match NA count ({int(na_mask.sum())})."
        )

    # 7. Write CSV tables
    X_path = out_dir / "X_features.csv"
    y_path = out_dir / "y_labels.csv"
    meta_path = out_dir / "metadata.csv"
    excl_path = out_dir / "exclusions.csv"

    X_features.to_csv(X_path, index=False)
    y_labels.to_csv(y_path, index=False)
    metadata.to_csv(meta_path, index=False)
    exclusions.to_csv(excl_path, index=False)

    # 8. Write config snapshot
    full_config = {
        "export_id": export_id,
        "task": task_clean,
        "policy_version": policy_version,
        "n_samples_total": len(y_labels),
        "n_positive": int((y_labels["label"] == 1).sum()),
        "n_verified_negative": int((y_labels["label"] == 0).sum()),
        "n_excluded_na": int(na_mask.sum()),
        "n_features": len(feature_cols),
        "feature_columns": feature_cols,
        "independent_event_count": event_count,
        "d15_minimum_required": min_events_required,
        "dataset_status": "APPROVED-main" if event_count >= min_events_required else "INSUFFICIENT",
        "parameters": config_snapshot,
    }
    config_path = out_dir / "config_snapshot.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(full_config, f, sort_keys=False)

    # 9. Generate and write data dictionary
    dict_content = generate_data_dictionary(
        task=task_clean,
        feature_names=feature_cols,
        config_params=config_snapshot,
        policy_version=policy_version,
    )
    (out_dir / "data_dictionary.md").write_text(dict_content, encoding="utf-8")

    # 10. Check Decision D-15 Event Count & write INSUFFICIENT.md if below threshold
    if event_count < min_events_required:
        insufficient_report = (
            f"# DATASET STATUS: INSUFFICIENT (Decision D-15)\n\n"
            f"**Export ID:** `{export_id}`  \n"
            f"**Task:** `{task_clean}`  \n"
            f"**Observed Independent Events:** `{event_count}`  \n"
            f"**Decision D-15 Minimum Required:** `{min_events_required}`  \n\n"
            f"--- \n\n"
            f"## Governance & Scientific Safety Enforcement:\n"
            f"The number of independent verified solar flare events in this dataset ({event_count})\n"
            f"is strictly below the minimum threshold ({min_events_required}) stipulated by Decision D-15\n"
            f"for conducting the main machine learning experiment.\n\n"
            f"### Training Permissions:\n"
            f"- **Main Experiment ML Training:** **STRICTLY BLOCKED.** Model evaluation on this dataset cannot\n"
            f"  yield statistically credible solar flare detection or forecasting performance claims.\n"
            f"- **PILOT Pipeline Verification:** **PERMITTED.** The dataset may be used solely as a PILOT dataset\n"
            f"  to verify data ingestion, model pipeline syntax, and metric calculation workflows.\n"
        )
        (out_dir / "INSUFFICIENT.md").write_text(insufficient_report, encoding="utf-8")

    return out_dir
