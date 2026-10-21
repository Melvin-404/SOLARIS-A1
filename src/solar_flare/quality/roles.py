"""Column-role evidence compilation for SOLARIS-A1 (Stage 4).

Inspects inventory metadata and candidate table columns to compile evidence
for time, count/rate, quality flag, GTI start/stop, and energy/channel indicators.
All candidate roles are strictly tagged as PROVISIONAL or UNRESOLVED with the note
"requires human confirmation (G1)".
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from astropy.io import fits


def compile_file_role_evidence(file_path: Path) -> Dict[str, Any]:
    """Extract column-role evidence from a single FITS file in a read-only manner.
    
    Parameters
    ----------
    file_path : Path
        Path to the FITS file (.lc.gz, .gti.gz, .pi.gz).
        
    Returns
    -------
    dict
        Structured evidence dictionary for candidate columns and header keywords.
    """
    evidence: Dict[str, Any] = {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "file_type": "UNKNOWN",
        "header_keywords": {},
        "candidate_roles": {},
    }

    name_lower = file_path.name.lower()
    if ".lc" in name_lower:
        evidence["file_type"] = "LIGHTCURVE"
    elif ".gti" in name_lower:
        evidence["file_type"] = "GTI"
    elif ".pi" in name_lower:
        evidence["file_type"] = "PI_SPECTRUM"

    # Open strictly read-only
    with fits.open(file_path, mode="readonly", memmap=True) as hdul:
        # Extract primary and main extension header keywords
        primary_hdr = hdul[0].header
        ext_hdr = hdul[1].header if len(hdul) > 1 else primary_hdr

        keys_to_check = [
            "TELESCOP", "INSTRUME", "OBS_ID", "FILTER", "NUMBAND",
            "TIMESYS", "MJDREFI", "MJDREFF", "TIMZERO", "TIMEDEL",
            "TIMEUNIT", "TIMEREF", "TSTART", "TSTOP", "DATE-OBS", "DATE-END"
        ]
        for k in keys_to_check:
            val = ext_hdr.get(k, primary_hdr.get(k, None))
            if val is not None:
                evidence["header_keywords"][k] = str(val).strip()

        if len(hdul) < 2 or not isinstance(hdul[1], (fits.BinTableHDU, fits.TableHDU)):
            return evidence

        table_hdu = hdul[1]
        col_names = table_hdu.columns.names
        n_rows = len(table_hdu.data) if table_hdu.data is not None else 0

        # Assess light-curve roles
        if evidence["file_type"] == "LIGHTCURVE":
            # 1. TIME
            if "TIME" in col_names and n_rows > 0:
                time_data = np.asarray(table_hdu.data["TIME"], dtype=np.float64)
                valid_mask = np.isfinite(time_data)
                valid_times = time_data[valid_mask]
                is_monotonic = bool(np.all(np.diff(valid_times) > 0)) if len(valid_times) > 1 else False
                diffs = np.diff(valid_times) if len(valid_times) > 1 else np.array([])
                evidence["candidate_roles"]["time"] = {
                    "candidate_column": "TIME",
                    "status": "PROVISIONAL",
                    "note": "requires human confirmation (G1)",
                    "format": table_hdu.columns["TIME"].format,
                    "unit_as_stored": table_hdu.columns["TIME"].unit or "None recorded",
                    "n_rows": n_rows,
                    "data_range": [float(np.min(valid_times)), float(np.max(valid_times))] if len(valid_times) > 0 else [],
                    "monotonic": is_monotonic,
                    "median_step": float(np.median(diffs)) if len(diffs) > 0 else None,
                    "header_evidence": {
                        "TIMESYS": evidence["header_keywords"].get("TIMESYS"),
                        "MJDREFI": evidence["header_keywords"].get("MJDREFI"),
                        "TIMEDEL": evidence["header_keywords"].get("TIMEDEL"),
                        "DATE-OBS": evidence["header_keywords"].get("DATE-OBS"),
                    }
                }
            else:
                evidence["candidate_roles"]["time"] = {
                    "candidate_column": None,
                    "status": "UNRESOLVED",
                    "note": "requires human confirmation (G1)",
                }

            # 2. COUNT / RATE
            count_col = None
            for c in ["COUNTS", "RATE", "COUNT"]:
                if c in col_names:
                    count_col = c
                    break
            if count_col and n_rows > 0:
                count_data = np.asarray(table_hdu.data[count_col], dtype=np.float64)
                n_nan = int(np.isnan(count_data).sum())
                n_pos_inf = int(np.isposinf(count_data).sum())
                n_neg_inf = int(np.isneginf(count_data).sum())
                valid_counts = count_data[np.isfinite(count_data)]
                evidence["candidate_roles"]["count_or_rate"] = {
                    "candidate_column": count_col,
                    "status": "PROVISIONAL",
                    "note": "requires human confirmation (G1)",
                    "format": table_hdu.columns[count_col].format,
                    "unit_as_stored": table_hdu.columns[count_col].unit or "None recorded",
                    "n_rows": n_rows,
                    "n_nan": n_nan,
                    "n_pos_inf": n_pos_inf,
                    "n_neg_inf": n_neg_inf,
                    "n_zeros": int((valid_counts == 0).sum()) if len(valid_counts) > 0 else 0,
                    "data_range": [float(np.min(valid_counts)), float(np.max(valid_counts))] if len(valid_counts) > 0 else [],
                    "mean": float(np.mean(valid_counts)) if len(valid_counts) > 0 else None,
                    "median": float(np.median(valid_counts)) if len(valid_counts) > 0 else None,
                    "header_evidence": {
                        "NUMBAND": evidence["header_keywords"].get("NUMBAND"),
                        "FILTER": evidence["header_keywords"].get("FILTER"),
                    }
                }
            else:
                evidence["candidate_roles"]["count_or_rate"] = {
                    "candidate_column": None,
                    "status": "UNRESOLVED",
                    "note": "requires human confirmation (G1)",
                }

            # 3. QUALITY FLAG
            flag_col = None
            for c in ["QUALITY", "FLAG", "STATUS"]:
                if c in col_names:
                    flag_col = c
                    break
            evidence["candidate_roles"]["quality_flag"] = {
                "candidate_column": flag_col,
                "status": "UNRESOLVED",
                "note": "No dedicated quality flag column found in RATE table; requires human confirmation (G1)",
            }

            # 4. ENERGY / CHANNEL INDICATOR
            evidence["candidate_roles"]["energy_or_channel"] = {
                "candidate_indicator": "Header keywords (NUMBAND, FILTER)",
                "status": "PROVISIONAL",
                "note": "requires human confirmation (G1)",
                "NUMBAND": evidence["header_keywords"].get("NUMBAND"),
                "FILTER": evidence["header_keywords"].get("FILTER"),
            }

        # Assess GTI roles
        elif evidence["file_type"] == "GTI":
            start_col = "START" if "START" in col_names else None
            stop_col = "STOP" if "STOP" in col_names else None

            if n_rows > 0 and start_col and stop_col:
                start_data = np.asarray(table_hdu.data[start_col], dtype=np.float64)
                stop_data = np.asarray(table_hdu.data[stop_col], dtype=np.float64)
                evidence["candidate_roles"]["gti_start"] = {
                    "candidate_column": start_col,
                    "status": "PROVISIONAL",
                    "note": "requires human confirmation (G1)",
                    "format": table_hdu.columns[start_col].format,
                    "unit_as_stored": table_hdu.columns[start_col].unit or "None recorded",
                    "n_intervals": n_rows,
                    "data_range": [float(np.min(start_data)), float(np.max(start_data))],
                    "monotonic": bool(np.all(np.diff(start_data) > 0)) if len(start_data) > 1 else True,
                }
                evidence["candidate_roles"]["gti_stop"] = {
                    "candidate_column": stop_col,
                    "status": "PROVISIONAL",
                    "note": "requires human confirmation (G1)",
                    "format": table_hdu.columns[stop_col].format,
                    "unit_as_stored": table_hdu.columns[stop_col].unit or "None recorded",
                    "n_intervals": n_rows,
                    "data_range": [float(np.min(stop_data)), float(np.max(stop_data))],
                    "monotonic": bool(np.all(np.diff(stop_data) > 0)) if len(stop_data) > 1 else True,
                }
            elif n_rows == 0:
                evidence["candidate_roles"]["gti_start"] = {
                    "candidate_column": start_col,
                    "status": "UNRESOLVED",
                    "note": "GTI table has ZERO rows for this observation; requires human confirmation (G1)",
                    "n_intervals": 0,
                }
                evidence["candidate_roles"]["gti_stop"] = {
                    "candidate_column": stop_col,
                    "status": "UNRESOLVED",
                    "note": "GTI table has ZERO rows for this observation; requires human confirmation (G1)",
                    "n_intervals": 0,
                }

        # Assess PI spectrum file
        elif evidence["file_type"] == "PI_SPECTRUM":
            evidence["candidate_roles"]["spectral_channels"] = {
                "candidate_columns": [c for c in ["SPEC_NUM", "CHANNEL", "COUNTS"] if c in col_names],
                "status": "UNRESOLVED",
                "note": "PI spectrum product — inspected read-only, not used in light-curve quality checks; requires human confirmation (G1)",
                "n_rows": n_rows,
            }

    return evidence


def generate_column_role_evidence(
    raw_dir: Path | str,
    output_json_path: Path | str,
    output_md_path: Path | str,
) -> Dict[str, Any]:
    """Scan raw FITS files and write comprehensive column-role evidence.
    
    Parameters
    ----------
    raw_dir : Path or str
        Directory containing raw FITS files.
    output_json_path : Path or str
        Destination path for JSON output.
    output_md_path : Path or str
        Destination path for Markdown report.
        
    Returns
    -------
    dict
        Complete evidence dictionary keyed by file name.
    """
    raw_path = Path(raw_dir)
    out_json = Path(output_json_path)
    out_md = Path(output_md_path)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(list(raw_path.glob("*.gz")) + list(raw_path.glob("*.fits")))
    all_evidence: Dict[str, Any] = {}

    for f in files:
        if f.is_file():
            all_evidence[f.name] = compile_file_role_evidence(f)

    # Save JSON
    with open(out_json, "w", encoding="utf-8") as jf:
        json.dump(all_evidence, jf, indent=2)

    # Generate Markdown report
    lines: List[str] = [
        "# SOLARIS-A1: Column-Role Evidence Report (Stage 4)",
        "",
        "> **CRITICAL NOTICE (Gate G1):** All candidate column roles, time systems, GTI columns, "
        "and channel definitions listed below are strictly **PROVISIONAL** or **UNRESOLVED**. "
        "No role is CONFIRMED. Every entry requires human researcher confirmation at Gate G1.",
        "",
        "---",
        "",
        "## Summary of Candidate Roles Across Products",
        "",
        "| File Name | Product Type | Candidate Time | Candidate Count/Rate | Quality Flag | GTI Interval Cols | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for fname, ev in all_evidence.items():
        ftype = ev.get("file_type", "UNKNOWN")
        roles = ev.get("candidate_roles", {})
        time_info = roles.get("time", {}).get("candidate_column", "-")
        count_info = roles.get("count_or_rate", {}).get("candidate_column", "-")
        flag_info = roles.get("quality_flag", {}).get("candidate_column", "None detected")
        gti_start = roles.get("gti_start", {}).get("candidate_column")
        gti_stop = roles.get("gti_stop", {}).get("candidate_column")
        gti_info = f"{gti_start}, {gti_stop}" if gti_start and gti_stop else "-"

        if ftype == "PI_SPECTRUM":
            time_info = "TSTART (spectrum)"
            count_info = "COUNTS (340D array)"
            gti_info = "N/A"

        status_tag = "PROVISIONAL (requires G1)" if ftype in ("LIGHTCURVE", "GTI") else "UNRESOLVED"
        lines.append(f"| `{fname}` | {ftype} | {time_info} | {count_info} | {flag_info} | {gti_info} | {status_tag} |")

    lines.extend([
        "",
        "---",
        "",
        "## Detailed Evidence by Product",
        "",
    ])

    for fname, ev in all_evidence.items():
        lines.append(f"### File: `{fname}`")
        lines.append(f"- **Product Type:** `{ev.get('file_type')}`")
        lines.append("- **Observed Header Keywords:**")
        for k, v in ev.get("header_keywords", {}).items():
            lines.append(f"  - `{k}`: `{v}`")
        lines.append("- **Role Evidence:**")
        for rname, rinfo in ev.get("candidate_roles", {}).items():
            lines.append(f"  - **Role `{rname}`:**")
            for rk, rv in rinfo.items():
                lines.append(f"    - `{rk}`: `{rv}`")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## Gate G1 Action Checklist for Student Researcher",
        "",
        "Before transitioning any role to CONFIRMED, the human student must verify:",
        "1. [ ] Confirm that `TIME` in `RATE` represents elapsed seconds from `1970-01-01 00:00:00 UTC` (MJD 40587).",
        "2. [ ] Confirm that `COUNTS` in `RATE` represents integrated detector counts (or count rate in c/s).",
        "3. [ ] Confirm that no hardware quality-flag bitmask exists in `.lc.gz`, or define where external flag indicators are sourced.",
        "4. [ ] Confirm that `START` and `STOP` in `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` correspond to valid observation intervals on the same time scale.",
        "5. [ ] Confirm why `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` contains zero rows (SDD1 inactive or off during this epoch).",
        "6. [ ] Confirm that `AL1_SOLEXS_20261018_SDD2_L1.pi.gz` is a multi-channel spectral file to be handled in later stages.",
        "",
    ])

    with open(out_md, "w", encoding="utf-8") as mf:
        mf.write("\n".join(lines))

    return all_evidence
