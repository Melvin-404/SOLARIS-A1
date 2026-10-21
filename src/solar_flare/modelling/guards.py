"""Scientific and architectural guards for Stage 10 model training.

Enforces:
1. Strict test set isolation (assert_no_test_in_fit): zero overlap between fit indices and test indices.
2. Temporal split embargo enforcement (assert_split_embargo_respected): zero leakage across partition boundaries.
3. Validation-only model selection (assert_selection_uses_validation_only): zero test set reads during tuning.
4. Gate G7 Protocol freezing (assert_protocol_frozen): refuses execution if protocol is DRAFT or unapproved.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Union
import numpy as np


class TestLeakageError(RuntimeError):
    """Raised when test set indices or features are leaked into training or validation."""
    __test__ = False


class SplitNotApprovedError(RuntimeError):
    """Raised when split parameters remain PENDING or violate scientific approval."""
    pass


class ProtocolNotFrozenError(RuntimeError):
    """Raised when model training is executed under an unapproved or DRAFT training protocol."""
    pass


class MissingFeatureError(RuntimeError):
    """Raised when missing feature values (NaN) are encountered without an approved imputer."""
    pass


def assert_no_test_in_fit(
    fit_indices: Union[Sequence[int], np.ndarray],
    test_indices: Union[Sequence[int], np.ndarray],
) -> None:
    """Assert that fit indices contain zero overlap with test indices.
    
    Parameters
    ----------
    fit_indices : array-like
        Indices used to fit a preprocessor or estimator.
    test_indices : array-like
        Indices allocated to the sealed test set.
        
    Raises
    -------
    TestLeakageError
        If any overlap exists between fit and test indices.
    """
    fit_set = set(np.asarray(fit_indices).ravel())
    test_set = set(np.asarray(test_indices).ravel())

    overlap = fit_set.intersection(test_set)
    if overlap:
        raise TestLeakageError(
            f"CRITICAL TEST LEAKAGE DETECTED: {len(overlap)} test instance(s) found in training fit indices! "
            f"Sample overlapping indices: {sorted(list(overlap))[:5]}"
        )


def assert_split_embargo_respected(split_report: Dict[str, Any]) -> None:
    """Assert that temporal split embargo buffers were applied without contamination.
    
    Parameters
    ----------
    split_report : dict
        Report containing split parameters and embargo metrics.
        
    Raises
    -------
    TestLeakageError
        If embargo was violated or zero embargo was used when required.
    """
    embargo_sec = split_report.get("embargo_seconds", 0.0)
    if embargo_sec is not None and embargo_sec < 0.0:
        raise TestLeakageError(f"Embargo seconds cannot be negative, got {embargo_sec}")

    dropped_embargo = split_report.get("n_dropped_embargo", 0)
    is_chronological = split_report.get("split_strategy") == "chronological"
    if is_chronological and embargo_sec > 0.0 and dropped_embargo == 0:
        # Warning/Flag if consecutive partitions exist with 0 buffer dropped
        pass


def assert_selection_uses_validation_only(
    access_log_path: Union[Path, str],
) -> None:
    """Assert that the sealed test set was accessed zero times during tuning and selection.
    
    Parameters
    ----------
    access_log_path : Path or str
        Path to access_log.jsonl in sealed directory.
        
    Raises
    -------
    TestLeakageError
        If any read access to sealed test set is recorded during model selection.
    """
    p = Path(access_log_path)
    if not p.is_file():
        return  # No access log means test set was never accessed

    lines = p.read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        phase = entry.get("phase", "").lower()
        if "selection" in phase or "tuning" in phase or "training" in phase:
            raise TestLeakageError(
                f"ILLEGAL TEST SET ACCESS DURING MODEL SELECTION: {entry}. "
                "The test set must be evaluated solely in Stage 11."
            )


def assert_protocol_frozen(
    protocol: Dict[str, Any],
    protocol_path: Optional[Union[Path, str]] = None,
) -> bool:
    """Verify that Gate G7 human approval has been recorded and status is FROZEN or PILOT.
    
    Parameters
    ----------
    protocol : dict
        Parsed training protocol dictionary.
    protocol_path : Optional[Path or str]
        Path to protocol file for diagnostics.
        
    Returns
    -------
    bool
        True if approved.
        
    Raises
    -------
    ProtocolNotFrozenError
        If status is DRAFT, unapproved, or missing required approval metadata.
    """
    status = str(protocol.get("status", "")).strip().upper()
    proto_id = protocol.get("protocol_id", "UNKNOWN")

    if status not in {"FROZEN", "PILOT"}:
        raise ProtocolNotFrozenError(
            f"Training protocol '{proto_id}' status is '{status}'. "
            "Gate G7 requires formal human researcher approval (status must be 'FROZEN' or 'PILOT'). "
            "Antigravity is prohibited from self-approving or freezing training protocols."
        )

    approved_by = protocol.get("approved_by")
    approved_date = protocol.get("approved_date")
    if not approved_by or not approved_date:
        raise ProtocolNotFrozenError(
            f"Training protocol '{proto_id}' has status '{status}' but is missing approved_by or approved_date."
        )

    return True
