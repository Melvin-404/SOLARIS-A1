"""Unit tests for consistency and lineage checks on synthetic project setups (Stage 13).

Tests:
1. verify_raw_to_preprocessing_lineage returns OK when hashes match and MISMATCH when corrupted.
2. verify_segments_to_features_lineage returns OK when segment hashes match and MISMATCH when corrupted.
3. verify_test_lock_integrity detects missing records or altered test data.
"""

from pathlib import Path
import json
import pytest

from solar_flare.integrity import (
    verify_raw_to_preprocessing_lineage,
    verify_segments_to_features_lineage,
    verify_test_lock_integrity,
    compute_sha256,
)


def test_raw_to_preprocessing_consistency(tmp_path: Path):
    """Verify raw lineage check on matching and corrupted synthetic files."""
    root = tmp_path / "raw_lineage_proj"
    raw_dir = root / "data" / "raw"
    raw_dir.mkdir(parents=True)
    raw_file = raw_dir / "test_obs.lc"
    raw_file.write_text("dummy raw content\n", encoding="utf-8")
    raw_hash = compute_sha256(raw_file)

    prep_dir = root / "results" / "preprocessing"
    prep_dir.mkdir(parents=True)
    hash_file = prep_dir / "raw_hashes_before.json"
    hash_file.write_text(json.dumps({"data/raw/test_obs.lc": raw_hash}), encoding="utf-8")

    # Clean check returns OK
    res_clean = verify_raw_to_preprocessing_lineage(root)
    assert len(res_clean) == 1
    assert res_clean[0].status == "OK"

    # Mutate raw file
    raw_file.write_text("mutated raw content\n", encoding="utf-8")
    res_mut = verify_raw_to_preprocessing_lineage(root)
    assert len(res_mut) == 1
    assert res_mut[0].status == "MISMATCH"
    assert res_mut[0].recorded_value == raw_hash
    assert res_mut[0].current_value != raw_hash


def test_segment_to_features_consistency(tmp_path: Path):
    """Verify segment lineage check on matching and corrupted synthetic files."""
    root = tmp_path / "seg_lineage_proj"
    stem = "AL1_SOLEXS_20261018_SDD2_L1"

    seg_dir = root / "data" / "processed" / "segments" / stem
    seg_dir.mkdir(parents=True)
    seg_file = seg_dir / "seg_001.csv"
    seg_file.write_text("time,counts\n0,10\n1,12\n", encoding="utf-8")
    seg_hash = compute_sha256(seg_file)

    feat_dir = root / "results" / "features" / stem
    feat_dir.mkdir(parents=True)
    build_log_file = feat_dir / "build_log.json"
    build_log_file.write_text(json.dumps({
        "segment_hashes_before": {"seg_001.csv": seg_hash}
    }), encoding="utf-8")

    # Clean check
    res_clean = verify_segments_to_features_lineage(root)
    assert len(res_clean) == 1
    assert res_clean[0].status == "OK"

    # Mutate segment file
    seg_file.write_text("time,counts\n0,10\n1,999\n", encoding="utf-8")
    res_mut = verify_segments_to_features_lineage(root)
    assert len(res_mut) == 1
    assert res_mut[0].status == "MISMATCH"
