"""Integration test: Comprehensive failure mode verification (Stage 14).

Verifies that all scientific safeguards and boundary guards trigger their documented
exceptions when invariants, schemas, or policies are violated:
1. Corrupt FITS produces documented error path.
2. Missing GTI column names refuse with GTIColumnError.
3. Duplicate timestamps under ERROR refuse with DuplicateTimestampError.
4. Unapproved policy refuses export with LabellingNotApprovedError.
5. PENDING parameters refuse final mode with ParameterPendingError.
6. Test-set access during model selection is flagged.
7. LeakageError is raised for injected future sample.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from astropy.io import fits

from solar_flare.inspection.fits_inspect import list_hdus, InspectionError
from solar_flare.quality.gti_coverage import load_gti_intervals, GTIColumnError
from solar_flare.preprocessing.filters import resolve_duplicate_timestamps, DuplicateTimestampError
from solar_flare.preprocessing.segmentation import segment_continuous, ParameterPendingError
from solar_flare.labels.policy import assert_labelling_approved, LabellingNotApprovedError
from solar_flare.modelling.training import run_selection
from solar_flare.features.leakage_guard import check_no_future_samples, LeakageError
from solar_flare.paths import project_root


def test_failure_mode_corrupt_fits(tmp_path: Path):
    """Verify that a corrupt or truncated FITS file produces documented error path."""
    corrupt_file = tmp_path / "corrupt.fits"
    corrupt_file.write_bytes(b"NOT_A_VALID_FITS_HEADER_DATA_OR_BLOCK")

    with pytest.raises(InspectionError):
        list_hdus(corrupt_file)


def test_failure_mode_missing_gti_columns(tmp_path: Path):
    """Verify that missing START or STOP columns in GTI table raises GTIColumnError."""
    bad_gti_file = tmp_path / "bad_gti.fits"
    col1 = fits.Column(name="T_START_INVALID", format="D", array=np.array([10.0]))
    col2 = fits.Column(name="T_STOP_INVALID", format="D", array=np.array([20.0]))
    tb = fits.BinTableHDU.from_columns([col1, col2], name="GTI")
    fits.HDUList([fits.PrimaryHDU(), tb]).writeto(str(bad_gti_file), overwrite=True)

    with pytest.raises(GTIColumnError) as exc_info:
        load_gti_intervals(bad_gti_file)
    assert "not found in" in str(exc_info.value)


def test_failure_mode_duplicate_timestamps_error():
    """Verify that duplicate timestamps under ERROR resolution policy raises DuplicateTimestampError."""
    df_dup = pd.DataFrame({
        "TIME": [10.0, 11.0, 11.0, 12.0],
        "COUNTS": [100.0, 101.0, 102.0, 103.0],
    })

    with pytest.raises(DuplicateTimestampError) as exc_info:
        resolve_duplicate_timestamps(df_dup, time_col="TIME", policy="ERROR")
    assert "duplicate timestamp" in str(exc_info.value).lower()
    assert "ERROR" in str(exc_info.value)


def test_failure_mode_unapproved_policy_refuses_export(tmp_path: Path):
    """Verify that unapproved labelling policy strictly raises LabellingNotApprovedError."""
    draft_policy = tmp_path / "draft_policy.md"
    draft_policy.write_text("Status: DRAFT — REQUIRES HUMAN APPROVAL\n", encoding="utf-8")

    draft_decisions = tmp_path / "decisions.yaml"
    draft_decisions.write_text(
        "decisions:\n  D-01:\n    status: PENDING\n",
        encoding="utf-8",
    )

    with pytest.raises(LabellingNotApprovedError) as exc_info:
        assert_labelling_approved(policy_path=draft_policy, decisions_path=draft_decisions)
    assert "Gate G3" in str(exc_info.value)


def test_failure_mode_pending_parameters_refuse_final_mode():
    """Verify that PENDING segmentation parameter raises ParameterPendingError."""
    df = pd.DataFrame({"TIME": [10.0, 11.0, 12.0], "COUNTS": [1.0, 2.0, 3.0]})

    with pytest.raises(ParameterPendingError) as exc_info:
        segment_continuous(df, time_col="TIME", max_gap_seconds="PENDING", min_segment_seconds=20.0)
    assert "PENDING" in str(exc_info.value)


def test_failure_mode_test_set_access_flagged():
    """Verify that model selection signature and AST strictly exclude test set access."""
    sig = inspect.signature(run_selection)
    prohibited_params = {"X_test", "y_test", "test_set", "test_df", "test_indices"}
    overlap = set(sig.parameters.keys()).intersection(prohibited_params)
    assert not overlap, f"run_selection accepts prohibited test set parameters: {overlap}"

    training_file = project_root() / "src" / "solar_flare" / "modelling" / "training.py"
    tree = ast.parse(training_file.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                assert alias.name != "read_sealed_test_set", "Forbidden test reader imported in training.py"


def test_failure_mode_injected_future_sample_leakage_error():
    """Verify that future sample access (t > window_end) raises LeakageError."""
    leaking_windows = pd.DataFrame([
        {"window_id": "W_VALID", "window_start": 0.0, "window_end": 60.0, "max_time_used": 60.0},
        {"window_id": "W_LEAK", "window_start": 10.0, "window_end": 70.0, "max_time_used": 75.0},
    ])

    with pytest.raises(LeakageError) as exc_info:
        check_no_future_samples(leaking_windows)
    assert "CRITICAL TEMPORAL LEAKAGE DETECTED" in str(exc_info.value)
    assert "W_LEAK" in str(exc_info.value)
