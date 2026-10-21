"""Stage 13: Pipeline Status, Integrity Checking, and Dashboard Integration Execution Script."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))
sys.path.insert(0, str(root_dir))

from solar_flare.paths import project_root
from solar_flare.status import pipeline_status
from solar_flare.integrity import run_integrity_checks, generate_integrity_report_markdown


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def snapshot_dir(dir_path: Path, ignore_subdirs: list[str] = None) -> dict[str, str]:
    ignore_subdirs = ignore_subdirs or []
    hashes = {}
    if not dir_path.is_dir():
        return hashes
    for p in sorted(dir_path.rglob("*")):
        if p.is_file():
            # Check if any parent part is in ignore_subdirs
            if any(part in ignore_subdirs for part in p.parts):
                continue
            rel = str(p.relative_to(project_root())).replace("\\", "/")
            hashes[rel] = compute_sha256(p)
    return hashes


def main() -> int:
    root = project_root()
    integration_dir = root / "results" / "integration"
    integration_dir.mkdir(parents=True, exist_ok=True)

    print("=== SOLARIS-A1 Stage 13 Integration Audit Execution ===")

    # 1. Snapshot raw data and results before running
    print("\n[1/5] Verifying pre-execution snapshot...")
    raw_hashes_before = snapshot_dir(root / "data" / "raw")
    results_hashes_before = snapshot_dir(root / "results", ignore_subdirs=["integration"])
    print(f"  Raw files snapshotted: {len(raw_hashes_before)}")
    print(f"  Results files snapshotted: {len(results_hashes_before)}")

    # 2. Run pure pipeline status
    print("\n[2/5] Running pure pipeline_status engine...")
    status_report = pipeline_status(root)
    status_json_path = integration_dir / "pipeline_status.json"
    status_md_path = integration_dir / "pipeline_status.md"

    status_json_path.write_text(json.dumps(status_report.to_dict(), indent=2), encoding="utf-8")
    status_md_path.write_text(status_report.to_markdown(), encoding="utf-8")
    print(f"  Saved status to {status_json_path} and {status_md_path}")
    print(f"  Stages audited: {len(status_report.stages)}")
    for s in status_report.stages:
        print(f"    - Stage {s.stage_id:2d} ({s.stage_name:25s}): {s.status:12s} [{s.gate_id or '-'}]")

    # 3. Run comprehensive integrity checks
    print("\n[3/5] Running comprehensive schema & cryptographic integrity checks...")
    integrity_checks = run_integrity_checks(root)
    integrity_md_path = integration_dir / "integrity_report.md"
    integrity_md_path.write_text(generate_integrity_report_markdown(integrity_checks), encoding="utf-8")
    print(f"  Saved integrity report to {integrity_md_path}")
    print(f"  Checks performed: {len(integrity_checks)}")
    n_ok = sum(1 for c in integrity_checks if c.status == "OK")
    n_other = len(integrity_checks) - n_ok
    print(f"    OK: {n_ok}, Non-OK: {n_other}")

    # 4. Run AppTest read-only execution test
    print("\n[4/5] Running AppTest read-only simulation...")
    from streamlit.testing.v1 import AppTest

    pages_to_test = [
        "1_Overview.py",
        "2_Dataset.py",
        "3_Data_Quality.py",
        "4_Light_Curves.py",
        "5_Events.py",
        "6_Features.py",
        "7_Model_Results.py",
    ]
    for p_name in pages_to_test:
        page_path = root / "dashboard" / "pages" / p_name
        at_page = AppTest.from_file(str(page_path), default_timeout=30)
        at_page.run()
        assert not at_page.exception, f"AppTest exception on {p_name}: {at_page.exception}"
        print(f"    - {p_name}: passed (0 exceptions)")
    print("  AppTest simulation passed with 0 runtime exceptions across all tested pages.")

    # 5. Verify post-execution snapshot immutability
    print("\n[5/5] Verifying post-execution data & results immutability...")
    raw_hashes_after = snapshot_dir(root / "data" / "raw")
    results_hashes_after = snapshot_dir(root / "results", ignore_subdirs=["integration"])

    post_hashes_path = integration_dir / "post_hashes.json"
    post_hashes_path.write_text(
        json.dumps({"raw": raw_hashes_after, "results": results_hashes_after}, indent=2),
        encoding="utf-8",
    )

    # Immutability assertions
    raw_mutations = {k: (raw_hashes_before.get(k), raw_hashes_after.get(k)) for k in set(raw_hashes_before) | set(raw_hashes_after) if raw_hashes_before.get(k) != raw_hashes_after.get(k)}
    results_mutations = {k: (results_hashes_before.get(k), results_hashes_after.get(k)) for k in set(results_hashes_before) | set(results_hashes_after) if results_hashes_before.get(k) != results_hashes_after.get(k)}

    if raw_mutations:
        print(f"  CRITICAL ERROR: data/raw/ was MUTATED: {raw_mutations}")
        return 1

    if results_mutations:
        print(f"  CRITICAL ERROR: results/ was MUTATED: {results_mutations}")
        return 1

    print("  Zero mutations detected in data/raw/ and results/ (outside results/integration/).")
    print("\n=== Stage 13 Integration Audit Completed Successfully ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
