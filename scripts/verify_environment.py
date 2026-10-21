"""Environment verification script for SOLARIS-A1.

Checks Python version, OS platform, package dependencies, configuration loading,
project directories, and Git availability.
Exits with code 0 on success, or code 1 if required components are missing.
"""

import importlib
from pathlib import Path
import platform
import subprocess
import sys

# Ensure src/ is on sys.path for direct script execution
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

REQUIRED_PACKAGES = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("astropy", "astropy"),
    ("scipy", "scipy"),
    ("matplotlib", "matplotlib"),
    ("pyyaml", "yaml"),
    ("pytest", "pytest"),
]

OPTIONAL_PACKAGES = [
    ("jupyter", "jupyter"),
    ("IPython", "IPython"),
]

EXPECTED_DIRS = [
    ("docs", _REPO_ROOT / "docs"),
    ("config", _REPO_ROOT / "config"),
    ("src", _REPO_ROOT / "src"),
    ("tests", _REPO_ROOT / "tests"),
    ("notebooks", _REPO_ROOT / "notebooks"),
    ("data/raw", _REPO_ROOT / "data" / "raw"),
    ("data/raw/gti", _REPO_ROOT / "data" / "raw" / "gti"),
    ("data/processed", _REPO_ROOT / "data" / "processed"),
    ("data/manifests", _REPO_ROOT / "data" / "manifests"),
    ("results", _REPO_ROOT / "results"),
]


def check_git() -> tuple[bool, str]:
    """Check Git installation and repository status."""
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            return True, "Git repository initialized and accessible."
        return False, f"Git returned code {proc.returncode}: {proc.stderr.strip()}"
    except FileNotFoundError:
        return False, "Git executable not found in PATH."


def main() -> int:
    """Run all verification checks and return exit code."""
    print("=" * 70)
    print("SOLARIS-A1 ENVIRONMENT VERIFICATION (Stage 1)")
    print("=" * 70)

    # 1. Platform & Python
    print(f"\n[1] Platform & Python Runtime:")
    print(f"    Operating System : {platform.system()} {platform.release()} ({platform.architecture()[0]})")
    print(f"    Python Executable: {sys.executable}")
    print(f"    Python Version   : {sys.version.split()[0]}")

    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        print(f"    Environment      : [OK] Isolated virtual environment (.venv)")
    else:
        print(f"    Environment      : [INFO] System / Global Python (Not in .venv)")
        print(f"                       Tip: To activate .venv, run: .\\.venv\\Scripts\\Activate.ps1")

    has_failures = False


    # 2. Required Packages
    print(f"\n[2] Required Dependencies:")
    for display_name, module_name in REQUIRED_PACKAGES:
        try:
            mod = importlib.import_module(module_name)
            version = getattr(mod, "__version__", "unknown")
            print(f"    [OK]      {display_name:12s} version: {version}")
        except ImportError as e:
            print(f"    [FAIL]    {display_name:12s} NOT FOUND ({e})")
            has_failures = True

    # 3. Optional Packages
    print(f"\n[3] Optional / Development Dependencies:")
    for display_name, module_name in OPTIONAL_PACKAGES:
        try:
            mod = importlib.import_module(module_name)
            version = getattr(mod, "__version__", "installed")
            print(f"    [OK]      {display_name:12s} version: {version}")
        except ImportError:
            print(f"    [SKIPPED] {display_name:12s} not installed (optional)")

    # 4. Project Directories
    print(f"\n[4] Project Directory Structure:")
    for name, path in EXPECTED_DIRS:
        if path.is_dir():
            print(f"    [OK]      {name:16s} -> {path}")
        else:
            print(f"    [MISSING] {name:16s} (expected at {path})")
            has_failures = True

    # 5. Configuration System
    print(f"\n[5] Configuration System:")
    try:
        from solar_flare.config import load_config
        cfg = load_config()
        proj_name = cfg.get("project", {}).get("name", "Unknown")
        stage = cfg.get("project", {}).get("stage_status", "Unknown")
        print(f"    [OK]      Configuration loaded successfully.")
        print(f"              Project: {proj_name}")
        print(f"              Status : {stage}")
        print(f"              Raw Dir: {cfg['resolved_paths']['raw_dir']}")
    except Exception as exc:
        print(f"    [FAIL]    Failed to load configuration: {exc}")
        has_failures = True

    # 6. Git Status
    print(f"\n[6] Version Control:")
    git_ok, git_msg = check_git()
    status_tag = "[OK]" if git_ok else "[INFO]"
    print(f"    {status_tag:9s} {git_msg}")

    # Summary
    print("\n" + "=" * 70)
    if has_failures:
        print("VERIFICATION FAILED: One or more required components are missing.")
        print("Please review requirements-dev.txt and install missing dependencies.")
        print("=" * 70)
        return 1

    print("VERIFICATION SUCCESSFUL: All required Stage 1 components are verified.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
