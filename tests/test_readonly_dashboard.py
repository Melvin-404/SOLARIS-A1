"""Unit tests verifying that dashboard execution performs zero file writes (Stage 13).

Tests:
1. Takes a recursive snapshot (file list, sizes, SHA-256 hashes) of data/ and results/.
2. Executes AppTest for dashboard/app.py and every page.
3. Takes post-run snapshot and verifies exact cryptographic identity.
"""

import hashlib
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from solar_flare.paths import project_root


def snapshot_directories(root: Path):
    """Recursively snapshot file sizes and SHA-256 hashes for data/ and results/."""
    snapshot = {}
    for base_name in ["data", "results"]:
        base_dir = root / base_name
        if not base_dir.is_dir():
            continue
        for f in sorted(base_dir.rglob("*")):
            if f.is_file():
                rel = str(f.relative_to(root)).replace("\\", "/")
                # Ignore transient test artifacts if any
                if "pre_hashes.json" in rel or "versions.txt" in rel:
                    continue
                h = hashlib.sha256(f.read_bytes()).hexdigest()
                snapshot[rel] = (f.stat().st_size, h)
    return snapshot


def test_dashboard_execution_zero_writes(tmp_path: Path):
    """Verify that running AppTest against all pages does not modify data/ or results/."""
    root = project_root()

    # 1. Pre-execution snapshot
    snap_before = snapshot_directories(root)
    assert len(snap_before) > 0

    # 2. Run AppTest on app.py and all pages
    app_file = root / "dashboard" / "app.py"
    at = AppTest.from_file(str(app_file), default_timeout=15)
    at.run()
    assert not at.exception

    for pf in (root / "dashboard" / "pages").glob("*.py"):
        at_page = AppTest.from_file(str(pf), default_timeout=15)
        at_page.run()
        assert not at_page.exception

    # 3. Post-execution snapshot
    snap_after = snapshot_directories(root)

    # 4. Assert exact identity
    added_files = set(snap_after.keys()) - set(snap_before.keys())
    removed_files = set(snap_before.keys()) - set(snap_after.keys())
    modified_files = [
        k for k in snap_before.keys()
        if k in snap_after and snap_before[k] != snap_after[k]
    ]

    assert not added_files, f"Dashboard created new files: {added_files}"
    assert not removed_files, f"Dashboard deleted files: {removed_files}"
    assert not modified_files, f"Dashboard mutated files: {modified_files}"
