"""Unit tests for evaluation reporting and single-shot governance (Stage 11).

Tests:
1. build_evaluation_report refuses execution if test set lock verification failed.
2. build_evaluation_report refuses execution if evaluation/ directory already exists.
3. Successful generation produces metrics.csv, evaluation_report.json, evaluation_report.md, and dashboard_contract.json.
"""

from pathlib import Path
import pytest
from solar_flare.evaluation.reporting import build_evaluation_report
from solar_flare.evaluation.window_metrics import compute_window_metrics


def test_reporting_refuses_without_lock_verification(tmp_path: Path):
    """Verify that build_evaluation_report raises RuntimeError if lock verification failed."""
    exp_dir = tmp_path / "exp_test"
    exp_dir.mkdir()

    rep = compute_window_metrics([1, 0], [1, 0])
    with pytest.raises(RuntimeError, match="lock verification failed"):
        build_evaluation_report(
            exp_dir=exp_dir,
            protocol_id="PROTO_01",
            dataset_status="PILOT",
            lock_verified=False,  # Failed verification
            task="detection",
            window_reports={"model_lr": rep},
        )


def test_reporting_refuses_if_evaluation_directory_exists(tmp_path: Path):
    """Verify that build_evaluation_report raises FileExistsError if evaluation/ already exists."""
    exp_dir = tmp_path / "exp_test"
    eval_dir = exp_dir / "evaluation"
    eval_dir.mkdir(parents=True)

    rep = compute_window_metrics([1, 0], [1, 0])
    with pytest.raises(FileExistsError, match="SINGLE-SHOT EVALUATION VIOLATION"):
        build_evaluation_report(
            exp_dir=exp_dir,
            protocol_id="PROTO_01",
            dataset_status="PILOT",
            lock_verified=True,
            task="detection",
            window_reports={"model_lr": rep},
            force_overwrite=False,
        )


def test_successful_reporting_artifacts(tmp_path: Path):
    """Verify creation and completeness of all required evaluation artifacts."""
    exp_dir = tmp_path / "exp_clean"
    exp_dir.mkdir()

    rep = compute_window_metrics([1, 0, 1, 0], [1, 0, 0, 0], [0.8, 0.2, 0.4, 0.1])
    eval_path = build_evaluation_report(
        exp_dir=exp_dir,
        protocol_id="PROTO_01",
        dataset_status="PILOT",
        lock_verified=True,
        task="detection",
        window_reports={"model_rf": rep},
    )

    assert (eval_path / "metrics.csv").is_file()
    assert (eval_path / "evaluation_report.json").is_file()
    assert (eval_path / "evaluation_report.md").is_file()
    assert (eval_path / "dashboard_contract.json").is_file()

    md_content = (eval_path / "evaluation_report.md").read_text(encoding="utf-8")
    assert "Interpretation is the responsibility of the human researcher." in md_content
    assert "PILOT" in md_content
