"""Static analysis and safety test ensuring EDA modules never write to datasets or label paths.

CRITICAL ARCHITECTURAL SAFEGUARD:
Exploratory data analysis must never generate labels, targets, or training datasets.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from solar_flare.paths import project_root


def test_static_scan_eda_modules_no_dataset_or_label_writes():
    """Verify that eda modules and scripts contain no write references to datasets or labels."""
    root = project_root()
    eda_dir = root / "src" / "solar_flare" / "eda"
    run_eda_script = root / "scripts" / "run_eda.py"

    py_files = list(eda_dir.glob("*.py")) + [run_eda_script]
    assert len(py_files) > 0, "No EDA python files found to scan"

    forbidden_patterns = [
        "data/processed/datasets",
        "data/processed/labels",
        "datasets/",
        "labels/",
        "to_csv(\"data/processed",
        "to_parquet(\"data/processed",
    ]

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            assert pattern not in content, (
                f"Forbidden path pattern '{pattern}' detected in {py_file.relative_to(root)}. "
                "EDA modules are strictly prohibited from writing to training or label locations."
            )


def test_no_files_exist_under_processed_datasets_or_labels():
    """Verify that no dataset or label files exist in the project directory."""
    root = project_root()
    forbidden_dirs = [
        root / "data" / "processed" / "datasets",
        root / "data" / "processed" / "labels",
        root / "results" / "labels" / "datasets",
    ]

    for d in forbidden_dirs:
        if d.is_dir():
            files = [item for item in d.rglob("*") if item.is_file() and item.name != "README.md"]
            assert not files, (
                f"Unexpected dataset or label file(s) found in {d.relative_to(root)}: {files}. "
                "Supervised datasets and flare labels must not be created."
            )
