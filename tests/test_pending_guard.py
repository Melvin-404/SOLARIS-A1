"""Unit tests for Stage 7 approval guard.

Tests that final mode (--final) refuses execution when D-14 / G1 / G2 are PENDING,
and that development mode runs with PROVISIONAL labeling.
All synthetic fixtures are named fixture_synthetic_*.
"""

from __future__ import annotations

from pathlib import Path
import pytest
import yaml

from scripts.run_preprocessing import check_approval_for_final


@pytest.fixture
def fixture_synthetic_pending_decisions(tmp_path: Path) -> Path:
    """Create a synthetic decisions register where D-14 is PENDING."""
    dec_file = tmp_path / "decisions.yaml"
    data = {
        "decisions": {
            "D-09": {"status": "PROVISIONAL", "approved_by": None},
            "D-10": {"status": "PROVISIONAL", "approved_by": None},
            "D-13": {"status": "PROVISIONAL", "approved_by": None},
            "D-14": {"status": "PENDING", "approved_by": None},
            "D-17": {"status": "PENDING", "approved_by": None},
        }
    }
    with open(dec_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f)
    return dec_file


@pytest.fixture
def fixture_synthetic_approved_decisions(tmp_path: Path) -> Path:
    """Create a synthetic decisions register where all required decisions are APPROVED."""
    dec_file = tmp_path / "decisions_approved.yaml"
    data = {
        "decisions": {
            "D-09": {"status": "APPROVED", "approved_by": "Researcher"},
            "D-10": {"status": "APPROVED", "approved_by": "Researcher"},
            "D-13": {"status": "APPROVED", "approved_by": "Researcher"},
            "D-14": {"status": "APPROVED", "approved_by": "Researcher"},
            "D-17": {"status": "APPROVED", "approved_by": "Researcher"},
        }
    }
    with open(dec_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f)
    return dec_file


def test_final_mode_refuses_when_pending(fixture_synthetic_pending_decisions, tmp_path: Path):
    """Verify that check_approval_for_final returns False and writes AWAITING_G4.md."""
    out_dir = tmp_path / "out"
    is_approved, missing = check_approval_for_final(fixture_synthetic_pending_decisions, out_dir=out_dir)

    assert is_approved is False
    assert len(missing) > 0
    assert any("D-14" in m for m in missing)

    awaiting_md = out_dir / "AWAITING_G4.md"
    assert awaiting_md.is_file()
    text = awaiting_md.read_text(encoding="utf-8")
    assert "Gate G4 Approval Pending" in text
    assert "D-14" in text


def test_final_mode_passes_when_all_approved(fixture_synthetic_approved_decisions, tmp_path: Path):
    """Verify that check_approval_for_final returns True when all decisions are approved."""
    out_dir = tmp_path / "out"
    is_approved, missing = check_approval_for_final(fixture_synthetic_approved_decisions, out_dir=out_dir)

    assert is_approved is True
    assert len(missing) == 0
