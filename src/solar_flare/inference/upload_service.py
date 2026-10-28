"""Upload, validation, and inference service for user-submitted datasets (Task A).

Allows users to upload a single day's Aditya-L1 SoLEXS observation (FITS or CSV),
validates data quality, enforces causal preprocessing and segmentation without
telemetry gap interpolation, computes the exact 19 causal features, and executes
inference using the existing frozen trained models.

STRICT CONSTRAINTS:
1. Zero training or fine-tuning: Never invokes fit(), train(), or retrain().
2. Zero model mutation: Model weights and artifacts remain strictly untouched.
3. No interpolation: Telemetry gaps are never bridged or synthetic data substituted.
4. Memory safety: Maximum file size limits and in-memory byte stream processing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import io
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import zipfile
import numpy as np
import pandas as pd

from solar_flare.evaluation.event_metrics import (
    PredictedInterval,
    merge_positive_windows,
)
from solar_flare.features.baseline import causal_baseline
from solar_flare.features.registry import compute_features
from solar_flare.features.windows import generate_windows
from solar_flare.inference.pipeline import (
    InferencePipeline,
    classify_risk,
    get_default_pipeline,
    get_pipeline,
)
from solar_flare.preprocessing.filters import (
    exclude_negative,
    exclude_non_finite,
)
from solar_flare.preprocessing.gti_apply import apply_gti
from solar_flare.preprocessing.segmentation import segment_continuous
from solar_flare.quality.checks import (
    check_duplicate_timestamps,
    check_negative_values,
    check_non_finite,
)

logger = logging.getLogger("solaris_a1.upload_service")

MAX_UPLOAD_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB safety cap
MIN_REQUIRED_SAMPLES = 60  # Minimum samples needed for at least one 60s window
MAX_ZIP_UPLOAD_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB max zip payload
MAX_ZIP_FILE_COUNT = 100  # Max entries in zip
MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES = 250 * 1024 * 1024  # 250 MB max uncompressed total
MAX_ZIP_SINGLE_FILE_BYTES = 100 * 1024 * 1024  # 100 MB max per file
MAX_ZIP_COMPRESSION_RATIO = 100.0  # Max compression ratio (zip bomb defense)


class UploadValidationError(ValueError):
    """Raised when an uploaded dataset is malformed, incompatible, or violates requirements."""
    pass


def _normalize_observation_stem(filename: str) -> str:
    """Extract canonical observation key from light-curve or GTI filename.

    Examples:
    - AL1_SOLEXS_20240713_SDD2_L1.lc.gz -> AL1_SOLEXS_20240713_SDD2_L1
    - AL1_SOLEXS_20240713_SDD2_L1.gti.gz -> AL1_SOLEXS_20240713_SDD2_L1
    - solexs_20240713_lightcurve.csv -> solexs_20240713
    - solexs_20240713_gti.csv -> solexs_20240713
    - 20240713.lc -> 20240713
    """
    name = Path(filename).name
    lower = name.lower()

    # Strip extensions
    for ext in [".lc.gz", ".gti.gz", ".fits.gz", ".lc", ".gti", ".fits", ".csv", ".gz"]:
        if lower.endswith(ext):
            name = name[:-len(ext)]
            lower = name.lower()
            break

    # Strip trailing descriptors
    for suffix in ["_lc", ".lc", "-lc", "_gti", ".gti", "-gti", "_lightcurve", "_good_times", "_rates"]:
        if lower.endswith(suffix):
            name = name[:-len(suffix)]
            lower = name.lower()
            break

    return name.strip()


def _is_gti_candidate(filename: str) -> bool:
    """Check if a filename is a Good Time Interval (GTI) candidate."""
    lower = Path(filename).name.lower()
    if lower.endswith(".gti") or lower.endswith(".gti.gz"):
        return True
    if ("gti" in lower or "good_time" in lower) and any(lower.endswith(ext) for ext in [".fits", ".fits.gz", ".csv"]):
        return True
    return False


def _is_lightcurve_candidate(filename: str) -> bool:
    """Check if a filename is a Light Curve candidate."""
    if _is_gti_candidate(filename):
        return False
    lower = Path(filename).name.lower()
    return any(lower.endswith(ext) for ext in [".lc", ".lc.gz", ".fits", ".fits.gz", ".csv"])


def inspect_uploaded_zip(
    file_content: Union[bytes, io.BytesIO],
    filename: str,
) -> Dict[str, Any]:
    """Inspect and validate a single-day SoLEXS observation ZIP archive in memory.

    Parameters
    ----------
    file_content : bytes or BytesIO
        Raw ZIP file payload.
    filename : str
        Filename of the uploaded ZIP archive.

    Returns
    -------
    Dict[str, Any]
        Structured inspection report containing matched observation pairs, dates, and safety validation.

    Raises
    ------
    UploadValidationError
        If archive is corrupt, violates path traversal constraints, exceeds size/ratio limits,
        or contains no supported light-curve files.
    """
    if isinstance(file_content, io.BytesIO):
        raw_bytes = file_content.getvalue()
    elif isinstance(file_content, bytes):
        raw_bytes = file_content
    else:
        raise UploadValidationError(f"Invalid ZIP payload type: {type(file_content)}")

    if len(raw_bytes) == 0:
        raise UploadValidationError("The uploaded ZIP archive is empty (0 bytes).")

    if len(raw_bytes) > MAX_ZIP_UPLOAD_SIZE_BYTES:
        raise UploadValidationError(
            f"ZIP file size ({len(raw_bytes) / (1024*1024):.1f} MB) exceeds maximum allowed limit of {MAX_ZIP_UPLOAD_SIZE_BYTES / (1024*1024):.0f} MB."
        )

    stream = io.BytesIO(raw_bytes)
    if not zipfile.is_zipfile(stream):
        raise UploadValidationError(f"File '{filename}' is not a valid or readable ZIP archive.")

    try:
        zf = zipfile.ZipFile(stream, mode="r")
    except Exception as exc:
        raise UploadValidationError(f"Failed to open ZIP archive '{filename}': {exc}") from exc

    with zf:
        infolist = zf.infolist()
        if len(infolist) == 0:
            raise UploadValidationError(f"ZIP archive '{filename}' contains no files.")

        if len(infolist) > MAX_ZIP_FILE_COUNT:
            raise UploadValidationError(
                f"Archive contains {len(infolist)} entries, exceeding maximum allowed limit of {MAX_ZIP_FILE_COUNT} entries."
            )

        total_uncompressed = 0
        valid_entries: List[Dict[str, Any]] = []
        lc_candidates: List[zipfile.ZipInfo] = []
        gti_candidates: List[zipfile.ZipInfo] = []

        for info in infolist:
            # Skip directories
            if info.is_dir():
                continue

            fname = info.filename
            # 1. Path traversal & security checks
            if "\0" in fname:
                raise UploadValidationError(f"Archive entry '{fname}' contains illegal null bytes.")

            norm_name = fname.replace("\\", "/")
            if norm_name.startswith("/") or bool(re.match(r"^[a-zA-Z]:", norm_name)):
                raise UploadValidationError(
                    f"Archive entry '{fname}' violates path traversal security constraints (absolute path)."
                )

            parts = Path(norm_name).parts
            if any(p == ".." for p in parts):
                raise UploadValidationError(
                    f"Archive entry '{fname}' violates path traversal security constraints (directory traversal '..')."
                )

            # 2. Size & Zip-bomb checks
            if info.file_size > MAX_ZIP_SINGLE_FILE_BYTES:
                raise UploadValidationError(
                    f"Archive entry '{fname}' uncompressed size ({info.file_size / (1024*1024):.1f} MB) exceeds single file limit of {MAX_ZIP_SINGLE_FILE_BYTES / (1024*1024):.0f} MB."
                )

            total_uncompressed += info.file_size
            if total_uncompressed > MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES:
                raise UploadValidationError(
                    f"Total uncompressed size of archive exceeds maximum allowed limit of {MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES / (1024*1024):.0f} MB."
                )

            if info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > MAX_ZIP_COMPRESSION_RATIO:
                    raise UploadValidationError(
                        f"Archive entry '{fname}' has a suspicious compression ratio ({ratio:.1f}:1), exceeding safety threshold of {MAX_ZIP_COMPRESSION_RATIO:.0f}:1."
                    )

            # Ignore metadata / hidden / system files
            base_name = Path(fname).name
            if base_name.startswith(".") or base_name.startswith("._") or "__macosx" in norm_name.lower() or base_name.lower() in [".ds_store", "thumbs.db"]:
                continue

            valid_entries.append({
                "filename": fname,
                "size_bytes": info.file_size,
                "compressed_bytes": info.compress_size,
            })

            if _is_gti_candidate(fname):
                gti_candidates.append(info)
            elif _is_lightcurve_candidate(fname):
                lc_candidates.append(info)

        if not lc_candidates:
            raise UploadValidationError(
                f"ZIP archive '{filename}' does not contain any supported Aditya-L1 SoLEXS light curve files (.lc, .lc.gz, .fits, .csv)."
            )

        # 3. Match Light Curves with GTIs
        observations: Dict[str, Dict[str, Any]] = {}
        matched_gtis: set[str] = set()

        for lc_info in lc_candidates:
            lc_fname = lc_info.filename
            obs_stem = _normalize_observation_stem(lc_fname)
            obs_date = _extract_date_from_string(lc_fname) or "Unknown Date"

            # Find matching GTI
            matched_gti_info: Optional[zipfile.ZipInfo] = None
            for gti_info in gti_candidates:
                gti_stem = _normalize_observation_stem(gti_info.filename)
                if gti_stem == obs_stem:
                    matched_gti_info = gti_info
                    break

            # Secondary match: same date & detector if only 1 GTI matches
            if matched_gti_info is None and obs_date != "Unknown Date":
                date_matches = [g for g in gti_candidates if _extract_date_from_string(g.filename) == obs_date]
                if len(date_matches) == 1:
                    matched_gti_info = date_matches[0]

            if matched_gti_info is not None:
                matched_gtis.add(matched_gti_info.filename)

            # Check for ambiguous duplicate light curves with the same key
            if obs_stem in observations:
                raise UploadValidationError(
                    f"Archive contains duplicate/ambiguous light curve files for the same observation '{obs_stem}': '{observations[obs_stem]['lc_filename']}' and '{lc_fname}'."
                )

            observations[obs_stem] = {
                "key": obs_stem,
                "display_label": f"{obs_stem} ({obs_date})",
                "observation_date": obs_date,
                "lc_filename": lc_fname,
                "lc_size_bytes": lc_info.file_size,
                "gti_filename": matched_gti_info.filename if matched_gti_info else None,
                "gti_size_bytes": matched_gti_info.file_size if matched_gti_info else None,
                "has_gti": matched_gti_info is not None,
                "status": "MATCHED_WITH_GTI" if matched_gti_info else "LIGHTCURVE_ONLY_NO_GTI",
            }

        unmatched_gtis = [g.filename for g in gti_candidates if g.filename not in matched_gtis]
        warnings: List[str] = []
        if unmatched_gtis:
            warnings.append(
                f"GTI file(s) {unmatched_gtis} could not be paired because observation identifiers did not match any light curve."
            )

        return {
            "archive_filename": filename,
            "total_archive_bytes": len(raw_bytes),
            "total_files_in_zip": len(infolist),
            "valid_files_count": len(valid_entries),
            "uncompressed_bytes_total": total_uncompressed,
            "observations": observations,
            "n_observations": len(observations),
            "has_multiple_observations": len(observations) > 1,
            "unmatched_gtis": unmatched_gtis,
            "warnings": warnings,
            "all_entries": valid_entries,
        }


def extract_zip_observation(
    file_content: Union[bytes, io.BytesIO],
    filename: str,
    observation_key: Optional[str] = None,
) -> Tuple[bytes, str, Optional[bytes], Optional[str]]:
    """Safely extract the chosen observation's light-curve and optional GTI bytes from a ZIP archive entirely in memory.

    Parameters
    ----------
    file_content : bytes or BytesIO
        Raw ZIP file payload.
    filename : str
        Filename of the uploaded ZIP archive.
    observation_key : str, optional
        Observation identifier to extract. Required if archive contains multiple observation days.

    Returns
    -------
    Tuple[bytes, str, Optional[bytes], Optional[str]]
        (lc_bytes, lc_filename, gti_bytes, gti_filename)

    Raises
    ------
    UploadValidationError
        If observation_key is missing when multiple observations exist, or not found.
    """
    inspection = inspect_uploaded_zip(file_content, filename)
    observations = inspection["observations"]

    if not observations:
        raise UploadValidationError(f"No valid observations found in archive '{filename}'.")

    if observation_key is None:
        if len(observations) > 1:
            keys = list(observations.keys())
            raise UploadValidationError(
                f"ZIP archive '{filename}' contains {len(observations)} observations: {keys}. Please select an observation explicitly."
            )
        target_key = list(observations.keys())[0]
    else:
        if observation_key not in observations:
            raise UploadValidationError(
                f"Observation key '{observation_key}' not found in archive. Available: {list(observations.keys())}"
            )
        target_key = observation_key

    target_obs = observations[target_key]
    lc_fname = target_obs["lc_filename"]
    gti_fname = target_obs["gti_filename"]

    if isinstance(file_content, io.BytesIO):
        raw_bytes = file_content.getvalue()
    else:
        raw_bytes = file_content

    with zipfile.ZipFile(io.BytesIO(raw_bytes), mode="r") as zf:
        lc_bytes = zf.read(lc_fname)
        gti_bytes = zf.read(gti_fname) if gti_fname else None

    return lc_bytes, lc_fname, gti_bytes, gti_fname


def process_uploaded_zip(
    file_content: Union[bytes, io.BytesIO],
    filename: str,
    observation_key: Optional[str] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any], Optional[List[Tuple[float, float]]], Dict[str, Any]]:
    """End-to-end processing of observation telemetry from an in-memory ZIP archive.

    Parameters
    ----------
    file_content : bytes or BytesIO
        Raw ZIP file payload.
    filename : str
        Filename of the uploaded ZIP archive.
    observation_key : str, optional
        Selected observation key if multiple observations exist.

    Returns
    -------
    Tuple[pd.DataFrame, Dict[str, Any], Optional[List[Tuple[float, float]]], Dict[str, Any]]
        (df, lc_metadata, gti_intervals, inspection_dict)
    """
    inspection = inspect_uploaded_zip(file_content, filename)
    lc_bytes, lc_fname, gti_bytes, gti_fname = extract_zip_observation(
        file_content, filename, observation_key=observation_key
    )

    df, lc_meta = parse_uploaded_lightcurve(lc_bytes, lc_fname)

    gti_intervals = None
    if gti_bytes and gti_fname:
        gti_intervals, _ = parse_uploaded_gti(gti_bytes, gti_fname)

    return df, lc_meta, gti_intervals, inspection


def _extract_date_from_string(text: str) -> Optional[str]:
    """Extract YYYY-MM-DD date from filename or header string."""
    # Matches YYYYMMDD (e.g. 20261018, 20240701)
    m = re.search(r"20[2-9]\d[01]\d[0-3]\d", text)
    if m:
        s = m.group(0)
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"

    # Matches YYYY-MM-DD
    m2 = re.search(r"20[2-9]\d-[01]\d-[0-3]\d", text)
    if m2:
        return m2.group(0)

    return None



def parse_uploaded_lightcurve(
    file_content: Union[bytes, io.BytesIO],
    filename: str,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Parse and standardize an uploaded light curve file (FITS or CSV).

    Parameters
    ----------
    file_content : bytes or BytesIO
        Raw uploaded file payload.
    filename : str
        Original filename of the upload.

    Returns
    -------
    Tuple[pd.DataFrame, Dict[str, Any]]
        df_standardized: DataFrame with columns ['time', 'counts'].
        metadata: Dictionary of detected file metadata.

    Raises
    ------
    UploadValidationError
        If file exceeds size cap, is empty, has unsupported extension, or lacks required columns.
    """
    if isinstance(file_content, io.BytesIO):
        raw_bytes = file_content.getvalue()
    elif isinstance(file_content, bytes):
        raw_bytes = file_content
    else:
        raise UploadValidationError(f"Invalid file payload type: {type(file_content)}")

    if len(raw_bytes) == 0:
        raise UploadValidationError("The uploaded file is empty (0 bytes).")

    if len(raw_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise UploadValidationError(
            f"File size ({len(raw_bytes) / (1024*1024):.1f} MB) exceeds maximum allowed limit of {MAX_UPLOAD_SIZE_BYTES / (1024*1024):.0f} MB."
        )

    lower_name = filename.lower()
    df_raw: Optional[pd.DataFrame] = None
    header_meta: Dict[str, Any] = {}

    # 1. Parse CSV
    if lower_name.endswith(".csv"):
        try:
            df_raw = pd.read_csv(io.BytesIO(raw_bytes))
        except Exception as exc:
            raise UploadValidationError(f"Failed to parse CSV file: {exc}") from exc

        if df_raw.empty:
            raise UploadValidationError("Uploaded CSV contains no data rows.")

        # Resolve time column
        time_candidates = ["time", "seconds", "timestamp", "met", "epoch", "date_time", "datetime"]
        time_col = None
        for col in df_raw.columns:
            if col.strip().lower() in time_candidates:
                time_col = col
                break
        if time_col is None:
            # Check for substring match
            for col in df_raw.columns:
                if "time" in col.strip().lower() or "sec" in col.strip().lower():
                    time_col = col
                    break

        # Resolve count/flux column
        count_candidates = ["counts", "rate", "flux", "count_rate", "counts_s", "rate_cps", "sdd2"]
        count_col = None
        for col in df_raw.columns:
            if col.strip().lower() in count_candidates:
                count_col = col
                break
        if count_col is None:
            for col in df_raw.columns:
                if any(k in col.strip().lower() for k in ["count", "rate", "flux"]):
                    count_col = col
                    break

        if time_col is None or count_col is None:
            raise UploadValidationError(
                f"Required telemetry columns missing in CSV '{filename}'. "
                f"Available columns: {list(df_raw.columns)}. "
                "Expected a time column (e.g. 'TIME', 'timestamp') and a count/flux column (e.g. 'COUNTS', 'rate')."
            )

        # Parse numeric time values
        try:
            time_series = pd.to_numeric(df_raw[time_col], errors="coerce")
            # If all values are NaN, check if timestamps are ISO strings
            if time_series.isna().all():
                dt_series = pd.to_datetime(df_raw[time_col], errors="coerce", utc=True)
                if dt_series.notna().any():
                    time_series = dt_series.astype(int) / 1e9
        except Exception as exc:
            raise UploadValidationError(f"Could not convert time column '{time_col}' to numeric: {exc}")

        count_series = pd.to_numeric(df_raw[count_col], errors="coerce")
        df_standard = pd.DataFrame({"time": time_series, "counts": count_series})

    # 2. Parse FITS (.lc, .lc.gz, .fits, .fits.gz)
    elif any(lower_name.endswith(ext) for ext in [".lc", ".lc.gz", ".fits", ".fits.gz"]):
        try:
            import gzip
            from astropy.io import fits
            
            # Decompress if gzip payload
            fits_bytes = gzip.decompress(raw_bytes) if (raw_bytes[:2] == b"\x1f\x8b" or lower_name.endswith(".gz")) else raw_bytes
            with fits.open(io.BytesIO(fits_bytes), mode="readonly", memmap=False) as hdul:
                # Find tabular HDU containing observation
                table_hdu = None
                for idx, hdu in enumerate(hdul):
                    if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)) and hdu.data is not None:
                        table_hdu = hdu
                        break

                if table_hdu is None:
                    raise UploadValidationError(
                        f"FITS file '{filename}' does not contain any binary table HDUs with telemetry."
                    )

                # Extract header keywords
                header = table_hdu.header
                primary_header = hdul[0].header if len(hdul) > 0 else {}
                for k in ["DATE-OBS", "TELESCOP", "INSTRUME", "OBS_ID", "TIMESYS", "MJDREFI", "TSTART", "TSTOP"]:
                    val = header.get(k) or primary_header.get(k)
                    if val is not None:
                        header_meta[k] = str(val).strip()

                colnames = list(table_hdu.data.names)
                time_col = next((c for c in colnames if "time" in c.lower()), colnames[0])
                count_col = next((c for c in colnames if any(k in c.lower() for k in ["count", "rate", "flux"])), None)

                if count_col is None and len(colnames) > 1:
                    count_col = colnames[1]

                if count_col is None:
                    raise UploadValidationError(
                        f"FITS table in '{filename}' does not contain a count rate or flux column. Found: {colnames}"
                    )

                times = np.array(table_hdu.data[time_col], dtype=np.float64)
                counts = np.array(table_hdu.data[count_col], dtype=np.float64)
                df_standard = pd.DataFrame({"time": times, "counts": counts})
        except UploadValidationError:
            raise
        except Exception as exc:
            raise UploadValidationError(f"Failed to inspect FITS file '{filename}': {exc}") from exc
    elif lower_name.endswith(".zip"):
        df_zip, meta_zip, _, _ = process_uploaded_zip(raw_bytes, filename)
        return df_zip, meta_zip
    else:
        raise UploadValidationError(
            f"Unsupported file format '{filename}'. Supported formats: ZIP archives (.zip), FITS (.lc, .lc.gz, .fits, .fits.gz), and CSV (.csv)."
        )

    # Validate minimal length
    if len(df_standard) < MIN_REQUIRED_SAMPLES:
        raise UploadValidationError(
            f"Uploaded file contains only {len(df_standard)} samples. "
            f"A minimum of {MIN_REQUIRED_SAMPLES} samples is required for 60-second sliding window evaluation."
        )

    # Sort chronologically
    df_standard.sort_values(by="time", inplace=True)
    df_standard.reset_index(drop=True, inplace=True)

    # Extract observation date
    obs_date = header_meta.get("DATE-OBS")
    if obs_date:
        obs_date = obs_date.split("T")[0].split(" ")[0].strip()
    if not obs_date:
        obs_date = _extract_date_from_string(filename)
    if not obs_date:
        # Check first timestamp if unix epoch
        t_first = float(df_standard["time"].iloc[0])
        if t_first > 1e8:  # plausible unix epoch
            try:
                obs_date = datetime.fromtimestamp(t_first, tz=timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                obs_date = "Unavailable"
        else:
            obs_date = "Mission Elapsed Time (MET)"

    t_min = float(df_standard["time"].min())
    t_max = float(df_standard["time"].max())
    span_s = float(t_max - t_min)

    metadata = {
        "filename": filename,
        "format": "CSV" if lower_name.endswith(".csv") else "FITS",
        "file_size_bytes": len(raw_bytes),
        "total_records": len(df_standard),
        "observation_date": obs_date,
        "detected_date": obs_date,
        "time_min": t_min,
        "time_max": t_max,
        "span_seconds": span_s,
        "span_hours": span_s / 3600.0,
        "header_metadata": header_meta,
    }

    return df_standard, metadata


def parse_uploaded_gti(
    file_content: Union[bytes, io.BytesIO],
    filename: str,
) -> Tuple[List[Tuple[float, float]], Dict[str, Any]]:
    """Parse an uploaded Good Time Interval (GTI) file (FITS or CSV).

    Parameters
    ----------
    file_content : bytes or BytesIO
        Raw GTI file payload.
    filename : str
        Filename of the uploaded GTI file.

    Returns
    -------
    Tuple[List[Tuple[float, float]], Dict[str, Any]]
        List of verified (start_sec, stop_sec) intervals, and metadata dictionary.

    Raises
    ------
    UploadValidationError
        If GTI file is invalid, empty, or lacks start/stop columns.
    """
    if isinstance(file_content, io.BytesIO):
        raw_bytes = file_content.getvalue()
    elif isinstance(file_content, bytes):
        raw_bytes = file_content
    else:
        raise UploadValidationError("Invalid GTI payload type.")

    if len(raw_bytes) == 0:
        raise UploadValidationError("The uploaded GTI file is empty (0 bytes).")

    lower_name = filename.lower()
    intervals: List[Tuple[float, float]] = []
    gti_format = "UNKNOWN"

    if lower_name.endswith(".csv"):
        gti_format = "CSV_GTI"
        try:
            df_gti = pd.read_csv(io.BytesIO(raw_bytes))
        except Exception as exc:
            raise UploadValidationError(f"Failed to parse GTI CSV: {exc}") from exc

        start_col = next((c for c in df_gti.columns if c.strip().lower() in ["start", "t_start", "onset"]), None)
        stop_col = next((c for c in df_gti.columns if c.strip().lower() in ["stop", "end", "t_stop"]), None)

        if start_col is None or stop_col is None:
            raise UploadValidationError(
                f"GTI CSV must contain start and stop columns. Found: {list(df_gti.columns)}"
            )

        for _, row in df_gti.iterrows():
            try:
                st_val = float(row[start_col])
                sp_val = float(row[stop_col])
                if sp_val > st_val:
                    intervals.append((st_val, sp_val))
            except (ValueError, TypeError):
                continue

    elif any(lower_name.endswith(ext) for ext in [".gti", ".gti.gz", ".fits", ".fits.gz"]):
        gti_format = "FITS_GTI"
        try:
            import gzip
            from astropy.io import fits
            fits_bytes = gzip.decompress(raw_bytes) if (raw_bytes[:2] == b"\x1f\x8b" or lower_name.endswith(".gz")) else raw_bytes
            with fits.open(io.BytesIO(fits_bytes), mode="readonly", memmap=False) as hdul:
                gti_hdu = None
                for hdu in hdul:
                    if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)) and hdu.data is not None:
                        if "gti" in (hdu.name or "").lower() or (
                            hasattr(hdu.data, "names") and "START" in hdu.data.names and "STOP" in hdu.data.names
                        ):
                            gti_hdu = hdu
                            break
                if gti_hdu is None:
                    # Fallback to first table HDU
                    for hdu in hdul:
                        if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)) and hdu.data is not None:
                            gti_hdu = hdu
                            break

                if gti_hdu is None:
                    raise UploadValidationError(f"No GTI table HDU found in '{filename}'.")

                colnames = list(gti_hdu.data.names)
                s_col = next((c for c in colnames if "start" in c.lower()), colnames[0])
                e_col = next((c for c in colnames if any(k in c.lower() for k in ["stop", "end"])), colnames[1])

                s_arr = np.array(gti_hdu.data[s_col], dtype=np.float64)
                e_arr = np.array(gti_hdu.data[e_col], dtype=np.float64)

                for st_val, sp_val in zip(s_arr, e_arr):
                    if sp_val > st_val:
                        intervals.append((float(st_val), float(sp_val)))
        except UploadValidationError:
            raise
        except Exception as exc:
            raise UploadValidationError(f"Failed to read GTI FITS: {exc}") from exc
    else:
        raise UploadValidationError(
            f"Unsupported GTI file format '{filename}'. Supported formats: FITS (.gti, .gti.gz, .fits) or CSV (.csv)."
        )

    if not intervals:
        raise UploadValidationError(f"GTI file '{filename}' contained zero valid intervals where STOP > START.")

    intervals.sort(key=lambda x: x[0])
    total_gti_dur = sum(sp - st for st, sp in intervals)
    metadata = {
        "format": gti_format,
        "filename": filename,
        "n_intervals": len(intervals),
        "total_duration_seconds": total_gti_dur,
        "first_interval_start": intervals[0][0],
        "last_interval_stop": intervals[-1][1],
    }
    return intervals, metadata


def validate_uploaded_telemetry(
    df: pd.DataFrame,
    gti_intervals: Optional[List[Tuple[float, float]]] = None,
) -> Dict[str, Any]:
    """Execute quality checks on uploaded light curve without modifying data.

    Parameters
    ----------
    df : pd.DataFrame
        Standardized DataFrame with 'time' and 'counts'.
    gti_intervals : list of (start, stop), optional
        Good Time Intervals if provided.

    Returns
    -------
    dict
        Structured validation results including counts, cadence, and quality status.
    """
    counts_arr = df["counts"].values
    times_arr = df["time"].values

    non_finite_res = check_non_finite(counts_arr)
    negative_res = check_negative_values(counts_arr)
    duplicate_res = check_duplicate_timestamps(times_arr)

    # Cadence analysis
    diffs = np.diff(times_arr)
    pos_diffs = diffs[diffs > 0]
    cadence_median = float(np.median(pos_diffs)) if len(pos_diffs) > 0 else 1.0
    cadence_min = float(np.min(pos_diffs)) if len(pos_diffs) > 0 else 0.0
    cadence_max = float(np.max(diffs)) if len(diffs) > 0 else 0.0

    # Count cadence gaps > 3.0 seconds
    gap_threshold_s = 3.0
    n_gaps = int(np.sum(diffs > gap_threshold_s))

    # GTI coverage check
    gti_coverage: Optional[Dict[str, Any]] = None
    if gti_intervals:
        in_gti_mask = np.zeros(len(times_arr), dtype=bool)
        for st_val, sp_val in gti_intervals:
            in_gti_mask |= (times_arr >= st_val) & (times_arr < sp_val)
        n_in = int(in_gti_mask.sum())
        n_out = int(len(times_arr) - n_in)
        cov_frac = float(n_in / len(times_arr)) if len(times_arr) > 0 else 0.0
        gti_coverage = {
            "n_intervals": len(gti_intervals),
            "n_samples_inside_gti": n_in,
            "n_samples_outside_gti": n_out,
            "gti_covered_fraction": cov_frac,
        }

    total_samples = max(1, len(df))
    n_nan = int(non_finite_res["counts"].get("n_nan", 0))
    n_non_finite = int(non_finite_res["counts"].get("n_non_finite", n_nan))
    pct_non_finite = float((n_non_finite / total_samples) * 100.0)

    n_negative = int(negative_res["counts"].get("n_negative", 0))
    pct_negative = float((n_negative / total_samples) * 100.0)

    n_duplicates = int(duplicate_res["counts"].get("n_duplicates", 0))

    warnings: List[str] = []
    if n_non_finite > 0:
        warnings.append(
            f"Identified {n_non_finite} non-finite/NaN values ({pct_non_finite:.2f}%). These will be excluded without interpolation."
        )
    if n_negative > 0:
        warnings.append(
            f"Identified {n_negative} negative count rate values ({pct_negative:.2f}%). These will be excluded without interpolation."
        )
    if n_duplicates > 0:
        warnings.append(
            f"Identified {n_duplicates} duplicate timestamps. Duplicate records will be dropped."
        )
    if n_gaps > 0:
        warnings.append(
            f"Identified {n_gaps} telemetry gaps exceeding 3.0s (maximum gap: {cadence_max:.1f}s). Continuous segmentation will be enforced without interpolation."
        )

    duration_seconds = float(times_arr[-1] - times_arr[0]) if len(times_arr) > 0 else 0.0
    status = "PASSED" if not warnings else "PASSED_WITH_WARNINGS"

    return {
        "status": status,
        "n_records": len(df),
        "total_records": len(df),
        "duration_seconds": duration_seconds,
        "cadence_median": cadence_median,
        "cadence_median_sec": cadence_median,
        "cadence_min_sec": cadence_min,
        "cadence_max_sec": cadence_max,
        "n_telemetry_gaps": n_gaps,
        "n_cadence_gaps": n_gaps,
        "n_non_finite": n_non_finite,
        "non_finite_pct": pct_non_finite,
        "n_negative": n_negative,
        "negative_pct": pct_negative,
        "n_duplicates": n_duplicates,
        "warnings": warnings,
        "non_finite": non_finite_res,
        "negative": negative_res,
        "duplicates": duplicate_res,
        "gti_coverage": gti_coverage,
    }


def execute_dataset_inference(
    df: pd.DataFrame,
    pipeline: Optional[InferencePipeline] = None,
    gti_intervals: Optional[List[Tuple[float, float]]] = None,
    window_seconds: float = 60.0,
    stride_seconds: float = 10.0,
    threshold: float = 0.50,
    min_segment_seconds: float = 60.0,
    max_gap_seconds: float = 3.0,
) -> Dict[str, Any]:
    """Run full causal preprocessing, feature engineering, and inference on uploaded dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Validated telemetry table with 'time' and 'counts'.
    pipeline : InferencePipeline, optional
        Inference pipeline instance. If omitted, uses default October 2026 pilot XGBoost.
    gti_intervals : list of (start, stop), optional
        Good Time Intervals.
    window_seconds : float, default=60.0
        Sliding window duration in seconds (Task A standard).
    stride_seconds : float, default=10.0
        Window stride in seconds.
    threshold : float, default=0.50
        Decision threshold for binary flare classification.
    min_segment_seconds : float, default=60.0
        Minimum continuous segment duration.
    max_gap_seconds : float, default=3.0
        Maximum time gap before creating a new segment (never bridged).

    Returns
    -------
    dict
        Structured output containing results DataFrame, candidate episodes, and summary metrics.

    Raises
    ------
    UploadValidationError
        If no continuous segments or sliding windows could be constructed.
    """
    pipe = pipeline or get_default_pipeline()

    # Step 1: Clean & Filter Telemetry (strictly logging dropped samples, never interpolating)
    finite_df, nan_excl = exclude_non_finite(df, value_col="counts", time_col="time")
    nonneg_df, neg_excl = exclude_negative(finite_df, value_col="counts", time_col="time")

    # Drop duplicate timestamps if any
    clean_df = nonneg_df.drop_duplicates(subset=["time"]).reset_index(drop=True)

    # Step 2: Apply GTI if provided
    gti_excl_count = 0
    if gti_intervals:
        gti_applied_df, gti_excl = apply_gti(
            clean_df,
            time_col="time",
            gti_intervals=gti_intervals,
            boundary="START_INCLUSIVE_STOP_EXCLUSIVE",
        )
        gti_excl_count = len(gti_excl)
    else:
        gti_applied_df = clean_df

    if len(gti_applied_df) < MIN_REQUIRED_SAMPLES:
        raise UploadValidationError(
            f"After quality filtering and GTI masking, only {len(gti_applied_df)} samples remained. "
            f"At least {MIN_REQUIRED_SAMPLES} samples are required to perform sliding-window feature analysis."
        )

    # Step 3: Continuous Segmentation (Strictly preserving telemetry gaps without interpolation)
    segments, seg_excl = segment_continuous(
        gti_applied_df,
        time_col="time",
        max_gap_seconds=max_gap_seconds,
        min_segment_seconds=min_segment_seconds,
        stem="upload_seg",
    )

    if not segments:
        raise UploadValidationError(
            f"No continuous observation segments >= {min_segment_seconds}s were identified. "
            "Data was either too heavily fragmented by gaps or truncated below minimum duration."
        )

    # Step 4: Sliding Windows & Causal Feature Extraction
    all_rows: List[Dict[str, Any]] = []

    for seg in segments:
        win_df, _ = generate_windows(
            seg.dataframe,
            segment_id=seg.segment_id,
            window_seconds=window_seconds,
            stride_seconds=stride_seconds,
            time_col="time",
            value_col="counts",
            is_final=False,
        )

        if win_df.empty:
            continue

        times_seg = seg.dataframe["time"].to_numpy(dtype=np.float64)
        counts_seg = seg.dataframe["counts"].to_numpy(dtype=np.float64)

        for _, w_row in win_df.iterrows():
            w_start = float(w_row["window_start"])
            w_end = float(w_row["window_end"])
            s_idx = int(w_row["start_index"])
            e_idx = int(w_row["end_index"]) + 1

            w_times = times_seg[s_idx:e_idx]
            w_vals = counts_seg[s_idx:e_idx]

            base_val, _ = causal_baseline(
                segment_df=seg.dataframe,
                window_start=w_start,
                lookback_seconds=600.0,
                time_col="time",
                value_col="counts",
                min_samples=15,
                is_final=False,
            )

            feat_vals, _ = compute_features(
                window_values=w_vals,
                window_times=w_times,
                baseline_value=base_val,
                n_expected_samples=int(window_seconds),
            )

            row_dict = {
                "window_id": str(w_row["window_id"]),
                "segment_id": seg.segment_id,
                "window_start": w_start,
                "window_end": w_end,
                "baseline_value": base_val,
                **feat_vals,
            }
            all_rows.append(row_dict)

    if not all_rows:
        raise UploadValidationError(
            "Could not generate sliding windows from the observation segments."
        )

    features_df = pd.DataFrame(all_rows)

    # Step 5: Model Inference using Existing Frozen Model
    probs = pipe.predict_proba(features_df)
    preds = pipe.predict(features_df, threshold=threshold)

    results_rows = []
    for idx, p_res in enumerate(preds):
        w_st = float(features_df.iloc[idx]["window_start"])
        w_en = float(features_df.iloc[idx]["window_end"])
        p_prob = float(probs[idx])
        is_flare = bool(p_prob >= threshold)
        margin = round(abs(p_prob - threshold) * 2.0, 4)
        risk = classify_risk(p_prob)

        # Format UTC representation if timestamps look like epoch seconds
        utc_str = None
        if w_en > 1e8:
            try:
                utc_str = datetime.fromtimestamp(w_en, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            except Exception:
                utc_str = None

        results_rows.append({
            "window_id": features_df.iloc[idx]["window_id"],
            "segment_id": features_df.iloc[idx]["segment_id"],
            "window_start": round(w_st, 2),
            "window_end": round(w_en, 2),
            "utc_time": utc_str,
            "flare_probability": round(p_prob, 4),
            "flare_detected": is_flare,
            "threshold_used": threshold,
            "risk_level": risk,
            "boundary_margin": margin,
            "mean_count_rate": round(float(features_df.iloc[idx].get("mean", 0.0)), 2),
            "peak_count_rate": round(float(features_df.iloc[idx].get("max", 0.0)), 2),
            "baseline_flux": round(float(features_df.iloc[idx].get("baseline_value", 0.0)), 2) if not pd.isna(features_df.iloc[idx].get("baseline_value")) else np.nan,
        })

    results_df = pd.DataFrame(results_rows)

    # Step 6: Merge positive windows into candidate flare episodes
    pos_windows = [(r["window_start"], r["window_end"]) for r in results_rows if r["flare_detected"]]
    pos_scores = [r["flare_probability"] for r in results_rows if r["flare_detected"]]
    merged_intervals = merge_positive_windows(pos_windows, pos_scores, merge_gap_seconds=60.0)

    candidate_episodes = []
    for idx, interval in enumerate(merged_intervals):
        ep_risk = classify_risk(interval.max_score or 0.5)
        utc_start = None
        utc_end = None
        if interval.start_sec > 1e8:
            try:
                utc_start = datetime.fromtimestamp(interval.start_sec, tz=timezone.utc).strftime("%H:%M:%S UTC")
                utc_end = datetime.fromtimestamp(interval.end_sec, tz=timezone.utc).strftime("%H:%M:%S UTC")
            except Exception:
                pass

        candidate_episodes.append({
            "episode_id": f"EPISODE_{idx+1:03d}",
            "start_sec": interval.start_sec,
            "end_sec": interval.end_sec,
            "duration_sec": interval.duration_sec,
            "n_windows": interval.n_windows,
            "peak_probability": round(interval.max_score or 0.0, 4),
            "risk_level": ep_risk,
            "utc_start": utc_start,
            "utc_end": utc_end,
        })

    n_pos_windows = int(results_df["flare_detected"].sum())
    total_evaluated_windows = len(results_df)

    summary = {
        "model_version": pipe.version_info["model_version"],
        "profile_id": pipe.version_info["profile_id"],
        "model_name": pipe.version_info["model_name"],
        "threshold_used": threshold,
        "window_duration_seconds": window_seconds,
        "stride_seconds": stride_seconds,
        "total_raw_samples": len(df),
        "clean_samples_retained": len(gti_applied_df),
        "continuous_segments_count": len(segments),
        "total_windows_evaluated": total_evaluated_windows,
        "flaring_windows_detected": n_pos_windows,
        "candidate_flare_episodes_count": len(candidate_episodes),
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "task": "Task A: 60-Second Window Flare Detection",
        "scientific_disclaimer": (
            "NOTICE: This analysis evaluates in-window flare presence (Task A) using the frozen SOLARIS-A1 model. "
            "It does not perform advance flare forecasting (Task B). Research benchmark only; not for mission-critical flight operations."
        ),
    }

    exclusions_summary = {
        "n_nan_dropped": len(nan_excl),
        "n_negative_dropped": len(neg_excl),
        "n_outside_gti_dropped": gti_excl_count,
        "n_short_segment_samples_dropped": len(seg_excl),
    }

    return {
        "summary": summary,
        "results_df": results_df,
        "features_df": features_df,
        "candidate_episodes": candidate_episodes,
        "exclusions": exclusions_summary,
        "segments": [s.to_dict() for s in segments],
    }
