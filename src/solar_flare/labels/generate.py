"""Guarded label generator skeleton for SOLARIS-A1 (Stage 6).

FIRST STATEMENT: Calls assert_labelling_approved().
Strictly refuses to run unless Gate G3 human approval is confirmed in both
docs/08_labelling_policy.md and config/decisions.yaml.
The non-refusal branch is exercised strictly by synthetic test fixtures in tmp_path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from solar_flare.labels.policy import assert_labelling_approved
from solar_flare.labels.matching import is_event_in_window


def generate_window_labels(
    windows_df: pd.DataFrame,
    events_df: pd.DataFrame,
    tolerance_seconds: float,
    policy_path: Optional[Union[Path, str]] = None,
    decisions_path: Optional[Union[Path, str]] = None,
    min_overlap_fraction: float = 0.5,
) -> pd.DataFrame:
    """Generate binary labels for sliding observation windows.
    
    FIRST STATEMENT ENFORCES GATE G3 HUMAN APPROVAL GUARD:
    Refuses execution if policy or decisions remain PENDING or unapproved.
    
    Parameters
    ----------
    windows_df : pd.DataFrame
        Table of sliding windows with window_id, start_time, end_time.
    events_df : pd.DataFrame
        Table of approved solar flare events with event_id, onset_time, end_time.
    tolerance_seconds : float
        Matching tolerance in seconds (Decision D-02).
    policy_path : Optional[Path or str]
        Path to labelling policy markdown.
    decisions_path : Optional[Path or str]
        Path to decisions.yaml.
    min_overlap_fraction : float
        Overlap fraction required for positive label assignment.
        
    Returns
    -------
    pd.DataFrame
        Labeled windows table with window_id, label, matched_events.
    """
    # 1. MANDATORY POLICY GUARD (Must execute first)
    assert_labelling_approved(policy_path=policy_path, decisions_path=decisions_path)

    # 2. Non-refusal execution branch (exercised only when approved)
    if tolerance_seconds is None:
        raise ValueError("tolerance_seconds must be provided explicitly.")

    records: List[Dict[str, Any]] = []
    for _, w_row in windows_df.iterrows():
        w_id = w_row["window_id"]
        w_s = float(w_row["start_time"])
        w_e = float(w_row["end_time"])

        matched_event_ids: List[str] = []
        for _, e_row in events_df.iterrows():
            e_id = e_row["event_id"]
            e_s = float(e_row["onset_time"])
            e_e = float(e_row["end_time"])

            if is_event_in_window(
                window_start=w_s,
                window_end=w_e,
                event_start=e_s,
                event_end=e_e,
                tolerance_seconds=tolerance_seconds,
                min_overlap_fraction=min_overlap_fraction,
            ):
                matched_event_ids.append(str(e_id))

        is_positive = int(len(matched_event_ids) > 0)
        records.append({
            "window_id": w_id,
            "start_time": w_s,
            "end_time": w_e,
            "label": is_positive,
            "matched_events": ";".join(matched_event_ids) if matched_event_ids else "NONE",
            "status": "APPROVED_LABELS" if is_positive else "VERIFIED_QUIET",
        })

    return pd.DataFrame(records)
