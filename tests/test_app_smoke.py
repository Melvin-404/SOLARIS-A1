"""Smoke tests for Streamlit dashboard execution using streamlit.testing.v1.AppTest (Stage 12).

Tests:
1. AppTest executes dashboard/app.py against the current repository state without exception.
2. AppTest executes each page in dashboard/pages/ without raising unhandled exceptions.
3. AppTest runs against a synthetic minimal/empty environment and gracefully renders empty states.
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from solar_flare.paths import project_root


def test_app_smoke_real_workspace():
    """Verify that app.py runs without unhandled exceptions on current workspace."""
    root = project_root()
    app_file = root / "dashboard" / "app.py"

    at = AppTest.from_file(str(app_file), default_timeout=15)
    at.run()
    assert not at.exception


def test_all_pages_smoke_real_workspace():
    """Verify that all pages run without unhandled exceptions on current workspace."""
    root = project_root()
    pages_dir = root / "dashboard" / "pages"
    page_files = sorted(list(pages_dir.glob("*.py")))

    for pf in page_files:
        at = AppTest.from_file(str(pf), default_timeout=15)
        at.run()
        assert not at.exception, f"Page {pf.name} raised unhandled exception: {at.exception}"


def test_app_smoke_empty_fixtures(tmp_path: Path):
    """Verify that app.py and pages render gracefully without exception on an empty project tree."""
    empty_root = tmp_path / "empty_workspace"
    empty_root.mkdir()
    (empty_root / "results").mkdir()
    (empty_root / "data").mkdir()
    (empty_root / "docs").mkdir()

    root = project_root()
    app_file = root / "dashboard" / "app.py"

    at = AppTest.from_file(str(app_file), default_timeout=15)
    at.run()
    assert not at.exception
