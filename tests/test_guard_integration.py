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


def test_export_cli_detection_refuses_under_draft():
    """Verify that export CLI for detection refuses to execute on current unapproved workspace."""
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


def test_export_cli_prediction_refuses_under_draft():
    """Verify that export CLI for prediction refuses to execute on current unapproved workspace."""
    exit_code = export_cli_main(["--task", "prediction"])
    assert exit_code == 1

    root = project_root()
    blocked_file = root / "results" / "exports" / "BLOCKED_PREDICTION.md"
    assert blocked_file.is_file(), "BLOCKED_PREDICTION.md was not written"
    content = blocked_file.read_text(encoding="utf-8")
    assert "Gate G6" in content
    assert "BLOCKED — PREREQUISITES NOT MET" in content
