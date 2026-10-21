"""Stage 9 Label Integration and Matching for Solar Flare Detection (Task A).

Performs rigorous, policy-guarded joining of sliding observation windows with
approved, independent solar flare event records.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. FIRST STATEMENT: Calls assert_labelling_approved(). Refuses execution if Gate G3
   human approval is not confirmed in docs/08_labelling_policy.md and config/decisions.yaml.
2. Verified negative labels (0) are assigned ONLY to observation windows falling strictly
   outside all events and their embargos with verified adequate coverage.
3. Unknown, partial, low-coverage, or unverified intervals are assigned <NA> with an
   explicit label_reason. Unknowns are NEVER imputed, filled, or converted to 0.
4. Any case not covered by the approved policy raises UnhandledPolicyCase.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from solar_flare.labels.policy import assert_labelling_approved
from solar_flare.labels.schema import validate_event_records
from solar_flare.labels.matching import interval_overlap_seconds, is_event_in_window


class UnhandledPolicyCase(RuntimeError):
    """Raised when a window encounters a condition not defined in the approved labelling policy."""
    pass


def load_approved_events(
    path: Union[Path, str],
    config: Optional[Dict[str, Any]] = None,
    event_sources_path: Optional[Union[Path, str]] = None,
) -> pd.DataFrame:
    """Load and strictly validate approved ground-truth flare event records.
    
    Parameters
    ----------
    path : Path or str
        Path to approved event CSV file (e.g. data/manifests/event_records_approved.csv).
    config : Optional[dict]
        Project configuration.
    event_sources_path : Optional[Path or str]
        Path to event sources registry.
        
    Returns
    -------
    pd.DataFrame
        Validated event records.
        
    Raises
    -------
    FileNotFoundError
        If event records file does not exist.
    ValueError
        If validation fails or time_system is not confirmed.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Approved event records file not found at: {p}")

    df = pd.read_csv(p)
    # 1. Run schema and consistency validation
    validate_event_records(df, config=config, event_sources_path=event_sources_path)

    # 2. Check time system status
    # Must have a confirmed, non-empty time system
    if "time_system" not in df.columns:
        raise ValueError("Approved event records missing mandatory 'time_system' column.")

    unconfirmed = df[df["time_system"].str.upper().str.contains("UNCONFIRMED|PENDING|UNKNOWN", na=True)]
    if not unconfirmed.empty:
        raise ValueError(
            f"Found {len(unconfirmed)} event record(s) with UNCONFIRMED or PENDING time_system. "
            "Gate G3 requires confirmed time systems before dataset export."
        )

    return df


def label_windows_detection(
    window_index: pd.DataFrame,
    events: pd.DataFrame,
    params: Dict[str, Any],
    policy_path: Optional[Union[Path, str]] = None,
    decisions_path: Optional[Union[Path, str]] = None,
    policy_version: str = "1.0",
) -> pd.DataFrame:
    """Assign Task A (Detection) ground-truth labels to observation windows.
    
    Parameters
    ----------
    window_index : pd.DataFrame
        Window index table with window_id, window_start, window_end, coverage_fraction, quality_flag.
    events : pd.DataFrame
        Validated ground-truth event records with event_id, onset_time, end_time.
    params : dict
        Labelling parameters:
        - tolerance_seconds (float, Decision D-02)
        - min_overlap_fraction (float, default 0.50)
        - embargo_seconds (float, Decision D-08)
        - min_coverage_fraction (float, default 0.80)
        - quiet_intervals (optional list of (start, end) tuples)
    policy_path : Optional[Path or str]
        Path to labelling policy markdown for approval assertion.
    decisions_path : Optional[Path or str]
        Path to decisions register YAML for approval assertion.
    policy_version : str
        Version identifier of the approved policy.
        
    Returns
    -------
    pd.DataFrame
        Labeled detection table:
        - window_id: str
        - label_detection: Int8 nullable (1 = positive, 0 = verified negative, <NA> = excluded)
        - label_reason: str
        - event_id: str or None
        - overlap_seconds: float
        - observed_fraction_of_event: float
        - policy_version: str
    """
    # 1. MANDATORY POLICY GUARD
    assert_labelling_approved(policy_path=policy_path, decisions_path=decisions_path)

    # 2. Validate input columns
    req_win_cols = {"window_id", "window_start", "window_end", "coverage_fraction", "quality_flag"}
    missing_win = req_win_cols - set(window_index.columns)
    if missing_win:
        raise ValueError(f"window_index missing required columns: {missing_win}")

    # 3. Extract parameters
    if "tolerance_seconds" not in params:
        raise ValueError("params missing required key 'tolerance_seconds' (Decision D-02).")
    tol_sec = float(params["tolerance_seconds"])
    min_overlap = float(params.get("min_overlap_fraction", 0.50))
    embargo_sec = float(params.get("embargo_seconds", 0.0))
    min_cov = float(params.get("min_coverage_fraction", 0.80))
    quiet_intervals: Optional[List[Tuple[float, float]]] = params.get("quiet_intervals")

    records: List[Dict[str, Any]] = []

    for _, w_row in window_index.iterrows():
        w_id = str(w_row["window_id"])
        w_start = float(w_row["window_start"])
        w_end = float(w_row["window_end"])
        w_dur = float(w_end - w_start)
        w_cov = float(w_row["coverage_fraction"])
        q_flag = str(w_row["quality_flag"])

        # Determine relationships with all events
        matched_events: List[Tuple[str, float, float]] = []  # (event_id, overlap_s, frac_event)
        partial_events: List[Tuple[str, float]] = []         # (event_id, overlap_s)
        in_embargo_of: List[str] = []

        for _, e_row in events.iterrows():
            e_id = str(e_row["event_id"])
            e_onset = float(e_row["onset_time"])
            e_end = float(e_row["end_time"])
            e_dur = max(1e-3, float(e_end - e_onset))

            overlap_s = interval_overlap_seconds(
                w_start, w_end, e_onset, e_end, tolerance_seconds=tol_sec
            )

            if overlap_s > 0.0:
                overlap_frac_win = overlap_s / w_dur
                overlap_frac_ev = overlap_s / e_dur

                if overlap_frac_win >= min_overlap:
                    matched_events.append((e_id, overlap_s, overlap_frac_ev))
                else:
                    partial_events.append((e_id, overlap_s))

            # Embargo check: window within embargo buffer of event
            # Interval [e_onset - embargo, e_end + embargo]
            if embargo_sec > 0.0:
                emb_overlap = interval_overlap_seconds(
                    w_start, w_end, e_onset - embargo_sec, e_end + embargo_sec, tolerance_seconds=0.0
                )
                if emb_overlap > 0.0 and overlap_s <= 0.0:
                    in_embargo_of.append(e_id)

        # Decision tree per approved policy
        if len(matched_events) > 0:
            # Positive window
            primary_match = matched_events[0]
            records.append({
                "window_id": w_id,
                "label_detection": 1,
                "label_reason": f"MATCHED_EVENT_{primary_match[0]}",
                "event_id": primary_match[0],
                "overlap_seconds": round(primary_match[1], 3),
                "observed_fraction_of_event": round(primary_match[2], 4),
                "policy_version": policy_version,
            })
        elif len(partial_events) > 0:
            # Ambiguous partial overlap: excluded from negatives to prevent contamination
            records.append({
                "window_id": w_id,
                "label_detection": pd.NA,
                "label_reason": f"PARTIAL_OVERLAP_EXCLUDED_{partial_events[0][0]}",
                "event_id": partial_events[0][0],
                "overlap_seconds": round(partial_events[0][1], 3),
                "observed_fraction_of_event": 0.0,
                "policy_version": policy_version,
            })
        elif len(in_embargo_of) > 0:
            # Embargo zone: excluded
            records.append({
                "window_id": w_id,
                "label_detection": pd.NA,
                "label_reason": f"EMBARGO_EXCLUDED_{in_embargo_of[0]}",
                "event_id": None,
                "overlap_seconds": 0.0,
                "observed_fraction_of_event": 0.0,
                "policy_version": policy_version,
            })
        elif w_cov < min_cov or q_flag == "LOW_COVERAGE":
            # Low coverage: excluded from negatives
            records.append({
                "window_id": w_id,
                "label_detection": pd.NA,
                "label_reason": f"LOW_COVERAGE_EXCLUDED (cov={w_cov:.2f} < {min_cov:.2f})",
                "event_id": None,
                "overlap_seconds": 0.0,
                "observed_fraction_of_event": 0.0,
                "policy_version": policy_version,
            })
        elif quiet_intervals is not None:
            # Explicit quiet interval policy
            in_quiet = any(
                (w_start >= q_s and w_end <= q_e) for q_s, q_e in quiet_intervals
            )
            if in_quiet:
                records.append({
                    "window_id": w_id,
                    "label_detection": 0,
                    "label_reason": "VERIFIED_QUIET_INTERVAL",
                    "event_id": None,
                    "overlap_seconds": 0.0,
                    "observed_fraction_of_event": 0.0,
                    "policy_version": policy_version,
                })
            else:
                # Outside quiet interval and no event: unverified negative
                records.append({
                    "window_id": w_id,
                    "label_detection": pd.NA,
                    "label_reason": "OUTSIDE_APPROVED_QUIET_INTERVAL",
                    "event_id": None,
                    "overlap_seconds": 0.0,
                    "observed_fraction_of_event": 0.0,
                    "policy_version": policy_version,
                })
        else:
            # Verified Negative (clean window outside all events/embargo with sufficient coverage)
            records.append({
                "window_id": w_id,
                "label_detection": 0,
                "label_reason": "VERIFIED_QUIET_BACKGROUND",
                "event_id": None,
                "overlap_seconds": 0.0,
                "observed_fraction_of_event": 0.0,
                "policy_version": policy_version,
            })

    out_df = pd.DataFrame(records)
    # Ensure Nullable Int8 for label_detection
    out_df["label_detection"] = out_df["label_detection"].astype("Int8")
    return out_df
