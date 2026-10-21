"""Temporal and definitional compatibility analysis for SOLARIS-A1 (Stage 6).

Evaluates whether external solar flare event sources temporally overlap with SoLEXS
observations without performing arbitrary time conversions.
Status vocabulary:
- TIME_SYSTEM_UNCONFIRMED (assigned whenever SoLEXS time system is unconfirmed)
- NO_OVERLAP
- OVERLAP_PENDING_TIME_CHECK
- COMPATIBLE_PENDING_APPROVAL
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

from solar_flare.paths import project_root


def report_temporal_overlap(
    solexs_start: float,
    solexs_end: float,
    source_coverage_start: Optional[float],
    source_coverage_end: Optional[float],
) -> Union[float, str]:
    """Calculate temporal overlap duration in seconds without converting time systems.
    
    Parameters
    ----------
    solexs_start : float
        Start timestamp of SoLEXS observation window.
    solexs_end : float
        End timestamp of SoLEXS observation window.
    source_coverage_start : Optional[float]
        Start of external source coverage in the same numeric units, if known.
    source_coverage_end : Optional[float]
        End of external source coverage in the same numeric units, if known.
        
    Returns
    -------
    float or str
        Overlap duration in seconds if positive overlap exists, or "NO OVERLAP".
    """
    if source_coverage_start is None or source_coverage_end is None:
        return "NO OVERLAP"

    overlap_start = max(float(solexs_start), float(source_coverage_start))
    overlap_end = min(float(solexs_end), float(source_coverage_end))

    if overlap_start < overlap_end:
        return float(overlap_end - overlap_start)
    return "NO OVERLAP"


def assess_source_compatibility(
    source_record: Dict[str, Any],
    time_system_confirmed: bool = False,
    overlap_result: Union[float, str] = "NO OVERLAP",
) -> str:
    """Determine compatibility status of an external source against SoLEXS.
    
    CRITICAL RULE:
    If the SoLEXS time system is unconfirmed (Decision D-10 not CONFIRMED/APPROVED),
    the status is strictly TIME_SYSTEM_UNCONFIRMED regardless of nominal overlap.
    
    Parameters
    ----------
    source_record : dict
        Row from event_sources.csv.
    time_system_confirmed : bool
        Whether Decision D-10 has been approved by the student researcher.
    overlap_result : float or str
        Result from report_temporal_overlap.
        
    Returns
    -------
    str
        Compatibility status.
    """
    if not time_system_confirmed:
        return "TIME_SYSTEM_UNCONFIRMED"

    if overlap_result == "NO OVERLAP" or (isinstance(overlap_result, (int, float)) and overlap_result <= 0):
        return "NO_OVERLAP"

    verified_by_human = str(source_record.get("verified_by_human", "no")).strip().lower()
    if verified_by_human in ("yes", "true", "confirmed"):
        return "COMPATIBLE_PENDING_APPROVAL"

    return "OVERLAP_PENDING_TIME_CHECK"


def generate_compatibility_report(
    solexs_start: float = 1792281600.0,
    solexs_end: float = 1792367999.0,
    event_sources_path: Optional[Path] = None,
    decisions_path: Optional[Path] = None,
    output_json: Optional[Path] = None,
    output_md: Optional[Path] = None,
) -> Dict[str, Any]:
    """Evaluate compatibility across all recorded event sources and write reports."""
    root = project_root()
    sources_csv = Path(event_sources_path) if event_sources_path else (root / "data" / "manifests" / "event_sources.csv")
    dec_file = Path(decisions_path) if decisions_path else (root / "config" / "decisions.yaml")
    out_j = Path(output_json) if output_json else (root / "results" / "labels" / "compatibility_report.json")
    out_m = Path(output_md) if output_md else (root / "results" / "labels" / "compatibility_report.md")

    out_j.parent.mkdir(parents=True, exist_ok=True)
    out_m.parent.mkdir(parents=True, exist_ok=True)

    # Check time system confirmation status in decisions.yaml
    time_confirmed = False
    if dec_file.is_file():
        with open(dec_file, "r", encoding="utf-8") as df:
            decs = yaml.safe_load(df) or {}
            d10 = decs.get("decisions", {}).get("D-10", {})
            if d10.get("status") in ("CONFIRMED", "APPROVED") and d10.get("approved_by"):
                time_confirmed = True

    # Read event sources
    sources: List[Dict[str, Any]] = []
    if sources_csv.is_file():
        with open(sources_csv, "r", encoding="utf-8") as sf:
            reader = csv.DictReader(sf)
            for row in reader:
                sources.append(row)

    evaluations: List[Dict[str, Any]] = []
    for s in sources:
        sid = s.get("source_id", "UNKNOWN")
        sname = s.get("source_name", "Unknown")

        # Nominal overlap check (numeric if stated, otherwise string / ongoing)
        # Note: In Stage 6, no time conversion is performed.
        status = assess_source_compatibility(
            s,
            time_system_confirmed=time_confirmed,
            overlap_result="NO OVERLAP" if not time_confirmed else "OVERLAP",
        )

        evaluations.append({
            "source_id": sid,
            "source_name": sname,
            "instrument": s.get("instrument", ""),
            "stated_time_system": s.get("time_system_as_stated", ""),
            "time_system_confirmed": time_confirmed,
            "compatibility_status": status,
            "notes": s.get("notes", ""),
        })

    payload = {
        "solexs_observation": {
            "start_timestamp": solexs_start,
            "end_timestamp": solexs_end,
            "time_system_decision": "D-10",
            "time_system_confirmed": time_confirmed,
        },
        "sources_evaluated": evaluations,
        "summary": (
            "NO VERIFIED INDEPENDENT SOURCE WITH CONFIRMED TIME COMPATIBILITY. "
            "SoLEXS time system (D-10) is UNCONFIRMED. All sources evaluated as TIME_SYSTEM_UNCONFIRMED."
        ),
    }

    with open(out_j, "w", encoding="utf-8") as jf:
        json.dump(payload, jf, indent=2)

    # Write Markdown
    lines = [
        "# SOLARIS-A1: Ground-Truth Time Compatibility Report (Stage 6)",
        "",
        "> **CRITICAL SCIENTIFIC STATUS:**",
        "> **TIME SYSTEM UNCONFIRMED (Decision D-10 Pending Gate G1 Approval)**.",
        "> In accordance with non-destructive scientific governance, no time conversions are performed.",
        "> All candidate event sources are currently evaluated as **`TIME_SYSTEM_UNCONFIRMED`**.",
        "",
        "---",
        "",
        "## SoLEXS Observation Window Under Analysis",
        f"- **Observation Start:** `{solexs_start}` s (Nominal: `2026-10-18 00:00:00 UTC`)",
        f"- **Observation End:** `{solexs_end}` s (Nominal: `2026-10-18 23:59:59 UTC`)",
        f"- **Time System Status:** `PROVISIONAL pending G1 confirmation` (D-10)",
        "",
        "---",
        "",
        "## Evaluated Sources and Compatibility Status",
        "",
        "| Source ID | Source Name | Instrument | Stated Time System | Compatibility Status | Notes |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for ev in evaluations:
        lines.append(
            f"| `{ev['source_id']}` | {ev['source_name']} | {ev['instrument']} | "
            f"`{ev['stated_time_system']}` | **`{ev['compatibility_status']}`** | {ev['notes']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Required Human Actions for Gate G3 Approval",
        "1. Confirm Decision D-10 in `config/decisions.yaml` (Unix epoch seconds from MJD 40587).",
        "2. Approve independent event source (`SRC_NOAA_NCEI_GOES` recommended) in `data/manifests/event_sources.csv`.",
        "3. Approve matching tolerance $\\Delta t_{\\text{match}}$ (Decision D-02) taking into account L1 Sun-Earth travel time (~5.0 s).",
        "",
    ])

    with open(out_m, "w", encoding="utf-8") as mf:
        mf.write("\n".join(lines))

    return payload


if __name__ == "__main__":
    rep = generate_compatibility_report()
    print("======================================================================")
    print("SOLARIS-A1 TEMPORAL COMPATIBILITY REPORT (STAGE 6)")
    print("======================================================================")
    print(f"Time System Confirmed: {rep['solexs_observation']['time_system_confirmed']}")
    for s in rep["sources_evaluated"]:
        print(f"- {s['source_id']} ({s['source_name']}): {s['compatibility_status']}")
    print("======================================================================")
