"""Unit tests for single-shot evaluation enforcement (Stage 11).

Tests:
1. First evaluation invocation on an approved synthetic experiment runs and generates artifacts.
2. Second invocation on the same experiment directory is strictly refused.
"""

import json
from pathlib import Path
import pytest
from scripts.evaluate_locked_models import main as evaluate_main
from solar_flare.modelling.lock import seal_test_set
import pandas as pd
import numpy as np


@pytest.fixture
def fixture_synthetic_experiment(tmp_path: Path) -> Path:
    """Create a fully structured synthetic Stage 10 experiment directory with Gate G8 approval."""
    exp_dir = tmp_path / "exp_synthetic_stage10"
    exp_dir.mkdir(parents=True)

    # 1. Gate G8 approval file
    g8_file = exp_dir / "G8_APPROVAL.json"
    g8_file.write_text(json.dumps({
        "g8_status": "APPROVED",
        "approved_by": "Dr. Test Researcher",
        "approved_date": "2026-10-21",
        "statement": "Authorization granted for single-shot test evaluation.",
    }), encoding="utf-8")

    # 2. Protocol snapshot
    proto_file = exp_dir / "protocol_snapshot.yaml"
    proto_file.write_text("protocol_id: PROTO_SYNTH_01\ntask: detection\nstatus: FROZEN\n", encoding="utf-8")

    # 3. Sealed test partition
    X_test = pd.DataFrame({
        "ratio_to_base": [1.1, 4.5, 0.9, 5.2],
        "flux_mean": [10.0, 50.0, 12.0, 55.0],
    })
    y_test = pd.DataFrame({"label": [0, 1, 0, 1]})
    meta_test = pd.DataFrame({
        "window_id": ["W01", "W02", "W03", "W04"],
        "window_start_sec": [1000.0, 1100.0, 1200.0, 1300.0],
        "window_end_sec": [1060.0, 1160.0, 1260.0, 1360.0],
        "segment_id": ["seg_01", "seg_01", "seg_02", "seg_02"],
    })

    seal_test_set(
        X_test=X_test,
        y_test=y_test,
        metadata_test=meta_test,
        out_dir=exp_dir,
        protocol_hash="hash123",
        dataset_export_id="export_synth",
    )

    # 4. Models directory and mock manifest
    models_dir = exp_dir / "models"
    models_dir.mkdir()
    manifest_file = models_dir / "model_manifest.json"
    manifest_file.write_text(json.dumps({}), encoding="utf-8")

    # 5. Run manifest
    run_manifest = exp_dir / "run_manifest.json"
    run_manifest.write_text(json.dumps({
        "status": "TRAINED_PENDING_TEST_EVALUATION",
        "experiment_id": exp_dir.name,
    }), encoding="utf-8")

    return exp_dir


def test_single_shot_evaluation_enforcement(fixture_synthetic_experiment: Path):
    """Verify that first invocation evaluates successfully and second invocation strictly refuses."""
    exp_dir = fixture_synthetic_experiment
    parent_dir = exp_dir.parent

    # 1. First invocation: Should succeed (return code 0)
    ret_first = evaluate_main([
        "--experiment-id", exp_dir.name,
        "--experiments-dir", str(parent_dir),
    ])
    assert ret_first == 0

    # Verify evaluation directory and status
    eval_dir = exp_dir / "evaluation"
    assert eval_dir.is_dir()
    assert (eval_dir / "metrics.csv").is_file()

    manifest = json.loads((exp_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "EVALUATED_ONCE"

    # 2. Second invocation on same experiment: Must strictly refuse (return non-zero)
    ret_second = evaluate_main([
        "--experiment-id", exp_dir.name,
        "--experiments-dir", str(parent_dir),
    ])
    assert ret_second != 0
