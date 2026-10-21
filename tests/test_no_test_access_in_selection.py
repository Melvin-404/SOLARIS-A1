"""Static code analysis test guaranteeing zero test set access in selection code (Stage 10).

CRITICAL ARCHITECTURAL SAFEGUARD:
Model selection and hyperparameter tuning must never reference, import, or read the sealed test set.
This test scans the AST of src/solar_flare/modelling/training.py to guarantee:
1. No import of read_sealed_test_set or lock reader functions.
2. No string or path reference to 'sealed' test files.
3. The function signature of run_selection does not accept test arguments.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
import pytest

from solar_flare.paths import project_root
from solar_flare.modelling.training import run_selection


def test_no_test_access_in_selection_ast_scan():
    """Verify that training.py contains zero test set imports or access paths."""
    root = project_root()
    training_file = root / "src" / "solar_flare" / "modelling" / "training.py"
    assert training_file.is_file(), "training.py not found"

    source_code = training_file.read_text(encoding="utf-8")
    tree = ast.parse(source_code)

    forbidden_symbols = {
        "read_sealed_test_set",
        "test_set.csv",
        "test_set.parquet",
    }

    for node in ast.walk(tree):
        # 1. Check import names
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                assert alias.name not in forbidden_symbols, (
                    f"Forbidden import '{alias.name}' detected in training.py."
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in forbidden_symbols, (
                    f"Forbidden import '{alias.name}' detected in training.py."
                )
        # 2. Check string literals
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            for symbol in forbidden_symbols:
                assert symbol not in node.value, (
                    f"Forbidden string literal reference '{symbol}' detected in training.py."
                )


def test_run_selection_signature_excludes_test_parameters():
    """Verify that run_selection function signature does not accept test data."""
    sig = inspect.signature(run_selection)
    param_names = set(sig.parameters.keys())

    prohibited_params = {"X_test", "y_test", "test_df", "test_set", "test_indices"}
    overlap = param_names.intersection(prohibited_params)
    assert not overlap, (
        f"run_selection accepts prohibited test parameters: {overlap}. "
        "Hyperparameter tuning and selection must operate strictly on validation data."
    )
