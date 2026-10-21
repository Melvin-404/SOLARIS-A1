"""Good Time Interval (GTI) coverage analysis for SOLARIS-A1 (Stage 4).

Loads GTI intervals using configured candidate column names and quantifies coverage
against observation timestamps. Pure quantification; never removes or filters samples.
Special rule: if GTI table has zero rows, records 'GTI EMPTY FOR THIS OBSERVATION'.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from astropy.io import fits


class GTIColumnError(ValueError):
    """Raised when configured GTI column names are not present in the FITS file."""
    pass


def load_gti_intervals(
    path: Union[Path, str],
    start_col: str = "START",
    stop_col: str = "STOP",
    hdu_index: int = 1,
) -> Dict[str, Any]:
    """Read GTI intervals from FITS file strictly read-only.
    
    Refuses to run if configured start_col or stop_col is absent.
    Detects zero-row tables, inverted intervals, and overlapping intervals.
    
    Parameters
    ----------
    path : Path or str
        Path to the GTI FITS file.
    start_col : str
        Column name for interval start timestamp (from column_roles.yaml).
    stop_col : str
        Column name for interval stop timestamp (from column_roles.yaml).
    hdu_index : int
        Index of the GTI BinTableHDU (default 1).
        
    Returns
    -------
    dict
        Structured GTI interval description and anomaly flags.
        
    Raises
    -------
    GTIColumnError
        If configured column names are missing from the table.
    """
    gti_path = Path(path)
    if not gti_path.is_file():
        raise FileNotFoundError(f"GTI file not found: {gti_path}")

    with fits.open(gti_path, mode="readonly", memmap=True) as hdul:
        if len(hdul) <= hdu_index or not isinstance(hdul[hdu_index], (fits.BinTableHDU, fits.TableHDU)):
            return {
                "status": "EMPTY",
                "message": "GTI EMPTY FOR THIS OBSERVATION",
                "file_name": gti_path.name,
                "n_intervals": 0,
                "intervals": [],
                "inverted": [],
                "overlaps": [],
            }

        table_hdu = hdul[hdu_index]
        col_names = table_hdu.columns.names
        n_rows = len(table_hdu.data) if table_hdu.data is not None else 0

        # Special rule: 0 rows
        if n_rows == 0:
            return {
                "status": "EMPTY",
                "message": "GTI EMPTY FOR THIS OBSERVATION",
                "file_name": gti_path.name,
                "n_intervals": 0,
                "intervals": [],
                "inverted": [],
                "overlaps": [],
            }

        # Validate column names
        missing = [col for col in (start_col, stop_col) if col not in col_names]
        if missing:
            raise GTIColumnError(
                f"Configured GTI column(s) {missing} not found in '{gti_path.name}'. "
                f"Available columns in HDU {hdu_index}: {list(col_names)}. "
                "Refusing to execute with unconfirmed column names."
            )

        start_vals = np.asarray(table_hdu.data[start_col], dtype=np.float64)
        stop_vals = np.asarray(table_hdu.data[stop_col], dtype=np.float64)

        intervals: List[Dict[str, float]] = []
        inverted: List[Dict[str, Any]] = []

        for i, (s, e) in enumerate(zip(start_vals, stop_vals)):
            duration = float(e - s)
            inv_info = {"index": i, "start": float(s), "stop": float(e), "duration_s": duration}
            intervals.append(inv_info)
            if e <= s:
                inverted.append(inv_info)

        # Check for overlaps (chronological order)
        overlaps: List[Dict[str, Any]] = []
        for i in range(len(intervals) - 1):
            if intervals[i]["stop"] > intervals[i + 1]["start"]:
                overlaps.append({
                    "interval_1_index": i,
                    "interval_2_index": i + 1,
                    "interval_1": intervals[i],
                    "interval_2": intervals[i + 1],
                    "overlap_s": float(intervals[i]["stop"] - intervals[i + 1]["start"]),
                })

        return {
            "status": "VALID",
            "message": f"Successfully loaded {n_rows} GTI intervals.",
            "file_name": gti_path.name,
            "n_intervals": n_rows,
            "intervals": intervals,
            "inverted": inverted,
            "overlaps": overlaps,
        }


def compute_coverage(
    times: np.ndarray,
    gti_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Quantify GTI coverage against observation timestamps without modifying data.
    
    Parameters
    ----------
    times : np.ndarray
        Array of observation timestamps from the light curve.
    gti_data : dict
        Output from load_gti_intervals.
        
    Returns
    -------
    dict
        Coverage metrics: covered duration, covered fraction, sample counts
        inside and outside GTI, and empty intervals.
    """
    t_arr = np.asarray(times, dtype=np.float64)
    total_samples = int(len(t_arr))

    if gti_data.get("status") == "EMPTY" or gti_data.get("n_intervals", 0) == 0:
        return {
            "gti_status": "GTI EMPTY FOR THIS OBSERVATION",
            "n_intervals": 0,
            "covered_duration_s": 0.0,
            "obs_span_s": float(np.max(t_arr) - np.min(t_arr)) if total_samples > 1 else 0.0,
            "gti_covered_fraction": 0.0,
            "n_samples_inside_gti": 0,
            "n_samples_outside_gti": total_samples,
            "empty_intervals": [],
            "detail": "GTI file has 0 rows for this observation. All samples treated as outside GTI.",
        }

    if total_samples == 0:
        return {
            "gti_status": "VALID",
            "n_intervals": gti_data.get("n_intervals", 0),
            "covered_duration_s": 0.0,
            "obs_span_s": 0.0,
            "gti_covered_fraction": 0.0,
            "n_samples_inside_gti": 0,
            "n_samples_outside_gti": 0,
            "empty_intervals": [],
            "detail": "Empty timestamp array provided.",
        }

    intervals = gti_data.get("intervals", [])
    inside_mask = np.zeros(total_samples, dtype=bool)
    empty_intervals: List[Dict[str, Any]] = []
    interval_sample_counts: List[int] = []

    for inv in intervals:
        s = inv["start"]
        e = inv["stop"]
        in_this = (t_arr >= s) & (t_arr <= e)
        cnt = int(in_this.sum())
        interval_sample_counts.append(cnt)
        inside_mask |= in_this
        if cnt == 0:
            empty_intervals.append(inv)

    n_inside = int(inside_mask.sum())
    n_outside = int((~inside_mask).sum())
    sample_fraction = float(n_inside / total_samples) if total_samples > 0 else 0.0

    # Total duration of non-inverted intervals
    total_gti_duration = sum(max(0.0, inv["stop"] - inv["start"]) for inv in intervals)
    obs_span = float(np.max(t_arr) - np.min(t_arr)) if total_samples > 1 else 0.0

    return {
        "gti_status": "VALID",
        "n_intervals": len(intervals),
        "covered_duration_s": float(total_gti_duration),
        "obs_span_s": float(obs_span),
        "gti_covered_fraction": sample_fraction,
        "n_samples_inside_gti": n_inside,
        "n_samples_outside_gti": n_outside,
        "empty_intervals": empty_intervals,
        "interval_sample_counts": interval_sample_counts,
        "detail": (
            f"Coverage: {n_inside}/{total_samples} samples inside GTI ({sample_fraction * 100:.2f}%). "
            f"{n_outside} samples outside GTI. {len(empty_intervals)} intervals had zero samples."
        ),
    }
