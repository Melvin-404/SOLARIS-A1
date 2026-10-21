"""Event comparison scaffolding for SOLARIS-A1 (Stage 5).

Compares candidate transient intervals against independent ground-truth event records.
CRITICAL CONSTRAINT:
When no external event catalogue is supplied, returns strictly:
'NOT PERFORMED — no independent event records supplied'.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd


def compare_candidates_to_events(
    candidates: pd.DataFrame | List[Dict[str, Any]],
    events_df: Optional[pd.DataFrame] = None,
    tolerance_seconds: float = 60.0,
) -> Dict[str, Any]:
    """Compare candidate transient intervals against independent solar flare event records.
    
    Parameters
    ----------
    candidates : pd.DataFrame or list of dicts
        Candidate burst intervals produced by candidate_intervals.
    events_df : Optional[pd.DataFrame]
        Ground-truth event records (e.g. GOES, PRADAN).
    tolerance_seconds : float
        Temporal association tolerance window (from config, Decision D-02).
        
    Returns
    -------
    dict
        Structured comparison result. Returns status 'NOT PERFORMED' if events_df is None or empty.
    """
    cand_df = candidates if isinstance(candidates, pd.DataFrame) else pd.DataFrame(candidates)
    n_candidates = len(cand_df)

    if events_df is None or events_df.empty or len(events_df) == 0:
        return {
            "status": "NOT PERFORMED — no independent event records supplied",
            "n_candidates": n_candidates,
            "n_events": 0,
            "matches": [],
            "tolerance_seconds": tolerance_seconds,
            "detail": (
                "Ground-truth flare event catalogue not yet supplied. "
                "Event comparison is strictly NOT PERFORMED. "
                "Event sourcing and label verification will be conducted in Stage 6."
            ),
        }

    # Evaluation branch for synthetic testing or future Stage 6 execution
    matches: List[Dict[str, Any]] = []

    # Expected column mappings for events table (documented in docs/06_event_record_schema.md)
    start_col = "event_start" if "event_start" in events_df.columns else "start_time"
    end_col = "event_end" if "event_end" in events_df.columns else "end_time"
    id_col = "event_id" if "event_id" in events_df.columns else "id"

    if start_col not in events_df.columns or end_col not in events_df.columns:
        return {
            "status": "ERROR — events_df missing required timestamp columns",
            "n_candidates": n_candidates,
            "n_events": len(events_df),
            "matches": [],
            "tolerance_seconds": tolerance_seconds,
            "detail": f"Required start/end columns ('{start_col}', '{end_col}') not found in events_df.",
        }

    for _, c_row in cand_df.iterrows():
        c_id = c_row.get("candidate_id", "UNKNOWN")
        c_start = float(c_row["start"])
        c_end = float(c_row["end"])

        for _, e_row in events_df.iterrows():
            e_id = e_row.get(id_col, "UNKNOWN")
            e_start = float(e_row[start_col])
            e_end = float(e_row[end_col])

            # Check overlap within tolerance
            overlap_start = max(c_start - tolerance_seconds, e_start)
            overlap_end = min(c_end + tolerance_seconds, e_end)

            if overlap_start <= overlap_end:
                matches.append({
                    "candidate_id": c_id,
                    "event_id": e_id,
                    "candidate_start": c_start,
                    "candidate_end": c_end,
                    "event_start": e_start,
                    "event_end": e_end,
                    "temporal_offset_s": float(abs(c_start - e_start)),
                })

    return {
        "status": "COMPLETED",
        "n_candidates": n_candidates,
        "n_events": len(events_df),
        "matches": matches,
        "tolerance_seconds": tolerance_seconds,
        "detail": f"Matched {len(matches)} candidate intervals against {len(events_df)} event records.",
    }
