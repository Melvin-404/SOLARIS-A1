"""Unit tests for solar_flare.preprocessing.audit module.

Tests mathematical sample conservation assertion and deliberate broken count trigger.
All synthetic fixtures are named fixture_synthetic_*.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

from solar_flare.preprocessing.audit import (
    ProcessingAudit,
    ReconciliationError,
    write_audit,
)


@pytest.fixture
def fixture_synthetic_audit() -> ProcessingAudit:
    """Create a valid ProcessingAudit instance."""
    return ProcessingAudit(
        file_stem="TEST_AUDIT_STEM",
        original_sample_count=100,
        source_file_sha256_before="test_hash_123456",
        parameters={"max_gap_seconds": 2.0},
        is_final_run=False,
    )


def test_reconciliation_exact_pass(fixture_synthetic_audit):
    """Verify that retained + excluded == original passes cleanly."""
    audit = fixture_synthetic_audit
    # Simulate 30 excluded samples
    excl_df = pd.DataFrame({
        "original_index": list(range(30)),
        "time": list(range(30)),
        "reason": ["NON_FINITE"] * 30,
        "value": [None] * 30,
        "details": ["Non-finite"] * 30,
    })
    audit.add_exclusions(excl_df)
    audit.set_retained(70)
    audit.finalize_hashes("test_hash_123456")

    assert audit.reconcile() is True


def test_reconciliation_broken_count_triggers_error(fixture_synthetic_audit):
    """Verify that a discrepancy between retained + excluded and original raises ReconciliationError."""
    audit = fixture_synthetic_audit
    # 30 excluded samples
    excl_df = pd.DataFrame({
        "original_index": list(range(30)),
        "time": list(range(30)),
        "reason": ["NON_FINITE"] * 30,
        "value": [None] * 30,
        "details": ["Non-finite"] * 30,
    })
    audit.add_exclusions(excl_df)
    # Deliberately report 69 instead of 70
    audit.set_retained(69)
    audit.finalize_hashes("test_hash_123456")

    with pytest.raises(ReconciliationError) as exc_info:
        audit.reconcile()
    assert "Mathematical sample reconciliation failed" in str(exc_info.value)
    assert "discrepancy: -1 samples" in str(exc_info.value)


def test_reconciliation_hash_mismatch_triggers_error(fixture_synthetic_audit):
    """Verify that a modified source file hash raises ReconciliationError."""
    audit = fixture_synthetic_audit
    audit.set_retained(100)
    audit.finalize_hashes("different_hash_after")

    with pytest.raises(ReconciliationError) as exc_info:
        audit.reconcile()
    assert "CRITICAL IMMUTABILITY VIOLATION" in str(exc_info.value)


def test_write_audit_generates_all_formats(fixture_synthetic_audit, tmp_path: Path):
    """Verify that write_audit exports .csv, .json, and .md files."""
    audit = fixture_synthetic_audit
    audit.set_retained(100)
    audit.finalize_hashes("test_hash_123456")
    audit.reconcile()

    created = write_audit(audit, out_dir=tmp_path)
    assert created["csv"].is_file()
    assert created["json"].is_file()
    assert created["md"].is_file()
