"""CLI tool to check the Gate G3 labelling approval guard status.

Invokes assert_labelling_approved() against docs/08_labelling_policy.md
and config/decisions.yaml. Expected behavior in Stage 6 is refusal.
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure src/ is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from solar_flare.labels.policy import assert_labelling_approved, LabellingNotApprovedError


def main() -> int:
    print("======================================================================")
    print("SOLARIS-A1 GATE G3 LABELLING POLICY GUARD CHECK")
    print("======================================================================")
    try:
        assert_labelling_approved()
        print("[SUCCESS] All labelling decisions and policy are APPROVED.")
        return 0
    except LabellingNotApprovedError as e:
        print("[REFUSAL ENFORCED] Gate G3 Guard successfully refused execution:")
        print(str(e))
        print("======================================================================")
        print("Supervised label generation is safely BLOCKED as required in Stage 6.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
