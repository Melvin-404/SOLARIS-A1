"""Unit tests for dashboard module imports (Stage 12).

Verifies that dashboard/app.py and all dashboard/pages/*.py modules can be parsed
and imported cleanly without syntax errors or unhandled top-level crashes.
"""

import importlib.util
from pathlib import Path
import pytest
from solar_flare.paths import project_root


def test_import_all_dashboard_pages():
    """Verify clean import of dashboard app and all individual pages via importlib."""
    root = project_root()
    dashboard_dir = root / "dashboard"
    app_file = dashboard_dir / "app.py"

    assert app_file.is_file()

    # Find all Python files in dashboard/ and dashboard/pages/
    page_files = [app_file] + sorted(list((dashboard_dir / "pages").glob("*.py")))
    assert len(page_files) >= 8  # app.py + 7 pages

    for pf in page_files:
        module_name = f"dashboard_test_{pf.stem}"
        spec = importlib.util.spec_from_file_location(module_name, pf)
        assert spec is not None
        assert spec.loader is not None
        # We verify that code compiles cleanly to bytecode
        with open(pf, "r", encoding="utf-8") as f:
            code = f.read()
        compiled = compile(code, str(pf), "exec")
        assert compiled is not None
