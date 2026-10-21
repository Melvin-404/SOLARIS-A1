"""Unit tests for artifact schema validation and cryptographic integrity (Stage 13).

Tests:
1. Schema validators accept valid synthetic files and reject invalid/empty ones.
2. Hash lineage checks detect tampering and return status='MISMATCH' with both hashes.
3. Cryptographic test set lock verification accurately validates seal.
"""

from pathlib import Path
import json
import pytest

from solar_flare.integrity import (
    validate_inventory_csv,
    validate_quality_summary_csv,
    validate_window_index_csv,
    validate_window_features_csv,
    validate_protocol_snapshot_yaml,
    validate_lock_record_json,
    validate_metrics_csv,
    verify_test_lock_integrity,
    compute_sha256,
)


def test_schema_validators_accept_valid_and_reject_invalid(tmp_path: Path):
    """Verify that schema validators accept conforming files and reject malformed ones."""
    # 1. Inventory CSV
    inv_file = tmp_path / "inventory.csv"
    inv_file.write_text("file_name,product_type\nAL1.lc,LIGHTCURVE\n", encoding="utf-8")
    ok, _ = validate_inventory_csv(inv_file)
    assert ok is True

    bad_inv = tmp_path / "bad_inventory.csv"
    bad_inv.write_text("wrong_col_1,wrong_col_2\n1,2\n", encoding="utf-8")
    ok_bad, _ = validate_inventory_csv(bad_inv)
    assert ok_bad is False

    # 2. Window Index CSV
    idx_file = tmp_path / "window_index.csv"
    idx_file.write_text(
        "window_id,window_start_sec,window_end_sec,coverage_fraction\nW1,0,60,1.0\n",
        encoding="utf-8",
    )
    ok_idx, _ = validate_window_index_csv(idx_file)
    assert ok_idx is True

    # 3. Protocol Snapshot YAML
    proto_file = tmp_path / "protocol_snapshot.yaml"
    proto_file.write_text("protocol_id: P1\nstatus: FROZEN\ntask: detection\n", encoding="utf-8")
    ok_proto, _ = validate_protocol_snapshot_yaml(proto_file)
    assert ok_proto is True

    bad_proto = tmp_path / "bad_protocol.yaml"
    bad_proto.write_text("not_a_protocol: true\n", encoding="utf-8")
    ok_bad_proto, _ = validate_protocol_snapshot_yaml(bad_proto)
    assert ok_bad_proto is False


def test_lock_integrity_detects_tampering(tmp_path: Path):
    """Verify that lock verification detects data modification and reports MISMATCH."""
    exp_dir = tmp_path / "exp_tamper"
    sealed_dir = exp_dir / "sealed"
    sealed_dir.mkdir(parents=True)

    test_file = sealed_dir / "test_set.csv"
    test_file.write_text("window_id,label\nW1,0\nW2,1\n", encoding="utf-8")
    true_hash = compute_sha256(test_file)

    lock_file = sealed_dir / "lock_record.json"
    lock_file.write_text(json.dumps({
        "sha256": true_hash,
        "row_count": 2,
        "protocol_hash": "proto123",
    }), encoding="utf-8")

    # Clean lock check passes
    res_clean = verify_test_lock_integrity(exp_dir)
    assert res_clean.status == "OK"
    assert res_clean.recorded_value == true_hash
    assert res_clean.current_value == true_hash

    # Tamper with test file: append a row
    test_file.write_text("window_id,label\nW1,0\nW2,1\nW3,0\n", encoding="utf-8")
    tampered_hash = compute_sha256(test_file)

    res_tampered = verify_test_lock_integrity(exp_dir)
    assert res_tampered.status == "MISMATCH"
    assert res_tampered.recorded_value == true_hash
    assert res_tampered.current_value == tampered_hash
    assert "TAMPERING DETECTED" in res_tampered.message
