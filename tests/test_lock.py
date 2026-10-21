"""Unit tests for test set cryptographic sealing and access locking (Stage 10).

Validates:
- seal_test_set writes test_set.csv and lock_record.json with SHA-256 hash.
- verify_lock detects file modification or tampering.
- Access logging records all reads in access_log.jsonl.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
import pandas as pd

from solar_flare.modelling.lock import seal_test_set, verify_lock, read_sealed_test_set
from solar_flare.modelling.guards import TestLeakageError


def test_seal_test_set_generates_hash_and_record(tmp_path: Path):
    """Verify that sealing produces valid lock_record.json with correct row count and hash."""
    X_test = pd.DataFrame({"feat1": [1.0, 2.0], "feat2": [3.0, 4.0]})
    y_test = pd.DataFrame({"label": [0, 1], "label_reason": ["QUIET", "EVENT"]})
    meta_test = pd.DataFrame({"window_id": ["w_01", "w_02"], "window_start": [10.0, 20.0]})

    record = seal_test_set(
        X_test=X_test,
        y_test=y_test,
        metadata_test=meta_test,
        out_dir=tmp_path,
        protocol_hash="mock_hash_123",
        dataset_export_id="exp_det_001",
    )

    assert record["status"] == "SEALED_LOCKED"
    assert record["row_count"] == 2
    assert len(record["sha256"]) == 64

    sealed_dir = tmp_path / "sealed"
    assert (sealed_dir / "test_set.csv").is_file()
    assert (sealed_dir / "lock_record.json").is_file()
    assert (sealed_dir / "access_log.jsonl").is_file()

    # Lock verification passes initially
    assert verify_lock(sealed_dir) is True


def test_verify_lock_detects_tampering(tmp_path: Path):
    """Verify that any modification to sealed test_set.csv triggers TestLeakageError."""
    X_test = pd.DataFrame({"feat1": [1.0, 2.0]})
    y_test = pd.DataFrame({"label": [0, 1]})
    meta_test = pd.DataFrame({"window_id": ["w_01", "w_02"]})

    seal_test_set(X_test, y_test, meta_test, out_dir=tmp_path, protocol_hash="h1", dataset_export_id="d1")
    sealed_dir = tmp_path / "sealed"

    # Tamper with the sealed file (temporarily enable write to simulate tampering)
    test_csv = sealed_dir / "test_set.csv"
    import stat, os
    os.chmod(test_csv, stat.S_IWRITE)
    with open(test_csv, "a", encoding="utf-8") as f:
        f.write("\ntampered_row,999,999\n")

    with pytest.raises(TestLeakageError, match="SEALED TEST SET TAMPERING DETECTED"):
        verify_lock(sealed_dir)


def test_access_logging_records_reads(tmp_path: Path):
    """Verify that calling read_sealed_test_set records access events in access_log.jsonl."""
    X_test = pd.DataFrame({"feat1": [1.0]})
    y_test = pd.DataFrame({"label": [0]})
    meta_test = pd.DataFrame({"window_id": ["w_01"]})

    seal_test_set(X_test, y_test, meta_test, out_dir=tmp_path, protocol_hash="h1", dataset_export_id="d1")
    sealed_dir = tmp_path / "sealed"

    # Read sealed test set
    df = read_sealed_test_set(sealed_dir, caller="test_stage11", phase="stage11_evaluation")
    assert len(df) == 1

    # Check access log
    log_file = sealed_dir / "access_log.jsonl"
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["caller"] == "test_stage11"
    assert entry["phase"] == "stage11_evaluation"
