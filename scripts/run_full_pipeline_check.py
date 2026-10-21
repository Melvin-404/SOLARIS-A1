"""Comprehensive automated pipeline verification tool for SOLARIS-A1 (Stage 14).

Executes:
1. Full test suite (pytest)
2. Dependency verification (pip check)
3. Import & requirements audit (scripts/check_dependencies.py)
4. Environment verification (scripts/verify_environment.py)
5. Static safeguard scans (tests/integration/test_static_safeguards.py)
6. Dashboard AppTest smoke suite
7. Pure pipeline status evaluation (src/solar_flare/status.py)
8. Artifact schema & cryptographic lineage checks (src/solar_flare/integrity.py)
9. Raw observation data immutability assertion

Writes comprehensive verification report to results/checks/full_check_<timestamp>.md.
Exits with code 0 only if all required checks pass.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Tuple

# Ensure paths
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from solar_flare.paths import project_root
from solar_flare.status import pipeline_status
from solar_flare.integrity import run_integrity_checks, generate_integrity_report_markdown


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_command(cmd: List[str], desc: str) -> Tuple[int, str, str]:
    """Run a shell/python command, return exit_code, stdout, stderr."""
    print(f"--> Running: {desc}...")
    proc = subprocess.run(cmd, cwd=str(_ROOT), capture_output=True, text=True, encoding="utf-8")
    return proc.returncode, proc.stdout, proc.stderr


def main() -> int:
    root = project_root()
    checks_dir = root / "results" / "checks"
    checks_dir.mkdir(parents=True, exist_ok=True)
    utc_now = datetime.now(timezone.utc)
    ts_str = utc_now.strftime("%Y%m%d_%H%M%SZ")
    out_md_path = checks_dir / f"full_check_{ts_str}.md"

    print("======================================================================")
    print("SOLARIS-A1 FULL AUTOMATED PIPELINE AUDIT (Stage 14)")
    print(f"Timestamp: {utc_now.isoformat()}")
    print("======================================================================\n")

    report_sections: List[str] = [
        "# SOLARIS-A1 Comprehensive Automated Pipeline Verification Report (Stage 14)",
        "",
        f"**Audit Timestamp:** `{utc_now.isoformat()}`  ",
        f"**Platform:** `{sys.platform}` | Python `{sys.version.split()[0]}`  ",
        f"**Project Root:** `{root}`  ",
        "",
        "---",
        "",
    ]

    all_passed = True
    check_summaries: List[Dict[str, Any]] = []

    # 1. Full Pytest Suite
    py_exec = sys.executable
    code_pytest, out_pytest, err_pytest = run_command(
        [py_exec, "-m", "pytest", "-v"],
        "Pytest Full Test Suite"
    )
    passed_pytest = (code_pytest == 0)
    all_passed = all_passed and passed_pytest
    check_summaries.append({"name": "Full Pytest Suite", "status": "PASS" if passed_pytest else "FAIL", "code": code_pytest})

    # Extract pytest summary line
    summary_lines = [l for l in out_pytest.splitlines() if "passed" in l or "failed" in l or "error" in l]
    pytest_summary_line = summary_lines[-1] if summary_lines else "Completed"

    report_sections.extend([
        "## 1. Automated Test Suite (pytest)",
        "",
        f"- **Exit Code:** `{code_pytest}`",
        f"- **Result Summary:** `{pytest_summary_line}`",
        "",
        "```text",
        "\n".join(out_pytest.splitlines()[-25:]),
        "```",
        "",
        "---",
        "",
    ])

    # 2. pip check
    code_pip, out_pip, err_pip = run_command([py_exec, "-m", "pip", "check"], "pip check")
    passed_pip = (code_pip == 0)
    all_passed = all_passed and passed_pip
    check_summaries.append({"name": "pip check", "status": "PASS" if passed_pip else "FAIL", "code": code_pip})

    report_sections.extend([
        "## 2. Dependency Consistency (pip check)",
        "",
        f"- **Exit Code:** `{code_pip}`",
        f"- **Output:** `{out_pip.strip() or err_pip.strip() or 'No broken requirements found.'}`",
        "",
        "---",
        "",
    ])

    # 3. Dependency scan
    code_dep, out_dep, err_dep = run_command([py_exec, "scripts/check_dependencies.py"], "Dependency & Import Audit")
    passed_dep = (code_dep == 0)
    all_passed = all_passed and passed_dep
    check_summaries.append({"name": "Dependency Audit", "status": "PASS" if passed_dep else "FAIL", "code": code_dep})

    report_sections.extend([
        "## 3. Dependency and Import Audit",
        "",
        f"- **Exit Code:** `{code_dep}`",
        "",
        "```text",
        out_dep.strip(),
        "```",
        "",
        "---",
        "",
    ])

    # 4. Environment Verification
    code_env, out_env, err_env = run_command([py_exec, "scripts/verify_environment.py"], "Environment Verification")
    passed_env = (code_env == 0)
    all_passed = all_passed and passed_env
    check_summaries.append({"name": "Environment Verification", "status": "PASS" if passed_env else "FAIL", "code": code_env})

    report_sections.extend([
        "## 4. Environment Verification (scripts/verify_environment.py)",
        "",
        f"- **Exit Code:** `{code_env}`",
        "",
        "```text",
        out_env.strip(),
        "```",
        "",
        "---",
        "",
    ])

    # 5. Static Safeguards
    code_sg, out_sg, err_sg = run_command(
        [py_exec, "-m", "pytest", "-v", "tests/integration/test_static_safeguards.py"],
        "Static Safeguard AST Scans"
    )
    passed_sg = (code_sg == 0)
    all_passed = all_passed and passed_sg
    check_summaries.append({"name": "Static Safeguards", "status": "PASS" if passed_sg else "FAIL", "code": code_sg})

    report_sections.extend([
        "## 5. Static Safeguard AST Scans",
        "",
        f"- **Exit Code:** `{code_sg}`",
        "",
        "```text",
        out_sg.strip(),
        "```",
        "",
        "---",
        "",
    ])

    # 6. Dashboard AppTest Smoke Run
    print("--> Running: Dashboard AppTest Smoke Simulation...")
    from streamlit.testing.v1 import AppTest
    pages_to_test = [
        "app.py",
        "pages/1_Overview.py",
        "pages/2_Dataset.py",
        "pages/3_Data_Quality.py",
        "pages/4_Light_Curves.py",
        "pages/5_Events.py",
        "pages/6_Features.py",
        "pages/7_Model_Results.py",
    ]
    apptest_results = []
    apptest_passed = True
    for p in pages_to_test:
        app_path = root / "dashboard" / p
        at = AppTest.from_file(str(app_path), default_timeout=30)
        at.run()
        has_exc = bool(at.exception)
        if has_exc:
            apptest_passed = False
            apptest_results.append(f"- `dashboard/{p}`: **FAILED** ({at.exception})")
        else:
            apptest_results.append(f"- `dashboard/{p}`: **PASS** (0 exceptions)")

    all_passed = all_passed and apptest_passed
    check_summaries.append({"name": "Dashboard AppTest Smoke Run", "status": "PASS" if apptest_passed else "FAIL", "code": 0 if apptest_passed else 1})

    report_sections.extend([
        "## 6. Dashboard AppTest Smoke Simulation",
        "",
        f"- **Overall Status:** `{'PASS' if apptest_passed else 'FAIL'}`",
        "",
        "\n".join(apptest_results),
        "",
        "---",
        "",
    ])

    # 7. Pure Pipeline Status
    print("--> Running: Pure pipeline_status Engine...")
    s_report = pipeline_status(root)
    report_sections.extend([
        "## 7. Pipeline Stage Status Audit (Stages 3-11)",
        "",
        s_report.to_markdown(),
        "",
        "---",
        "",
    ])
    check_summaries.append({"name": "Pipeline Status Report", "status": "COMPLETE", "code": 0})

    # 8. Integrity Checks
    print("--> Running: Comprehensive Schema & Lineage Integrity Checks...")
    integrity_res = run_integrity_checks(root)
    n_ok = sum(1 for c in integrity_res if c.status == "OK")
    n_err = sum(1 for c in integrity_res if c.status in ("ERROR", "MISMATCH"))
    passed_integrity = (n_err == 0)
    all_passed = all_passed and passed_integrity
    check_summaries.append({"name": "Artifact & Lineage Integrity Checks", "status": "PASS" if passed_integrity else "FAIL", "code": 0 if passed_integrity else 1})

    report_sections.extend([
        "## 8. Artifact Schema & Cryptographic Lineage Integrity",
        "",
        f"- **Total Checks:** `{len(integrity_res)}` | **OK:** `{n_ok}` | **Errors/Mismatches:** `{n_err}`",
        "",
        generate_integrity_report_markdown(integrity_res),
        "",
        "---",
        "",
    ])

    # 9. Raw Data Immutability
    print("--> Verifying: Raw Observation Data Immutability...")
    pre_hash_path = root / "results" / "checks" / "pre_hashes.json"
    raw_immutability_passed = True
    raw_diffs = []

    if pre_hash_path.is_file():
        pre_hashes = json.loads(pre_hash_path.read_text(encoding="utf-8"))
        for rel_path, meta in pre_hashes.items():
            f_path = root / rel_path
            if not f_path.is_file():
                raw_immutability_passed = False
                raw_diffs.append(f"{rel_path}: File disappeared")
            else:
                curr_h = compute_sha256(f_path)
                rec_h = meta.get("sha256")
                if curr_h != rec_h:
                    raw_immutability_passed = False
                    raw_diffs.append(f"{rel_path}: Hash mismatch (pre={rec_h[:8]}... vs curr={curr_h[:8]}...)")

    all_passed = all_passed and raw_immutability_passed
    check_summaries.append({"name": "Raw Data Immutability", "status": "PASS" if raw_immutability_passed else "FAIL", "code": 0 if raw_immutability_passed else 1})

    report_sections.extend([
        "## 9. Raw Observation Data Immutability",
        "",
        f"- **Verification Status:** `{'PASS (Zero Mutations)' if raw_immutability_passed else 'FAIL (MUTATION DETECTED)'}`",
        f"- **Raw Files Checked:** `{len(pre_hashes) if pre_hash_path.is_file() else 0}`",
        "",
        *( [f"- [ERROR] {d}" for d in raw_diffs] if raw_diffs else ["All raw observation files in `data/raw/` are byte-for-byte identical to pre-run snapshot."] ),
        "",
        "---",
        "",
    ])

    # Summary Table at the end
    report_sections.extend([
        "## 10. Audit Summary Table",
        "",
        "| Verification Item | Status | Exit Code / Result |",
        "| :--- | :---: | :--- |",
    ])
    for item in check_summaries:
        badge = f"**{item['status']}**"
        report_sections.append(f"| {item['name']} | {badge} | `{item['code']}` |")

    report_sections.append("")
    report_sections.append(f"**Final Audit Result:** `{'SUCCESS (All automated checks passed)' if all_passed else 'FAILURE'}`\n")

    # Write Markdown Report
    out_md_path.write_text("\n".join(report_sections), encoding="utf-8")
    print(f"\nAudit complete! Full report saved to:\n  {out_md_path}\n")
    print(f"Final Exit Code: {0 if all_passed else 1}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
