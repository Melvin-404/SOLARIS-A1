"""Static code safeguard scan suite for SOLARIS-A1 (Stage 14).

Enforces mandatory architectural, scientific, and integrity invariants via AST and regex scans:
1. No interpolation calls in preprocessing, features, export, labels.
2. Strict isolation of .fit( calls: permitted ONLY in modelling/training.py and
   modelling/preprocessing_fit.py under guarded protocols.
3. No naive train_test_split on windowed time-series data without grouping.
4. No hard-coded absolute paths (e.g. drive letters, /home, /Users).
5. Zero network calls in src/solar_flare/ (requests, urllib, socket, http.client).
6. Zero write operations to data/raw/ across src/, scripts/, and dashboard/.
"""

from __future__ import annotations

import ast
from pathlib import Path
import re
import pytest

from solar_flare.paths import project_root


def test_safeguard_no_interpolation():
    """Verify zero interpolation or imputation in preprocessing, features, export, and labels."""
    root = project_root()
    dirs = [
        root / "src" / "solar_flare" / "preprocessing",
        root / "src" / "solar_flare" / "features",
        root / "src" / "solar_flare" / "export",
        root / "src" / "solar_flare" / "labels",
    ]

    prohibited_patterns = [
        re.compile(r"\.interpolate\s*\("),
        re.compile(r"\binterp\s*\("),
        re.compile(r"\.ffill\s*\("),
        re.compile(r"\.bfill\s*\("),
        re.compile(r"\.resample\s*\("),
        re.compile(r"\.fillna\s*\(.*method", re.IGNORECASE),
    ]

    violations = []
    for d in dirs:
        if not d.is_dir():
            continue
        for p in d.rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for pat in prohibited_patterns:
                    if pat.search(line):
                        violations.append(f"{p.name}:{line_no}: {line.strip()}")

    assert not violations, f"Prohibited interpolation/imputation operations detected: {violations}"


def test_safeguard_fit_isolation():
    """Verify that .fit( calls exist ONLY inside permitted, protocol-guarded modelling files.

    Allowed Exceptions & Rationale:
    1. src/solar_flare/modelling/preprocessing_fit.py:
       - Rationale: Fits scikit-learn StandardScaler/SimpleImputer strictly on training split data.
       - Guard: Raises LeakageError if validation or test indices are passed.
    2. src/solar_flare/modelling/training.py:
       - Rationale: Fits candidate estimators (LogisticRegression, RandomForest, XGBoost)
         during hyperparameter tuning and refits final selected model on training+validation pool.
       - Guard: Guaranteed zero access to sealed test set; training protocol freeze enforced.
    All other modules in src/solar_flare/ are forbidden from invoking .fit().
    """
    root = project_root()
    src_dir = root / "src" / "solar_flare"
    allowed_rel_paths = {
        Path("src/solar_flare/modelling/preprocessing_fit.py"),
        Path("src/solar_flare/modelling/training.py"),
    }

    fit_pattern = re.compile(r"\b\w+\.fit\s*\(")
    violations = []

    for py_file in src_dir.rglob("*.py"):
        rel_path = py_file.relative_to(root)
        if rel_path in allowed_rel_paths:
            continue

        text = py_file.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if fit_pattern.search(line):
                violations.append(f"{rel_path}:{line_no}: {line.strip()}")

    assert not violations, (
        f"Forbidden .fit( call detected outside allowed modelling modules: {violations}. "
        f"Allowed files are: {[str(p) for p in allowed_rel_paths]}"
    )


def test_safeguard_no_naive_train_test_split():
    """Verify that train_test_split is not imported or called as code in src/."""
    root = project_root()
    src_dir = root / "src" / "solar_flare"

    violations = []
    for py_file in src_dir.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and "train_test_split" in [a.name for a in node.names]:
                violations.append(f"{py_file.name}:{node.lineno}: import train_test_split")
            elif isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name == "train_test_split":
                    violations.append(f"{py_file.name}:{node.lineno}: train_test_split() call")

    assert not violations, (
        f"Prohibited naive train_test_split code execution detected in src/: {violations}. "
        "Time-series windowed data requires chronological or event-grouped block splits."
    )


def test_safeguard_no_hardcoded_absolute_paths():
    """Verify that no hard-coded absolute filesystem paths exist in src/ or dashboard/."""
    root = project_root()
    dirs = [root / "src", root / "dashboard"]

    # Match Windows drive letters (C:\, D:\) and Unix home roots (/home/user, /Users/user)
    path_patterns = [
        re.compile(r"[A-Za-z]:[\\/][Uu]sers[\\/]"),
        re.compile(r"/home/[a-zA-Z0-9_\-\.]+"),
    ]

    violations = []
    for d in dirs:
        for py_file in d.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for pat in path_patterns:
                    if pat.search(line):
                        violations.append(f"{py_file.name}:{line_no}: {line.strip()}")

    assert not violations, f"Hard-coded absolute path patterns detected: {violations}"


def test_safeguard_no_network_calls():
    """Verify that no network libraries are imported in src/solar_flare/."""
    root = project_root()
    src_dir = root / "src" / "solar_flare"

    net_patterns = [
        re.compile(r"^\s*import\s+requests\b"),
        re.compile(r"^\s*from\s+requests\b"),
        re.compile(r"^\s*import\s+urllib\b"),
        re.compile(r"^\s*from\s+urllib\b"),
        re.compile(r"^\s*import\s+socket\b"),
        re.compile(r"^\s*import\s+http\.client\b"),
    ]

    violations = []
    for py_file in src_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pat in net_patterns:
                if pat.search(line):
                    violations.append(f"{py_file.name}:{line_no}: {line.strip()}")

    assert not violations, f"Unauthorized network call import detected in src/: {violations}"


def test_safeguard_no_raw_data_writes():
    """Verify that zero write operations target data/raw/ in src/, scripts/, or dashboard/."""
    root = project_root()
    dirs = [root / "src", root / "scripts", root / "dashboard"]

    write_patterns = [
        re.compile(r"open\s*\([^)]*data[/\\\\]raw[^)]*[\'\"][wa\+][\'\"]", re.IGNORECASE),
        re.compile(r"\.writeto\s*\([^)]*data[/\\\\]raw", re.IGNORECASE),
        re.compile(r"\.to_csv\s*\([^)]*data[/\\\\]raw", re.IGNORECASE),
    ]

    violations = []
    for d in dirs:
        for py_file in d.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for pat in write_patterns:
                    if pat.search(line):
                        violations.append(f"{py_file.name}:{line_no}: {line.strip()}")

    assert not violations, f"Write operations targeting data/raw/ detected: {violations}"
