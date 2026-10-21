"""Target generation for Task A (Detection) and Task B (Pre-Flare Forecasting).

Task A Target: Is a verified solar flare active in observation window [w_start, w_end]?
Task B Target: Does a verified flare onset fall within the future horizon (t0, t0 + H]?

CRITICAL SAFEGUARDS:
1. Target generation for Task B (prediction) strictly refuses execution unless
   docs/22_forecasting_policy.md and forecasting decisions in config/decisions.yaml
   are formally APPROVED by the human researcher.
2. Forecasting targets never peek past reference time t0 = window_end when formulating features.
3. Unknown, embargoed, ongoing-event, or right-censored intervals are recorded as <NA> with
   reason codes. They are NEVER converted to 0.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import yaml

from solar_flare.paths import project_root
from solar_flare.export.join_labels import label_windows_detection


class ForecastingNotApprovedError(RuntimeError):
    """Raised when Task B forecasting export is invoked without Gate G6 human approval."""
    pass


def assert_forecasting_approved(
    policy_path: Optional[Union[Path, str]] = None,
    decisions_path: Optional[Union[Path, str]] = None,
) -> bool:
    """Assert that Gate G6 human approval has been recorded for pre-flare forecasting.
    
    Parameters
    ----------
    policy_path : Optional[Path or str]
        Path to docs/22_forecasting_policy.md.
    decisions_path : Optional[Path or str]
        Path to config/decisions.yaml.
        
    Returns
    -------
    bool
        True if approved.
        
    Raises
    -------
    ForecastingNotApprovedError
        If policy file is missing, status is not APPROVED, or decisions are PENDING.
    """
    root = project_root()
    p_path = Path(policy_path) if policy_path else (root / "docs" / "22_forecasting_policy.md")
    d_path = Path(decisions_path) if decisions_path else (root / "config" / "decisions.yaml")

    missing_reasons: List[str] = []

    # 1. Inspect forecasting policy document
    if not p_path.is_file():
        missing_reasons.append(f"Forecasting policy document not found: {p_path}")
    else:
        text = p_path.read_text(encoding="utf-8")
        approved_pattern = re.compile(
            r"^Status:\s*APPROVED\s+by\s+.+?,\s*date\s+\d{4}-\d{2}-\d{2}",
            re.MULTILINE | re.IGNORECASE,
        )
        if not approved_pattern.search(text):
            curr_match = re.search(r"^Status:\s*(.+)$", text, re.MULTILINE)
            curr_status = curr_match.group(1).strip() if curr_match else "UNKNOWN / NOT SPECIFIED"
            missing_reasons.append(
                f"Forecasting policy status in '{p_path.name}' is '{curr_status}'. "
                "Requires exact format 'Status: APPROVED by <name>, date <YYYY-MM-DD>'."
            )

    # 2. Inspect decisions.yaml for forecasting items (D-07, D-08)
    req_decs = ["D-07", "D-08"]
    if not d_path.is_file():
        missing_reasons.append(f"Decisions register not found: {d_path}")
    else:
        with open(d_path, "r", encoding="utf-8") as df:
            decs_data = yaml.safe_load(df) or {}
        decs_dict = decs_data.get("decisions", {})

        for d_id in req_decs:
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
                missing_reasons.append(f"Decision '{d_id}' marked APPROVED but has null/empty value")

    if missing_reasons:
        msg = (
            "Task B forecasting export is strictly BLOCKED pending Gate G6 human approval.\n"
            "The following items must be confirmed by the human researcher:\n"
            + "\n".join(f"  - {r}" for r in missing_reasons)
        )
        raise ForecastingNotApprovedError(msg)

    return True


def detection_target(
    window_index: pd.DataFrame,
    events: pd.DataFrame,
    params: Dict[str, Any],
    policy_path: Optional[Union[Path, str]] = None,
    decisions_path: Optional[Union[Path, str]] = None,
) -> pd.DataFrame:
    """Wrapper generating Task A detection target table."""
    return label_windows_detection(
        window_index=window_index,
        events=events,
        params=params,
        policy_path=policy_path,
        decisions_path=decisions_path,
    )


def prediction_target(
    window_index: pd.DataFrame,
    onsets: pd.DataFrame,
    horizon_seconds: float,
    embargo_seconds: float,
    min_coverage_fraction: float = 0.80,
    ongoing_event_policy: str = "EXCLUDE",
    policy_path: Optional[Union[Path, str]] = None,
    decisions_path: Optional[Union[Path, str]] = None,
    policy_version: str = "1.0",
) -> pd.DataFrame:
    """Generate Task B (Pre-Flare Forecasting) ground-truth labels for sliding windows.
    
    Parameters
    ----------
    window_index : pd.DataFrame
        Window table containing window_id, window_end (reference time t0),
        and optionally segment_end.
    onsets : pd.DataFrame
        Verified flare event records with onset_time and end_time.
    horizon_seconds : float
        Forecasting horizon duration H in seconds (Decision D-07).
    embargo_seconds : float
        Pre-window embargo duration before t0.
    min_coverage_fraction : float
        Minimum horizon observation coverage required for negative labels.
    ongoing_event_policy : str
        Policy for windows where an event is active at t0 ("EXCLUDE" or "ALLOW").
    policy_path : Optional[Path or str]
        Path to docs/22_forecasting_policy.md.
    decisions_path : Optional[Path or str]
        Path to config/decisions.yaml.
    policy_version : str
        Policy version string.
        
    Returns
    -------
    pd.DataFrame
        Task B target table:
        - window_id: str
        - label_prediction: Int8 nullable (1 = onset in (t0, t0+H], 0 = verified clean, <NA> = excluded)
        - next_onset_time: float or NaN
        - seconds_to_next_onset: float or NaN
        - excluded_reason: str or None
        - ongoing_event_at_t0: bool
        - horizon_coverage_fraction: float
        - policy_version: str
    """
    # 1. MANDATORY POLICY GUARD (Must execute first)
    assert_forecasting_approved(policy_path=policy_path, decisions_path=decisions_path)

    if horizon_seconds <= 0.0:
        raise ValueError(f"horizon_seconds must be positive, got {horizon_seconds}")
    if embargo_seconds < 0.0:
        raise ValueError(f"embargo_seconds cannot be negative, got {embargo_seconds}")

    records: List[Dict[str, Any]] = []

    # Sort onsets for efficient search
    event_list = []
    if onsets is not None and not onsets.empty:
        for _, row in onsets.iterrows():
            event_list.append({
                "event_id": str(row["event_id"]),
                "onset": float(row["onset_time"]),
                "end": float(row["end_time"]),
            })
    event_list.sort(key=lambda x: x["onset"])

    for _, w_row in window_index.iterrows():
        w_id = str(w_row["window_id"])
        t0 = float(w_row["window_end"])
        seg_end = float(w_row["segment_end"]) if "segment_end" in w_row else None

        # 1. Check if an ongoing flare is currently active at t0
        ongoing_at_t0 = any(
            (ev["onset"] <= t0 <= ev["end"]) for ev in event_list
        )

        # 2. Check if an onset occurred recently during embargo (t0 - embargo, t0]
        recent_embargo_onset = any(
            (t0 - embargo_seconds < ev["onset"] <= t0) for ev in event_list
        ) if embargo_seconds > 0.0 else False

        # 3. Future onsets strictly after t0
        future_onsets = [ev for ev in event_list if ev["onset"] > t0]
        next_ev = future_onsets[0] if future_onsets else None
        next_onset_t = next_ev["onset"] if next_ev else np.nan
        secs_to_next = (next_onset_t - t0) if next_ev else np.nan

        # 4. Onsets in prediction horizon (t0, t0 + H]
        horizon_end = t0 + horizon_seconds
        onsets_in_horizon = [
            ev for ev in future_onsets if ev["onset"] <= horizon_end
        ]

        # 5. Check horizon coverage fraction
        if seg_end is not None:
            observed_horizon_s = max(0.0, min(seg_end, horizon_end) - t0)
            horizon_cov = observed_horizon_s / horizon_seconds
        else:
            horizon_cov = 1.0

        # Decision tree
        if ongoing_at_t0 and ongoing_event_policy.upper() == "EXCLUDE":
            records.append({
                "window_id": w_id,
                "label_prediction": pd.NA,
                "next_onset_time": next_onset_t,
                "seconds_to_next_onset": secs_to_next,
                "excluded_reason": "ONGOING_EVENT_AT_T0",
                "ongoing_event_at_t0": True,
                "horizon_coverage_fraction": round(horizon_cov, 4),
                "policy_version": policy_version,
            })
        elif recent_embargo_onset:
            records.append({
                "window_id": w_id,
                "label_prediction": pd.NA,
                "next_onset_time": next_onset_t,
                "seconds_to_next_onset": secs_to_next,
                "excluded_reason": "RECENT_ONSET_IN_EMBARGO",
                "ongoing_event_at_t0": ongoing_at_t0,
                "horizon_coverage_fraction": round(horizon_cov, 4),
                "policy_version": policy_version,
            })
        elif len(onsets_in_horizon) > 0:
            # Positive prediction window: verified onset will occur in (t0, t0 + H]
            first_h_onset = onsets_in_horizon[0]
            records.append({
                "window_id": w_id,
                "label_prediction": 1,
                "next_onset_time": first_h_onset["onset"],
                "seconds_to_next_onset": round(first_h_onset["onset"] - t0, 3),
                "excluded_reason": None,
                "ongoing_event_at_t0": ongoing_at_t0,
                "horizon_coverage_fraction": round(horizon_cov, 4),
                "policy_version": policy_version,
            })
        elif horizon_cov < min_coverage_fraction:
            # Insufficient observed data within forecast horizon (censored / observation boundary)
            records.append({
                "window_id": w_id,
                "label_prediction": pd.NA,
                "next_onset_time": next_onset_t,
                "seconds_to_next_onset": secs_to_next,
                "excluded_reason": f"INSUFFICIENT_HORIZON_COVERAGE ({horizon_cov:.2f} < {min_coverage_fraction:.2f})",
                "ongoing_event_at_t0": ongoing_at_t0,
                "horizon_coverage_fraction": round(horizon_cov, 4),
                "policy_version": policy_version,
            })
        else:
            # Verified Negative prediction window: clean horizon with adequate coverage
            records.append({
                "window_id": w_id,
                "label_prediction": 0,
                "next_onset_time": next_onset_t,
                "seconds_to_next_onset": secs_to_next,
                "excluded_reason": None,
                "ongoing_event_at_t0": ongoing_at_t0,
                "horizon_coverage_fraction": round(horizon_cov, 4),
                "policy_version": policy_version,
            })

    out_df = pd.DataFrame(records)
    out_df["label_prediction"] = out_df["label_prediction"].astype("Int8")
    return out_df
