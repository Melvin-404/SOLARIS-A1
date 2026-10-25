"""Unit tests for solar_flare.labels.policy module.

Tests the Gate G3 human approval guard.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest
import yaml

from solar_flare.labels.policy import assert_labelling_approved, LabellingNotApprovedError
from solar_flare.labels.generate import generate_window_labels


@pytest.fixture
def fixture_synthetic_approved_setup(tmp_path: Path):
    """Create synthetic approved policy markdown and decisions.yaml in tmp_path."""
    policy_file = tmp_path / "08_labelling_policy.md"
    policy_file.write_text(
        "# Labelling Policy\n\nStatus: APPROVED by Dr. Solar Researcher, date 2026-10-21\n\nApproved content.",
        encoding="utf-8"
    )

    decisions_file = tmp_path / "decisions.yaml"
    decisions_content = {
        "decisions": {
            "D-01": {"status": "APPROVED", "value": "SRC_NOAA_NCEI_GOES", "approved_by": "Researcher"},
            "D-02": {"status": "APPROVED", "value": 30.0, "approved_by": "Researcher"},
            "D-03": {"status": "APPROVED", "value": "OFFICIAL_CATALOG_START_END", "approved_by": "Researcher"},
            "D-04": {"status": "APPROVED", "value": "EXCLUDE_PARTIAL_WINDOWS", "approved_by": "Researcher"},
            "D-08": {"status": "APPROVED", "value": "EMBARGO_30M_PRE_60M_POST", "approved_by": "Researcher"},
            "D-10": {"status": "APPROVED", "value": "UNIX_EPOCH_SECONDS_MJD_40587", "approved_by": "Researcher"},
            "D-15": {"status": "APPROVED", "value": 20, "approved_by": "Researcher"},
        }
    }
    with open(decisions_file, "w", encoding="utf-8") as f:
        yaml.dump(decisions_content, f)

    return policy_file, decisions_file


def test_real_draft_policy_raises_guard_refusal(tmp_path: Path):
    """Verify that assert_labelling_approved on draft policy or pending decisions raises LabellingNotApprovedError."""
    draft_policy = tmp_path / "08_labelling_policy.md"
    draft_policy.write_text("# Labelling Policy\n\nStatus: DRAFT — REQUIRES HUMAN APPROVAL\n", encoding="utf-8")
    draft_dec = tmp_path / "decisions.yaml"
    draft_dec.write_text("decisions:\n  D-01:\n    status: PENDING\n    value: null\n", encoding="utf-8")
    with pytest.raises(LabellingNotApprovedError) as exc_info:
        assert_labelling_approved(policy_path=draft_policy, decisions_path=draft_dec)
    assert "Supervised labelling is strictly BLOCKED" in str(exc_info.value)
    assert "D-01" in str(exc_info.value)


def test_repository_approved_policy_passes():
    """Verify that assert_labelling_approved on the active repository files passes Gate G3."""
    assert assert_labelling_approved() is True



def test_synthetic_approved_setup_passes(fixture_synthetic_approved_setup):
    """Verify that complete approved policy and decisions pass the guard and allow generation."""
    policy_file, decisions_file = fixture_synthetic_approved_setup
    assert assert_labelling_approved(policy_path=policy_file, decisions_path=decisions_file) is True

    # Exercise non-refusal branch of label generator
    windows_df = pd.DataFrame([
        {"window_id": "W001", "start_time": 1000.0, "end_time": 1060.0},
        {"window_id": "W002", "start_time": 2000.0, "end_time": 2060.0},
    ])
    events_df = pd.DataFrame([
        {"event_id": "FLARE_1", "onset_time": 1010.0, "end_time": 1050.0},
    ])

    labeled = generate_window_labels(
        windows_df,
        events_df,
        tolerance_seconds=10.0,
        policy_path=policy_file,
        decisions_path=decisions_file,
        min_overlap_fraction=0.5,
    )
    assert len(labeled) == 2
    assert labeled.iloc[0]["label"] == 1
    assert labeled.iloc[1]["label"] == 0


def test_approved_policy_with_missing_decision_raises(fixture_synthetic_approved_setup):
    """Verify that approved policy file but pending decision (e.g. D-15) raises refusal."""
    policy_file, decisions_file = fixture_synthetic_approved_setup

    # Tamper decisions: make D-15 PENDING
    with open(decisions_file, "r", encoding="utf-8") as f:
        decs = yaml.safe_load(f)
    decs["decisions"]["D-15"]["status"] = "PENDING"
    decs["decisions"]["D-15"]["value"] = None

    with open(decisions_file, "w", encoding="utf-8") as f:
        yaml.dump(decs, f)

    with pytest.raises(LabellingNotApprovedError) as exc_info:
        assert_labelling_approved(policy_path=policy_file, decisions_path=decisions_file)
    assert "D-15" in str(exc_info.value)
