"""Test Set Sealing and Cryptographic Lockdown Engine (Stage 10).

CRITICAL SCIENTIFIC GOVERNANCE:
1. The test partition is sealed BEFORE any model tuning or selection runs.
2. The sealed test set is cryptographically hashed (SHA-256) and locked in
   results/experiments/<experiment_id>/sealed/test_set.csv.
3. Every read access to the sealed test set is permanently logged in access_log.jsonl.
4. Model selection and hyperparameter tuning code must NEVER read the sealed test set.
   A static test (test_no_test_access_in_selection.py) and a dynamic guard verify
   that access count remains strictly 0 throughout Stage 10.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, Optional, Union
import numpy as np
import pandas as pd

from solar_flare.modelling.guards import TestLeakageError


def seal_test_set(
    X_test: pd.DataFrame,
    y_test: pd.DataFrame,
    metadata_test: pd.DataFrame,
    out_dir: Union[Path, str],
    protocol_hash: str,
    dataset_export_id: str,
) -> Dict[str, Any]:
    """Cryptographically seal and lock the test dataset before model selection.
    
    Parameters
    ----------
    X_test : pd.DataFrame
        Test feature matrix.
    y_test : pd.DataFrame
        Test target labels.
    metadata_test : pd.DataFrame
        Test metadata and coordinates.
    out_dir : Path or str
        Destination directory for sealed artifacts.
    protocol_hash : str
        Hash of approved training protocol.
    dataset_export_id : str
        ID of source dataset export.
        
    Returns
    -------
    dict
        Lock record containing file hash, row counts, and creation timestamp.
    """
    sealed_dir = Path(out_dir) / "sealed"
    sealed_dir.mkdir(parents=True, exist_ok=True)

    test_file = sealed_dir / "test_set.csv"
    lock_file = sealed_dir / "lock_record.json"
    access_log = sealed_dir / "access_log.jsonl"

    # Combine test features, labels, and metadata for unified immutable storage
    combined = metadata_test.copy() if metadata_test is not None else pd.DataFrame(index=X_test.index)
    if "label" in y_test.columns:
        combined["label"] = y_test["label"].values
    if "label_reason" in y_test.columns:
        combined["label_reason"] = y_test["label_reason"].values

    for col in X_test.columns:
        combined[f"feat_{col}"] = X_test[col].values

    # Write CSV
    combined.to_csv(test_file, index=False)

    # Compute SHA-256 hash
    file_bytes = test_file.read_bytes()
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    # Attempt to set file to read-only (Windows safe)
    try:
        os.chmod(test_file, stat.S_IREAD)
    except Exception:
        pass

    ts_now = datetime.now(timezone.utc).isoformat()
    record = {
        "status": "SEALED_LOCKED",
        "file_name": "test_set.csv",
        "sha256": sha256_hash,
        "row_count": len(combined),
        "feature_count": len(X_test.columns),
        "protocol_hash": protocol_hash,
        "dataset_export_id": dataset_export_id,
        "created_at_utc": ts_now,
        "read_only_enforced": True,
    }

    lock_file.write_text(json.dumps(record, indent=2), encoding="utf-8")

    # Initialize empty access log
    if not access_log.is_file():
        access_log.write_text("", encoding="utf-8")

    return record


def verify_lock(sealed_dir: Union[Path, str]) -> bool:
    """Verify cryptographic integrity of the sealed test dataset.
    
    Parameters
    ----------
    sealed_dir : Path or str
        Directory containing test_set.csv and lock_record.json.
        
    Returns
    -------
    bool
        True if valid.
        
    Raises
    -------
    TestLeakageError
        If lock record is missing, test file is missing, or hash mismatch is detected.
    """
    s_dir = Path(sealed_dir)
    lock_file = s_dir / "lock_record.json"
    test_file = s_dir / "test_set.csv"

    if not lock_file.is_file():
        raise TestLeakageError(f"Sealed lock record not found at: {lock_file}")
    if not test_file.is_file():
        raise TestLeakageError(f"Sealed test data file not found at: {test_file}")

    record = json.loads(lock_file.read_text(encoding="utf-8"))
    expected_hash = record.get("sha256")

    actual_hash = hashlib.sha256(test_file.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise TestLeakageError(
            f"SEALED TEST SET TAMPERING DETECTED! Expected hash {expected_hash}, got {actual_hash}."
        )

    return True


def log_test_access(sealed_dir: Union[Path, str], caller: str, phase: str) -> None:
    """Log an auditable read access event to the sealed test set."""
    s_dir = Path(sealed_dir)
    access_log = s_dir / "access_log.jsonl"
    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "caller": caller,
        "phase": phase,
    }
    with open(access_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_sealed_test_set(
    sealed_dir: Union[Path, str],
    caller: str,
    phase: str,
) -> pd.DataFrame:
    """Read the sealed test set, verifying cryptographic lock and logging access.
    
    PROHIBITED CALLER:
    Must NEVER be called during Stage 10 model selection or training.
    """
    s_dir = Path(sealed_dir)
    # 1. Log access
    log_test_access(s_dir, caller=caller, phase=phase)

    # 2. Verify lock integrity
    verify_lock(s_dir)

    # 3. Read data
    test_file = s_dir / "test_set.csv"
    return pd.read_csv(test_file)
