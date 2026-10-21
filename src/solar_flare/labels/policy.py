"""Policy guard asserting human researcher approval for supervised labelling.

Enforces Gate G3:
Supervised label generation strictly refuses to run unless:
1. docs/08_labelling_policy.md contains 'Status: APPROVED by <name>, date <YYYY-MM-DD>'
2. config/decisions.yaml contains APPROVED entries for D-01, D-02, D-03, D-04, D-08, D-10, D-15
   with non-null, non-empty values.

The guard reads files directly on every invocation; it does not cache any flag.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union
import yaml


from solar_flare.paths import project_root


class LabellingNotApprovedError(RuntimeError):
    """Raised when label generation is invoked without formal Gate G3 human approval."""
    pass


def assert_labelling_approved(
    policy_path: Optional[Union[Path, str]] = None,
    decisions_path: Optional[Union[Path, str]] = None,
) -> bool:
    """Verify that Gate G3 human approval has been formally recorded in policy and decisions.
    
    Parameters
    ----------
    policy_path : Optional[Path or str]
        Path to docs/08_labelling_policy.md.
    decisions_path : Optional[Path or str]
        Path to config/decisions.yaml.
        
    Returns
    -------
    bool
        True if all approval criteria are met.
        
    Raises
    -------
    LabellingNotApprovedError
        If any policy status or required decision remains PENDING, PROVISIONAL, or unapproved.
    """
    root = project_root()
    p_path = Path(policy_path) if policy_path else (root / "docs" / "08_labelling_policy.md")
    d_path = Path(decisions_path) if decisions_path else (root / "config" / "decisions.yaml")

    missing_reasons: List[str] = []

    # 1. Inspect policy document status line
    if not p_path.is_file():
        missing_reasons.append(f"Policy file not found: {p_path}")
    else:
        text = p_path.read_text(encoding="utf-8")
        approved_pattern = re.compile(
            r"^Status:\s*APPROVED\s+by\s+.+?,\s*date\s+\d{4}-\d{2}-\d{2}",
            re.MULTILINE | re.IGNORECASE,
        )
        if not approved_pattern.search(text):
            # Extract current status line for diagnostic message
            curr_match = re.search(r"^Status:\s*(.+)$", text, re.MULTILINE)
            curr_status = curr_match.group(1).strip() if curr_match else "UNKNOWN / NOT SPECIFIED"
            missing_reasons.append(
                f"Policy status line in '{p_path.name}' is '{curr_status}'. "
                "Requires exact format 'Status: APPROVED by <name>, date <YYYY-MM-DD>'."
            )

    # 2. Inspect decisions.yaml required entries
    required_decisions = ["D-01", "D-02", "D-03", "D-04", "D-08", "D-10", "D-15"]

    if not d_path.is_file():
        missing_reasons.append(f"Decisions register not found: {d_path}")
    else:
        with open(d_path, "r", encoding="utf-8") as df:
            decs_data = yaml.safe_load(df) or {}

        decs_dict = decs_data.get("decisions", {})
        for d_id in required_decisions:
            entry = decs_dict.get(d_id)
            if not entry:
                missing_reasons.append(f"Decision '{d_id}' missing from {d_path.name}")
                continue

            status = str(entry.get("status", "")).strip().upper()
            val = entry.get("value")
            is_val_empty = (
                val is None
                or str(val).strip() == ""
                or str(val).strip().lower() == "null"
            )

            if status != "APPROVED":
                missing_reasons.append(f"Decision '{d_id}' status is '{status}' (required: 'APPROVED')")
            elif is_val_empty:
                missing_reasons.append(f"Decision '{d_id}' is marked APPROVED but has null/empty value")

    if missing_reasons:
        msg = (
            "Supervised labelling is strictly BLOCKED pending Gate G3 human approval.\n"
            "The following approval items must be confirmed by the human researcher:\n"
            + "\n".join(f"  - {r}" for r in missing_reasons)
        )
        raise LabellingNotApprovedError(msg)

    return True
