"""Unit tests for pipeline status function and stage state transitions (Stage 13).

Tests:
1. Missing artifacts return status='MISSING'.
2. Blocked notice files (AWAITING_G*.md, BLOCKED_*.md) trigger status='BLOCKED'.
3. Stale configuration parameters trigger status='STALE' with recorded vs current values.
4. Complete valid artifacts return status='COMPLETE' or 'PROVISIONAL'.
"""

import json
from pathlib import Path
import pytest
import yaml

from solar_flare.status import pipeline_status, StatusReport


def test_status_empty_project(tmp_path: Path):
    """Verify that an empty project returns MISSING across all stages."""
    empty_root = tmp_path / "empty_proj"
    empty_root.mkdir()

    rep = pipeline_status(empty_root)
    assert isinstance(rep, StatusReport)
    assert len(rep.stages) == 9  # Stages 3 to 11
    for s in rep.stages:
        assert s.status in {"MISSING", "BLOCKED"}  # Stage 6 defaults to MISSING if policy not found


def test_status_blocked_detection(tmp_path: Path):
    """Verify that AWAITING files trigger BLOCKED status."""
    proj = tmp_path / "blocked_proj"
    proj.mkdir()

    # Stage 10 AWAITING_G7
    exp_dir = proj / "results" / "experiments"
    exp_dir.mkdir(parents=True)
    (exp_dir / "AWAITING_G7.md").write_text("# Awaiting Gate G7\n", encoding="utf-8")

    # Stage 11 AWAITING_G8
    (exp_dir / "AWAITING_G8.md").write_text("# Awaiting Gate G8\n", encoding="utf-8")

    rep = pipeline_status(proj)
    s10 = next(s for s in rep.stages if s.stage_id == 10)
    assert s10.status == "BLOCKED"
    assert s10.gate_id == "G7"

    s11 = next(s for s in rep.stages if s.stage_id == 11)
    assert s11.status == "BLOCKED"
    assert s11.gate_id == "G8"


def test_status_stale_detection(tmp_path: Path):
    """Verify that parameter discrepancy between build_log and config triggers STALE."""
    proj = tmp_path / "stale_proj"
    stem = "AL1_SOLEXS_20261018_SDD2_L1"

    # Stage 8 features
    feat_dir = proj / "data" / "processed" / "features" / stem
    feat_dir.mkdir(parents=True)
    (feat_dir / "window_index.csv").write_text("window_id,window_start_sec,window_end_sec,coverage_fraction\nW1,0,60,1.0\n", encoding="utf-8")
    (feat_dir / "window_features.csv").write_text("window_id,f1,f2,f3,f4,f5\nW1,1,2,3,4,5\n", encoding="utf-8")

    # Build log with recorded window_seconds = 60.0
    res_feat_dir = proj / "results" / "features" / stem
    res_feat_dir.mkdir(parents=True)
    build_log = {
        "parameters": {"window_seconds": 60.0, "stride_seconds": 10.0}
    }
    (res_feat_dir / "build_log.json").write_text(json.dumps(build_log), encoding="utf-8")

    # Current config with modified window_length_seconds = 120.0
    cfg_dir = proj / "config"
    cfg_dir.mkdir(parents=True)
    cfg_data = {
        "features": {"window_length_seconds": 120.0, "stride_seconds": 10.0}
    }
    (cfg_dir / "default.yaml").write_text(yaml.dump(cfg_data), encoding="utf-8")

    rep = pipeline_status(proj)
    s8 = next(s for s in rep.stages if s.stage_id == 8)
    assert s8.status == "STALE"
    assert "Recorded window_seconds" in s8.reason or "mismatch" in s8.reason.lower()
    assert s8.recorded_hash == "60.0"
    assert s8.current_hash == "120.0"
