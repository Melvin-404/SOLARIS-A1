"""Integration tests for export CLI guards and policy enforcement (Stage 9).

Validates:
- Invoking scripts/export_dataset.py refuses under DRAFT policy with exit code 1.
- CLI generates BLOCKED markdown report with specific missing items.
- CLI updates results/exports/export_log.json with refusal reasons.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from solar_flare.paths import project_root
from scripts.export_dataset import main as export_cli_main


from solar_flare.labels.policy import LabellingNotApprovedError
from solar_flare.export.targets import ForecastingNotApprovedError


def test_export_cli_detection_refuses_under_draft(monkeypatch):
    """Verify that export CLI for detection refuses to execute when policy is in draft status."""
    def mock_refusal(*args, **kwargs):
        raise LabellingNotApprovedError("Gate G3 draft refusal: requires approval")

    monkeypatch.setattr("scripts.export_dataset.assert_labelling_approved", mock_refusal)
    exit_code = export_cli_main(["--task", "detection"])
    assert exit_code == 1

    root = project_root()
    blocked_file = root / "results" / "exports" / "BLOCKED_DETECTION.md"
    assert blocked_file.is_file(), "BLOCKED_DETECTION.md was not written"
    content = blocked_file.read_text(encoding="utf-8")
    assert "Gate G3" in content
    assert "BLOCKED — PREREQUISITES NOT MET" in content

    # Check export_log.json
    log_file = root / "results" / "exports" / "export_log.json"
    assert log_file.is_file()
    logs = json.loads(log_file.read_text(encoding="utf-8"))
    assert any(entry.get("task") == "detection" and entry.get("status") == "BLOCKED" for entry in logs)


def test_export_cli_prediction_refuses_under_draft(monkeypatch):
    """Verify that export CLI for prediction refuses to execute when policy is in draft status."""
    def mock_refusal(*args, **kwargs):
        raise ForecastingNotApprovedError("Gate G6 draft refusal: requires approval")

    monkeypatch.setattr("scripts.export_dataset.assert_forecasting_approved", mock_refusal)
    exit_code = export_cli_main(["--task", "prediction"])
    assert exit_code == 1

    root = project_root()
    blocked_file = root / "results" / "exports" / "BLOCKED_PREDICTION.md"
    assert blocked_file.is_file(), "BLOCKED_PREDICTION.md was not written"
    content = blocked_file.read_text(encoding="utf-8")
    assert "Gate G6" in content
    assert "BLOCKED — PREREQUISITES NOT MET" in content


def test_export_cli_detection_approved_workspace_passes():
    """Verify that export CLI for detection succeeds under current approved workspace."""
    exit_code = export_cli_main(["--task", "detection"])
    assert exit_code == 0
