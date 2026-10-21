"""CLI script to run compatibility assessment for SOLARIS-A1 (Stage 6)."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from solar_flare.labels.compatibility import generate_compatibility_report


def main() -> None:
    rep = generate_compatibility_report()
    print("======================================================================")
    print("SOLARIS-A1 TEMPORAL COMPATIBILITY REPORT (STAGE 6)")
    print("======================================================================")
    print(f"Time System Confirmed: {rep['solexs_observation']['time_system_confirmed']}")
    for s in rep["sources_evaluated"]:
        print(f"- {s['source_id']} ({s['source_name']}): {s['compatibility_status']}")
    print("======================================================================")
    print("Report written to:")
    print(f"- results/labels/compatibility_report.json")
    print(f"- results/labels/compatibility_report.md")


if __name__ == "__main__":
    main()
