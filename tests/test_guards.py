"""Unit tests for modelling guards (Stage 10).

Validates:
- assert_no_test_in_fit detects test sample overlap.
- assert_split_embargo_respected checks embargo constraints.
- assert_selection_uses_validation_only flags test set access during tuning.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from solar_flare.modelling.guards import (
    assert_no_test_in_fit,
    assert_split_embargo_respected,
    assert_selection_uses_validation_only,
    TestLeakageError,
)


def test_no_test_in_fit_overlap_raises():
    """Verify that any overlapping index raises TestLeakageError."""
    with pytest.raises(TestLeakageError, match="CRITICAL TEST LEAKAGE DETECTED"):
        assert_no_test_in_fit([0, 1, 2, 3], [3, 4, 5])


def test_no_test_in_fit_clean_passes():
    """Verify that disjoint index arrays pass cleanly."""
    assert_no_test_in_fit([0, 1, 2], [3, 4, 5])  # Should not raise


def test_split_embargo_negative_raises():
    """Verify that negative embargo duration raises TestLeakageError."""
    with pytest.raises(TestLeakageError, match="cannot be negative"):
        assert_split_embargo_respected({"embargo_seconds": -10.0})


def test_selection_uses_validation_only_flags_test_read(tmp_path: Path):
    """Verify that an access log recording a test read during selection raises TestLeakageError."""
    log_file = tmp_path / "access_log.jsonl"
    entry = {"caller": "run_selection", "phase": "model_selection_tuning"}
    log_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    with pytest.raises(TestLeakageError, match="ILLEGAL TEST SET ACCESS"):
        assert_selection_uses_validation_only(log_file)
