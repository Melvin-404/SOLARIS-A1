"""Static code scan test guaranteeing zero interpolation in preprocessing.

Scans all Python source files in src/solar_flare/preprocessing/ and src/solar_flare/features/
for prohibited imputation, interpolation, or filling calls:
- .fillna
- .ffill
- .bfill
- .interpolate
- interp(
- .resample(
"""

from __future__ import annotations

from pathlib import Path
import re
import pytest

from solar_flare.paths import project_root

PROHIBITED_PATTERNS = [
    r"\.fillna\s*\(",
    r"\.ffill\s*\(",
    r"\.bfill\s*\(",
    r"\.interpolate\s*\(",
    r"\binterp\s*\(",
    r"\.resample\s*\(",
]


def test_no_interpolation_in_preprocessing_and_features():
    """Verify that no prohibited interpolation or filling operations exist in preprocessing source code."""
    root = project_root()
    dirs_to_scan = [
        root / "src" / "solar_flare" / "preprocessing",
        root / "src" / "solar_flare" / "features",
    ]

    scanned_files = []
    violations = []

    compiled_patterns = [re.compile(p, re.IGNORECASE) for p in PROHIBITED_PATTERNS]

    for d in dirs_to_scan:
        if not d.is_dir():
            continue
        for py_file in d.glob("**/*.py"):
            scanned_files.append(py_file)
            content = py_file.read_text(encoding="utf-8")
            for line_no, line in enumerate(content.splitlines(), start=1):
                # Ignore comment lines
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for pat in compiled_patterns:
                    if pat.search(line):
                        violations.append(
                            f"{py_file.name}:{line_no}: Prohibited interpolation/fill match: {line.strip()}"
                        )

    assert len(scanned_files) > 0, "No preprocessing files found to scan"
    assert not violations, f"Detected prohibited interpolation call(s):\n" + "\n".join(violations)
