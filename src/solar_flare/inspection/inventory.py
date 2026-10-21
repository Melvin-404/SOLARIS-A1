"""Dataset inventory generation for SoLEXS FITS files.

Builds tabular inventory records capturing HDU structure, column candidate roles,
header observation tags, and temporal coverage across all manifest files.
Ambiguous column roles are marked as UNRESOLVED.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd
from astropy.io import fits

from solar_flare.inspection.fits_inspect import (
    list_hdus,
    describe_columns,
    InspectionError,
)
from solar_flare.manifest import find_file_in_dir

COUNT_RATE_KEYWORDS = ("COUNT", "RATE", "FLUX", "COUNTS", "CPS", "PHOTON")
QUALITY_FLAG_KEYWORDS = ("FLAG", "QUAL", "STATUS", "ERR", "ERROR", "BAD")
TIME_KEYWORDS = ("TIME", "DATE", "TSTART", "TSTOP", "START", "STOP", "SEC", "MJD", "UTC")



def _detect_candidate_roles(cols: List[Dict[str, Any]]) -> Dict[str, str]:
    """Identify candidate column roles without making final assumptions.

    Where multiple or ambiguous matches occur, the role is labelled UNRESOLVED.

    Args:
        cols: Column descriptor dictionaries.

    Returns:
        Dict[str, str]: Mapping of category -> detected candidate names or UNRESOLVED.
    """
    time_candidates = []
    count_candidates = []
    qual_candidates = []

    for col in cols:
        name_upper = col["name"].upper()
        if any(kw in name_upper for kw in TIME_KEYWORDS):
            time_candidates.append(col["name"])
        if any(kw in name_upper for kw in COUNT_RATE_KEYWORDS):
            count_candidates.append(col["name"])
        if any(kw in name_upper for kw in QUALITY_FLAG_KEYWORDS):
            qual_candidates.append(col["name"])

    # Build status descriptors
    time_res = ", ".join(time_candidates) if time_candidates else "NONE_DETECTED"
    if len(time_candidates) > 1:
        time_res = f"UNRESOLVED ({time_res})"

    count_res = ", ".join(count_candidates) if count_candidates else "NONE_DETECTED"
    if len(count_candidates) > 1:
        count_res = f"UNRESOLVED ({count_res})"

    qual_res = ", ".join(qual_candidates) if qual_candidates else "NONE_DETECTED"
    if len(qual_candidates) > 1:
        qual_res = f"UNRESOLVED ({qual_res})"

    return {
        "time_candidates": time_res,
        "count_rate_candidates": count_res,
        "quality_candidates": qual_res,
    }


def build_inventory(
    raw_dir: Union[Path, str],
    manifest_df: pd.DataFrame,
    out_dir: Optional[Union[Path, str]] = None,
) -> pd.DataFrame:
    """Scan all FITS files listed in the manifest and compile an inventory DataFrame.

    Outputs results to inventory.csv and inventory.json if out_dir is specified.

    Args:
        raw_dir: Directory containing raw files.
        manifest_df: Loaded manifest DataFrame.
        out_dir: Optional directory to save output artifacts.

    Returns:
        pd.DataFrame: Compiled inventory DataFrame.
    """
    raw_path = Path(raw_dir)
    inventory_rows: List[Dict[str, Any]] = []

    for _, row in manifest_df.iterrows():
        fname = row.get("file_name", "")
        if not fname or "EXAMPLE" in fname.upper():
            continue

        file_type = row.get("file_type", "UNKNOWN")
        paired_gti = row.get("paired_gti_file", "")
        pairing_ver = row.get("pairing_verified", "no").lower()

        disk_file = find_file_in_dir(fname, raw_path)
        if disk_file is None:
            inventory_rows.append({
                "file_name": fname,
                "file_type": file_type,
                "disk_status": "MISSING_ON_DISK",
                "file_size_bytes": 0,
                "hdu_names": "N/A",
                "main_hdu_name": "N/A",
                "rows_main_hdu": 0,
                "detected_time_candidates": "N/A",
                "detected_count_rate_candidates": "N/A",
                "detected_quality_candidates": "N/A",
                "header_obs_id": row.get("observation_id", "N/A"),
                "header_telescope": "N/A",
                "header_instrument": "N/A",
                "header_tstart": "N/A",
                "header_tstop": "N/A",
                "header_date_obs": "N/A",
                "header_date_end": "N/A",
                "unpaired_status": "MISSING_FILE",
            })
            continue

        size_bytes = disk_file.stat().st_size

        try:
            hdus = list_hdus(disk_file)
            hdu_names_str = ", ".join([h["name"] for h in hdus])

            # Locate main table HDU (e.g., RATE, GTI, or first table extension)
            main_hdu_info = None
            for h in hdus:
                if h["columns_count"] > 0:
                    main_hdu_info = h
                    if h["name"].upper() in ("RATE", "LIGHTCURVE", "GTI"):
                        break

            main_hdu_name = main_hdu_info["name"] if main_hdu_info else "NONE"
            main_rows = main_hdu_info["rows"] if main_hdu_info else 0

            # Column candidates
            if main_hdu_info and main_hdu_info["columns_count"] > 0:
                cols = describe_columns(disk_file, hdu=main_hdu_info["index"])
                candidate_roles = _detect_candidate_roles(cols)
            else:
                candidate_roles = {
                    "time_candidates": "NO_TABLE_COLUMNS",
                    "count_rate_candidates": "NO_TABLE_COLUMNS",
                    "quality_candidates": "NO_TABLE_COLUMNS",
                }

            # Extract header keywords from Primary and Main HDUs
            hdr_obs_id = "UNKNOWN"
            hdr_telescope = "UNKNOWN"
            hdr_instrument = "UNKNOWN"
            hdr_tstart = "UNKNOWN"
            hdr_tstop = "UNKNOWN"
            hdr_date_obs = "UNKNOWN"
            hdr_date_end = "UNKNOWN"

            with fits.open(str(disk_file), mode="readonly", memmap=False) as hdul:
                for hdu_item in hdul:
                    h = hdu_item.header
                    if "OBS_ID" in h and hdr_obs_id == "UNKNOWN":
                        hdr_obs_id = str(h["OBS_ID"])
                    if "TELESCOP" in h and hdr_telescope == "UNKNOWN":
                        hdr_telescope = str(h["TELESCOP"])
                    if "INSTRUME" in h and hdr_instrument == "UNKNOWN":
                        hdr_instrument = str(h["INSTRUME"])
                    if "TSTART" in h and hdr_tstart == "UNKNOWN":
                        hdr_tstart = str(h["TSTART"])
                    if "TSTOP" in h and hdr_tstop == "UNKNOWN":
                        hdr_tstop = str(h["TSTOP"])
                    if "DATE-OBS" in h and hdr_date_obs == "UNKNOWN":
                        hdr_date_obs = str(h["DATE-OBS"])
                    if "DATE-END" in h and hdr_date_end == "UNKNOWN":
                        hdr_date_end = str(h["DATE-END"])

            # Check pairing status
            if file_type == "LIGHTCURVE":
                if not paired_gti or pairing_ver != "yes":
                    unpaired_status = "UNPAIRED_OR_UNVERIFIED"
                else:
                    gti_disk = find_file_in_dir(paired_gti, raw_path)
                    unpaired_status = "PAIRED_OK" if gti_disk else "PAIRED_GTI_MISSING_ON_DISK"
            else:
                unpaired_status = "GTI_OR_OTHER"

            inventory_rows.append({
                "file_name": fname,
                "file_type": file_type,
                "disk_status": "PRESENT",
                "file_size_bytes": size_bytes,
                "hdu_names": hdu_names_str,
                "main_hdu_name": main_hdu_name,
                "rows_main_hdu": main_rows,
                "detected_time_candidates": candidate_roles["time_candidates"],
                "detected_count_rate_candidates": candidate_roles["count_rate_candidates"],
                "detected_quality_candidates": candidate_roles["quality_candidates"],
                "header_obs_id": hdr_obs_id,
                "header_telescope": hdr_telescope,
                "header_instrument": hdr_instrument,
                "header_tstart": hdr_tstart,
                "header_tstop": hdr_tstop,
                "header_date_obs": hdr_date_obs,
                "header_date_end": hdr_date_end,
                "unpaired_status": unpaired_status,
            })

        except Exception as exc:
            inventory_rows.append({
                "file_name": fname,
                "file_type": file_type,
                "disk_status": f"INSPECTION_ERROR: {exc}",
                "file_size_bytes": size_bytes,
                "hdu_names": "ERROR",
                "main_hdu_name": "ERROR",
                "rows_main_hdu": 0,
                "detected_time_candidates": "ERROR",
                "detected_count_rate_candidates": "ERROR",
                "detected_quality_candidates": "ERROR",
                "header_obs_id": "ERROR",
                "header_telescope": "ERROR",
                "header_instrument": "ERROR",
                "header_tstart": "ERROR",
                "header_tstop": "ERROR",
                "header_date_obs": "ERROR",
                "header_date_end": "ERROR",
                "unpaired_status": "ERROR",
            })

    inv_df = pd.DataFrame(inventory_rows)

    if out_dir:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        csv_path = out_path / "inventory.csv"
        json_path = out_path / "inventory.json"
        inv_df.to_csv(csv_path, index=False)
        inv_df.to_json(json_path, orient="records", indent=2)

    return inv_df
