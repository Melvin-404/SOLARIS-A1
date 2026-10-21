"""Architectural integrity tests enforcing read-only boundaries and zero-training guarantees (Stage 13).

AST Static Scan Rules:
1. No imports of training/modelling execution modules (run_selection, train_models).
2. No imports of xgboost.
3. No estimator fitting calls (.fit()).
4. No subprocess invocations executing pipeline scripts.
5. No file writes (open in 'w'/'a' mode or write_text) targeting data/ or results/.
"""

import ast
from pathlib import Path
import pytest
from solar_flare.paths import project_root


class ForbiddenArchitectureVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.violations = []

    def visit_Import(self, node):
        for alias in node.names:
            if "xgboost" in alias.name:
                self.violations.append(f"{self.filename}:{node.lineno}: Forbidden import of xgboost in presentation/status layer.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            if "xgboost" in node.module:
                self.violations.append(f"{self.filename}:{node.lineno}: Forbidden import from xgboost.")
            if "solar_flare.modelling.training" in node.module:
                self.violations.append(f"{self.filename}:{node.lineno}: Forbidden import from training module in presentation/status layer.")
        for alias in node.names:
            if alias.name in {"run_selection", "train_models"}:
                self.violations.append(f"{self.filename}:{node.lineno}: Forbidden import of training function '{alias.name}'.")
        self.generic_visit(node)

    def visit_Call(self, node):
        # Check method calls to .fit(
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "fit":
                self.violations.append(f"{self.filename}:{node.lineno}: Forbidden call to .fit() in presentation/status layer.")
            if node.func.attr in {"write_text", "write_bytes"} and not self.filename.endswith("reporting.py"):
                # Ensure no direct write calls in dashboard or status
                self.violations.append(f"{self.filename}:{node.lineno}: Forbidden call to .{node.func.attr}() in presentation/status layer.")

        # Check subprocess calls
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "subprocess":
                self.violations.append(f"{self.filename}:{node.lineno}: Forbidden call to subprocess.")

        # Check open() in write mode
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            for arg in node.args[1:]:
                if isinstance(arg, ast.Constant) and any(m in str(arg.value) for m in ["w", "a", "x", "+"]):
                    self.violations.append(f"{self.filename}:{node.lineno}: Forbidden open() in write mode ('{arg.value}').")
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and any(m in str(kw.value.value) for m in ["w", "a", "x", "+"]):
                    self.violations.append(f"{self.filename}:{node.lineno}: Forbidden open(mode='{kw.value.value}').")

        self.generic_visit(node)


def test_ast_architecture_boundary_enforcement():
    """Verify via AST scan that dashboard, status, and integrity modules contain no forbidden calls."""
    root = project_root()

    target_files = []
    # All dashboard files
    d_dir = root / "dashboard"
    target_files.extend(list(d_dir.glob("*.py")))
    target_files.extend(list((d_dir / "pages").glob("*.py")))
    target_files.extend(list((d_dir / "components").glob("*.py")))

    # status and integrity
    target_files.append(root / "src" / "solar_flare" / "status.py")
    target_files.append(root / "src" / "solar_flare" / "integrity.py")

    all_violations = []

    for f in target_files:
        if not f.is_file():
            continue
        code = f.read_text(encoding="utf-8")
        tree = ast.parse(code, filename=str(f))
        visitor = ForbiddenArchitectureVisitor(filename=f.name)
        visitor.visit(tree)
        all_violations.extend(visitor.violations)

    assert not all_violations, f"Architectural boundary violations found:\n" + "\n".join(all_violations)
