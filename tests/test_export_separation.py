"""Tests ensuring complete task separation between Detection and Prediction exports (Stage 9).

Validates:
- Detection and prediction datasets are exported to completely isolated subdirectories.
- Invalid or mixed task specifications raise DatasetExportError.
"""

from __future__ import annotations

from pathlib import Path
import pytest
import pandas as pd

from solar_flare.export.export import export_dataset, DatasetExportError


def test_export_separation_distinct_directories(tmp_path: Path):
    """Verify that detection and prediction exports reside in distinct directory hierarchies."""
    out_root = tmp_path / "datasets"

    features_df = pd.DataFrame({
        "window_id": ["w1"],
        "mean": [5.0],
    })
    det_labels_df = pd.DataFrame({
        "window_id": ["w1"],
        "label_detection": pd.Series([1], dtype="Int8"),
        "label_reason": ["TEST"],
    })
    pred_labels_df = pd.DataFrame({
        "window_id": ["w1"],
        "label_prediction": pd.Series([0], dtype="Int8"),
        "excluded_reason": [None],
    })
    window_index_df = pd.DataFrame({
        "window_id": ["w1"],
        "window_start": [0.0],
        "window_end": [60.0],
    })

    det_dir = export_dataset(
        task="detection",
        features_df=features_df,
        labels_df=det_labels_df,
        window_index_df=window_index_df,
        out_root=out_root,
        config_snapshot={},
        policy_text="pol",
    )

    pred_dir = export_dataset(
        task="prediction",
        features_df=features_df,
        labels_df=pred_labels_df,
        window_index_df=window_index_df,
        out_root=out_root,
        config_snapshot={},
        policy_text="pol",
    )

    assert det_dir != pred_dir
    assert "detection" in str(det_dir)
    assert "prediction" not in str(det_dir)
    assert "prediction" in str(pred_dir)
    assert "detection" not in str(pred_dir)


def test_invalid_task_raises_error(tmp_path: Path):
    """Verify that an invalid or unrecognized task raises DatasetExportError."""
    df = pd.DataFrame({"window_id": ["w1"], "mean": [5.0]})
    with pytest.raises(DatasetExportError, match="Invalid task"):
        export_dataset(
            task="unsupported_task",
            features_df=df,
            labels_df=df,
            window_index_df=df,
            out_root=tmp_path,
            config_snapshot={},
            policy_text="",
        )
