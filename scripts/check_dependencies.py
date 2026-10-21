"""Dependency and import audit tool for SOLARIS-A1 (Stage 14).

Scans all import statements in src/, dashboard/, scripts/, tests/;
compares against requirements.txt and requirements-dev.txt;
reports missing, unused, and unpinned dependencies.
"""

from __future__ import annotations

import ast
from pathlib import Path
import re
import sys
from typing import Dict, List, Set, Tuple

# Mapping of top-level import package names to canonical PyPI package names
IMPORT_TO_DIST = {
    "yaml": "pyyaml",
    "sklearn": "scikit-learn",
    "fits": "astropy",
    "astropy": "astropy",
    "numpy": "numpy",
    "np": "numpy",
    "pd": "pandas",
    "pandas": "pandas",
    "scipy": "scipy",
    "matplotlib": "matplotlib",
    "plt": "matplotlib",
    "xgboost": "xgboost",
    "joblib": "joblib",
    "streamlit": "streamlit",
    "st": "streamlit",
    "plotly": "plotly",
    "pytest": "pytest",
    "jupyter": "jupyter",
    "IPython": "ipython",
}

# Standard library modules in Python 3.10+
if hasattr(sys, "stdlib_module_names"):
    STDLIB_MODULES = set(sys.stdlib_module_names)
else:
    STDLIB_MODULES = {
        "abc", "argparse", "ast", "asyncio", "base64", "builtins", "collections",
        "concurrent", "contextlib", "copy", "csv", "ctypes", "dataclasses",
        "datetime", "decimal", "difflib", "dis", "doctest", "email", "enum",
        "errno", "filecmp", "fnmatch", "fractions", "functools", "gc", "glob", "gzip",
        "hashlib", "heapq", "hmac", "html", "http", "importlib", "inspect",
        "io", "itertools", "json", "logging", "math", "mimetypes", "multiprocessing",
        "numbers", "operator", "os", "pathlib", "pickle", "platform", "posixpath",
        "pprint", "pydoc", "queue", "random", "re", "secrets", "shutil",
        "signal", "socket", "sqlite3", "ssl", "stat", "string", "struct",
        "subprocess", "sys", "tarfile", "tempfile", "textwrap", "threading",
        "time", "timeit", "traceback", "types", "typing", "unittest", "urllib",
        "uuid", "warnings", "weakref", "zipfile", "zoneinfo", "__future__",
    }

LOCAL_MODULES = {"solar_flare", "dashboard", "scripts"}


def extract_imports_from_file(file_path: Path) -> Set[str]:
    """Parse a python file using AST and return top-level imported module names."""
    imports = set()
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                imports.add(top)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                top = node.module.split(".")[0]
                imports.add(top)
    return imports


def parse_requirements_file(path: Path) -> Dict[str, str]:
    """Parse package names and version specifiers from a requirements file."""
    reqs: Dict[str, str] = {}
    if not path.is_file():
        return reqs

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-r"):
            continue
        # Split on version operators
        match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", line)
        if match:
            pkg_name = match.group(1).lower().replace("_", "-")
            spec = match.group(2).strip()
            reqs[pkg_name] = spec
    return reqs


def check_dependencies(root: Path) -> Dict[str, Any]:
    """Execute complete dependency scan across repository."""
    scan_dirs = [root / "src", root / "dashboard", root / "scripts", root / "tests"]
    scanned_files = []
    all_imports = set()

    for d in scan_dirs:
        if d.is_dir():
            for p in d.rglob("*.py"):
                scanned_files.append(p)
                all_imports.update(extract_imports_from_file(p))

    # Filter out stdlib and internal packages
    third_party_imports = set()
    for imp in all_imports:
        if imp in STDLIB_MODULES or imp in LOCAL_MODULES:
            continue
        dist_name = IMPORT_TO_DIST.get(imp, imp.lower().replace("_", "-"))
        third_party_imports.add(dist_name)

    # Read requirements
    req_main = parse_requirements_file(root / "requirements.txt")
    req_dev = parse_requirements_file(root / "requirements-dev.txt")
    all_reqs = {**req_main, **req_dev}

    missing_in_reqs = sorted(list(third_party_imports - set(all_reqs.keys())))
    unused_in_code = sorted(list(set(all_reqs.keys()) - third_party_imports))
    unpinned_reqs = sorted([pkg for pkg, spec in all_reqs.items() if not spec])

    return {
        "files_scanned": len(scanned_files),
        "third_party_imported": sorted(list(third_party_imports)),
        "requirements_declared": sorted(list(all_reqs.keys())),
        "missing_in_reqs": missing_in_reqs,
        "unused_in_code": unused_in_code,
        "unpinned_reqs": unpinned_reqs,
    }


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    print("=== SOLARIS-A1 Dependency Audit (Stage 14) ===\n")

    res = check_dependencies(root)
    print(f"Files scanned across src/, dashboard/, scripts/, tests/: {res['files_scanned']}")
    print(f"Third-party packages detected in code: {len(res['third_party_imported'])}")
    for pkg in res["third_party_imported"]:
        print(f"  - {pkg}")

    print(f"\nPackages declared in requirements: {len(res['requirements_declared'])}")
    for pkg in res["requirements_declared"]:
        print(f"  - {pkg}")

    print("\n--- Audit Results ---")
    if res["missing_in_reqs"]:
        print(f"[WARN] Packages imported in code but NOT in requirements: {res['missing_in_reqs']}")
    else:
        print("[OK] All imported third-party packages are declared in requirements.")

    if res["unused_in_code"]:
        print(f"[INFO] Declared packages with no direct source import: {res['unused_in_code']}")
    else:
        print("[OK] All declared packages are directly imported in code.")

    if res["unpinned_reqs"]:
        print(f"[WARN] Unpinned packages in requirements: {res['unpinned_reqs']}")
    else:
        print("[OK] All declared packages specify version constraints (e.g. >=).")

    print("\n=== Dependency Audit Complete ===")
    return 0 if not res["missing_in_reqs"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
