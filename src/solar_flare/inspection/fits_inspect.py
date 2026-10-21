"""Core FITS inspection utilities for SOLARIS-A1.

Extracts HDU structures, headers, table columns, and numerical summaries from
SoLEXS FITS files without mutating files or assuming predefined column semantics.
All operations are strictly read-only.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
from astropy.io import fits

TIME_COLUMN_CANDIDATE_KEYWORDS = ("TIME", "DATE", "TSTART", "TSTOP", "START", "STOP", "SEC", "MJD", "UTC")



class InspectionError(Exception):
    """Raised when FITS inspection fails due to malformed data, invalid HDUs, or corrupted files."""
    pass


def _open_fits_readonly(path: Union[Path, str]) -> fits.HDUList:
    """Open a FITS file in strictly read-only mode without memmap.

    Args:
        path: Path to the FITS or compressed FITS (.gz) file.

    Returns:
        fits.HDUList: Opened HDU list.

    Raises:
        FileNotFoundError: If the file does not exist.
        InspectionError: If the file is not a valid FITS file.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"FITS file not found: {file_path}")

    try:
        # mode='readonly' and memmap=False guarantee zero modifications to the file
        return fits.open(str(file_path), mode="readonly", memmap=False)
    except OSError as exc:
        raise InspectionError(f"Failed to open FITS file '{file_path}': {exc}") from exc


def list_hdus(path: Union[Path, str]) -> List[Dict[str, Any]]:
    """List all HDU extensions in a FITS file.

    Args:
        path: Path to the FITS file.

    Returns:
        List[Dict[str, Any]]: Descriptors containing index, name, ver, type, rows, and columns.
    """
    descriptors: List[Dict[str, Any]] = []
    with _open_fits_readonly(path) as hdul:
        for idx, hdu in enumerate(hdul):
            is_table = isinstance(hdu, (fits.BinTableHDU, fits.TableHDU))
            rows = int(hdu.data.shape[0]) if (is_table and hdu.data is not None) else 0
            cols = len(hdu.columns) if is_table else 0

            descriptors.append({
                "index": idx,
                "name": hdu.name if hdu.name else f"HDU_{idx}",
                "ver": getattr(hdu, "ver", 1),
                "type": type(hdu).__name__,
                "shape": tuple(hdu.shape) if getattr(hdu, "shape", None) is not None else (),
                "rows": rows,
                "columns_count": cols,
            })
    return descriptors


def read_header_dict(
    path: Union[Path, str],
    hdu: Union[int, str] = 0,
) -> Dict[str, Dict[str, Any]]:
    """Read all header cards from a specified HDU as a structured dictionary.

    Args:
        path: Path to the FITS file.
        hdu: HDU index (int) or extension name (str). Defaults to 0 (Primary).

    Returns:
        Dict[str, Dict[str, Any]]: Mapping of keyword -> {value, comment}.

    Raises:
        InspectionError: If the requested HDU does not exist.
    """
    with _open_fits_readonly(path) as hdul:
        try:
            target_hdu = hdul[hdu]
        except (IndexError, KeyError) as exc:
            raise InspectionError(
                f"HDU '{hdu}' not found in '{path}'. Available: {[h.name for h in hdul]}"
            ) from exc

        header_dict: Dict[str, Dict[str, Any]] = {}
        for card in target_hdu.header.cards:
            kw = card.keyword
            if not kw or kw in ("COMMENT", "HISTORY"):
                continue
            header_dict[kw] = {
                "value": card.value,
                "comment": card.comment if card.comment else "",
            }
        return header_dict


def describe_columns(
    path: Union[Path, str],
    hdu: Union[int, str] = 1,
) -> List[Dict[str, Any]]:
    """Extract column definitions and formats from a table HDU.

    Args:
        path: Path to the FITS file.
        hdu: HDU index or name containing the table. Defaults to 1.

    Returns:
        List[Dict[str, Any]]: List of column metadata dictionaries.

    Raises:
        InspectionError: If the HDU does not exist or is not a table.
    """
    with _open_fits_readonly(path) as hdul:
        try:
            target_hdu = hdul[hdu]
        except (IndexError, KeyError) as exc:
            raise InspectionError(
                f"HDU '{hdu}' not found in '{path}'."
            ) from exc

        if not isinstance(target_hdu, (fits.BinTableHDU, fits.TableHDU)):
            raise InspectionError(
                f"HDU '{hdu}' in '{path}' is a {type(target_hdu).__name__}, not a table HDU."
            )

        cols: List[Dict[str, Any]] = []
        for col in target_hdu.columns:
            cols.append({
                "name": col.name,
                "format": col.format,
                "unit": col.unit if col.unit else "",
                "dim": str(col.dim) if col.dim else "",
                "disp": col.disp if col.disp else "",
            })
        return cols


def summarise_time_columns(
    path: Union[Path, str],
    hdu: Union[int, str] = 1,
) -> List[Dict[str, Any]]:
    """Detect and summarize candidate time columns in a table HDU.

    Detection relies on keyword matching in column names and presence of
    astronomical time headers (TIMESYS, MJDREF, etc.). Column roles remain
    strictly candidate interpretations for human review.

    Args:
        path: Path to the FITS file.
        hdu: HDU index or name. Defaults to 1.

    Returns:
        List[Dict[str, Any]]: List of candidate time column summaries.
    """
    with _open_fits_readonly(path) as hdul:
        try:
            target_hdu = hdul[hdu]
        except (IndexError, KeyError) as exc:
            raise InspectionError(f"HDU '{hdu}' not found in '{path}'.") from exc

        if not isinstance(target_hdu, (fits.BinTableHDU, fits.TableHDU)) or target_hdu.data is None:
            return []

        data = target_hdu.data
        candidates: List[Dict[str, Any]] = []

        for col in target_hdu.columns:
            col_upper = col.name.upper()
            is_candidate = any(kw in col_upper for kw in TIME_COLUMN_CANDIDATE_KEYWORDS)
            if not is_candidate:
                continue

            arr = data[col.name]
            if not np.issubdtype(arr.dtype, np.number):
                continue

            flat = np.asarray(arr, dtype=np.float64).flatten()
            valid_mask = np.isfinite(flat)
            valid = flat[valid_mask]

            if len(valid) == 0:
                candidates.append({
                    "column_name": col.name,
                    "unit": col.unit or "",
                    "total_count": len(flat),
                    "valid_count": 0,
                    "min": None,
                    "max": None,
                    "median_spacing": None,
                    "unique_count": 0,
                    "is_monotonic": False,
                    "status": "CANDIDATE_ALL_NAN_OR_EMPTY",
                })
                continue

            diffs = np.diff(valid) if len(valid) > 1 else np.array([])
            median_spacing = float(np.median(diffs)) if len(diffs) > 0 else None
            is_monotonic = bool(np.all(diffs >= 0)) if len(diffs) > 0 else True
            unique_count = int(len(np.unique(valid)))

            candidates.append({
                "column_name": col.name,
                "unit": col.unit or "",
                "total_count": int(len(flat)),
                "valid_count": int(len(valid)),
                "min": float(np.min(valid)),
                "max": float(np.max(valid)),
                "median_spacing": median_spacing,
                "unique_count": unique_count,
                "is_monotonic": is_monotonic,
                "status": "CANDIDATE_TIME_AXIS",
            })

        return candidates


def summarise_numeric_columns(
    path: Union[Path, str],
    hdu: Union[int, str] = 1,
) -> Dict[str, Dict[str, Any]]:
    """Compute comprehensive statistical metrics for all numeric columns in a table.

    Includes explicit counts of NaN and Infinite values without crashing.

    Args:
        path: Path to the FITS file.
        hdu: HDU index or name. Defaults to 1.

    Returns:
        Dict[str, Dict[str, Any]]: Mapping of column name -> metrics dictionary.
    """
    with _open_fits_readonly(path) as hdul:
        try:
            target_hdu = hdul[hdu]
        except (IndexError, KeyError) as exc:
            raise InspectionError(f"HDU '{hdu}' not found in '{path}'.") from exc

        if not isinstance(target_hdu, (fits.BinTableHDU, fits.TableHDU)) or target_hdu.data is None:
            return {}

        data = target_hdu.data
        results: Dict[str, Dict[str, Any]] = {}

        for col in target_hdu.columns:
            arr = data[col.name]
            if not np.issubdtype(arr.dtype, np.number):
                continue

            flat = np.asarray(arr, dtype=np.float64).flatten()
            total_count = int(len(flat))
            nan_count = int(np.isnan(flat).sum())
            inf_count = int(np.isinf(flat).sum())

            finite = flat[np.isfinite(flat)]
            if len(finite) == 0:
                results[col.name] = {
                    "count": total_count,
                    "finite_count": 0,
                    "nan_count": nan_count,
                    "inf_count": inf_count,
                    "min": None,
                    "max": None,
                    "mean": None,
                    "median": None,
                }
            else:
                results[col.name] = {
                    "count": total_count,
                    "finite_count": int(len(finite)),
                    "nan_count": nan_count,
                    "inf_count": inf_count,
                    "min": float(np.min(finite)),
                    "max": float(np.max(finite)),
                    "mean": float(np.mean(finite)),
                    "median": float(np.median(finite)),
                }

        return results
