"""Tests for dataset export engine (Stage 9).

Validates:
- Strict 1-to-1 join assertion between features and labels
- X_features contains NO identifiers, labels, or timestamps
- exclusions.csv row count equals <NA> count in y_labels.csv
- Deterministic export_id computation
- INSUFFICIENT.md written when independent event count is below Decision D-15
"""

from __future__ import annotations

from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import yaml

from solar_flare.export.export import export_dataset, compute_export_id, DatasetExportError


@pytest.fixture
def synthetic_export_data():
    """Create minimal valid synthetic tables for dataset export testing."""
    n_rows = 10
    win_ids = [f"win_{i:04d}" for i in range(n_rows)]

    features_df = pd.DataFrame({
        "window_id": win_ids,
        "mean": np.linspace(10.0, 20.0, n_rows),
        "std": np.ones(n_rows),
        "median": np.linspace(10.0, 20.0, n_rows),
        "temporal_slope": np.zeros(n_rows),
    })

    # Labels: 2 positive, 6 negative, 2 NA
    labels = [1, 1, 0, 0, 0, 0, 0, 0, pd.NA, pd.NA]
    reasons = [
        "MATCHED_EVENT_01", "MATCHED_EVENT_02",
        "VERIFIED_QUIET", "VERIFIED_QUIET", "VERIFIED_QUIET",
        "VERIFIED_QUIET", "VERIFIED_QUIET", "VERIFIED_QUIET",
        "EMBARGO_EXCLUDED", "LOW_COVERAGE_EXCLUDED",
    ]

    labels_df = pd.DataFrame({
        "window_id": win_ids,
        "label_detection": pd.Series(labels, dtype="Int8"),
        "label_reason": reasons,
    })

    window_index_df = pd.DataFrame({
        "window_id": win_ids,
        "file_stem": ["STEM_01"] * n_rows,
        "segment_id": ["SEG_01"] * n_rows,
        "window_start": [float(i * 10) for i in range(n_rows)],
        "window_end": [float(i * 10 + 60) for i in range(n_rows)],
        "coverage_fraction": [1.0] * 8 + [0.5] * 2,
        "quality_flag": ["OK"] * 8 + ["LOW_COVERAGE"] * 2,
    })

    config_snapshot = {"window_seconds": 60.0, "stride_seconds": 10.0}
    policy_text = "Approved policy mock text"

    return features_df, labels_df, window_index_df, config_snapshot, policy_text


def test_export_successful_generation(synthetic_export_data, tmp_path: Path):
    """Verify that a valid export creates all required files with proper segregation."""
    feat_df, lab_df, idx_df, cfg, pol = synthetic_export_data

    out_root = tmp_path / "datasets"
    export_dir = export_dataset(
        task="detection",
        features_df=feat_df,
        labels_df=lab_df,
        window_index_df=idx_df,
        out_root=out_root,
        config_snapshot=cfg,
        policy_text=pol,
        event_count=2,
        min_events_required=10,  # Below threshold -> triggers INSUFFICIENT
    )

    assert export_dir.is_dir()
    assert (export_dir / "X_features.csv").is_file()
    assert (export_dir / "y_labels.csv").is_file()
    assert (export_dir / "metadata.csv").is_file()
    assert (export_dir / "exclusions.csv").is_file()
    assert (export_dir / "config_snapshot.yaml").is_file()
    assert (export_dir / "data_dictionary.md").is_file()
    assert (export_dir / "INSUFFICIENT.md").is_file()

    # 1. Verify X_features has NO identifier or label columns
    X = pd.read_csv(export_dir / "X_features.csv")
    assert len(X) == 10
    assert "window_id" not in X.columns
    assert "label" not in X.columns
    assert "file_stem" not in X.columns
    assert "window_start" not in X.columns
    assert set(X.columns) == {"mean", "std", "median", "temporal_slope"}

    # 2. Verify y_labels has window_id, label, label_reason
    y = pd.read_csv(export_dir / "y_labels.csv")
    assert len(y) == 10
    assert list(y.columns) == ["window_id", "label", "label_reason"]
    assert y["label"].isna().sum() == 2

    # 3. Verify exclusions count equals NA count
    excl = pd.read_csv(export_dir / "exclusions.csv")
    assert len(excl) == 2
    assert set(excl["window_id"]) == {"win_0008", "win_0009"}


def test_export_one_to_one_mismatch_raises(synthetic_export_data, tmp_path: Path):
    """Verify that a mismatch in row counts or window_ids raises DatasetExportError."""
    feat_df, lab_df, idx_df, cfg, pol = synthetic_export_data

    # Drop one row from labels
    truncated_lab = lab_df.iloc[:-1].copy()

    with pytest.raises(DatasetExportError, match="1-to-1 join count mismatch"):
        export_dataset(
            task="detection",
            features_df=feat_df,
            labels_df=truncated_lab,
            window_index_df=idx_df,
            out_root=tmp_path,
            config_snapshot=cfg,
            policy_text=pol,
        )


def test_export_deterministic_id(synthetic_export_data):
    """Verify that export_id is deterministic and changes when config changes."""
    _, _, _, cfg, pol = synthetic_export_data

    id1 = compute_export_id("detection", cfg, pol)
    id2 = compute_export_id("detection", cfg, pol)
    assert id1 == id2

    # Change config
    cfg_altered = {"window_seconds": 120.0, "stride_seconds": 10.0}
    id3 = compute_export_id("detection", cfg_altered, pol)
    assert id1 != id3
