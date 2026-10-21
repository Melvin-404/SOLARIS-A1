"""Event record schema and validation for SOLARIS-A1 (Stage 6).

Defines the EventRecord dataclass and strict validation rules.
Validation enforces:
- Required fields
- onset <= peak <= end
- ISO 8601 or numeric epoch parseability
- Allowed time-system membership (fails if config list is PENDING/empty)
- Unique event_id
- source_id present in data/manifests/event_sources.csv
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from solar_flare.paths import project_root


@dataclass
class EventRecord:
    """Standardized solar flare event record representation."""
    event_id: str
    source_id: str
    onset_time: float
    end_time: float
    time_system: str
    classification: str
    classification_method: str
    peak_time: Optional[float] = None
    uncertainty_seconds: float = 0.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _parse_time(val: Any) -> float:
    """Parse time value into float seconds; handles numeric or ISO 8601 strings."""
    if isinstance(val, (int, float, np.integer, np.floating)):
        return float(val)
    if isinstance(val, str):
        # Try numeric string
        try:
            return float(val)
        except ValueError:
            pass
        # Try ISO 8601
        try:
            # Handle trailing Z
            iso_str = val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso_str)
            return dt.timestamp()
        except Exception as e:
            raise ValueError(f"Unparseable time value '{val}': {e}")
    raise ValueError(f"Invalid time value type: {type(val)}")


def validate_event_records(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None,
    event_sources_path: Optional[Union[Path, str]] = None,
) -> bool:
    """Validate a DataFrame of event records against strict scientific constraints.
    
    Parameters
    ----------
    df : pd.DataFrame
        Event records to validate.
    config : Optional[dict]
        Project configuration dictionary.
    event_sources_path : Optional[Path or str]
        Path to data/manifests/event_sources.csv.
        
    Returns
    -------
    bool
        True if all validation checks pass.
        
    Raises
    -------
    ValueError
        If any validation rule is violated.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Input event records must be a non-null pandas DataFrame.")

    if len(df) == 0:
        return True

    # 1. Required fields
    required_fields = {
        "event_id",
        "source_id",
        "onset_time",
        "end_time",
        "time_system",
        "classification",
        "classification_method",
    }
    missing = required_fields - set(df.columns)
    if missing:
        raise ValueError(f"Event records missing required field(s): {sorted(list(missing))}")

    # 2. Check no duplicate event_id
    dup_ids = df[df["event_id"].duplicated(keep=False)]["event_id"].unique().tolist()
    if dup_ids:
        raise ValueError(f"Duplicate event_id detected in event records: {dup_ids}")

    # 3. Check allowed time-system list from config
    allowed_time_systems: List[str] = []
    if config:
        labels_cfg = config.get("labels", {})
        sci_cfg = config.get("scientific_parameters", {})
        raw_list = labels_cfg.get("allowed_time_systems", sci_cfg.get("allowed_time_systems"))
        if isinstance(raw_list, list):
            allowed_time_systems = [str(x).upper() for x in raw_list]

    if not allowed_time_systems or any("PENDING" in s for s in allowed_time_systems):
        raise ValueError(
            "Allowed time-systems list in config is PENDING or unconfigured. "
            "Validation cannot proceed until the human researcher approves allowed time systems."
        )

    # 4. Check source_id against event_sources.csv
    root = project_root()
    src_csv = Path(event_sources_path) if event_sources_path else (root / "data" / "manifests" / "event_sources.csv")
    valid_source_ids = set()
    if src_csv.is_file():
        with open(src_csv, "r", encoding="utf-8") as sf:
            reader = csv.DictReader(sf)
            for r in reader:
                valid_source_ids.add(r.get("source_id", "").strip())

    for idx, row in df.iterrows():
        eid = row["event_id"]
        sid = str(row["source_id"]).strip()

        # Validate source_id presence
        if sid not in valid_source_ids:
            raise ValueError(f"Record '{eid}' has unknown source_id '{sid}' not registered in event_sources.csv")

        # Validate time_system
        tsys = str(row["time_system"]).strip().upper()
        if tsys not in allowed_time_systems:
            raise ValueError(
                f"Record '{eid}' has unapproved time_system '{tsys}'. "
                f"Approved time systems: {allowed_time_systems}"
            )

        # Parse and validate ordering: onset <= peak <= end
        onset = _parse_time(row["onset_time"])
        end = _parse_time(row["end_time"])

        if onset > end:
            raise ValueError(f"Record '{eid}' has invalid ordering: onset_time ({onset}) > end_time ({end})")

        has_peak = "peak_time" in row and pd.notna(row["peak_time"]) and row["peak_time"] is not None
        if has_peak:
            peak = _parse_time(row["peak_time"])
            if not (onset <= peak <= end):
                raise ValueError(
                    f"Record '{eid}' violates temporal sequence: onset ({onset}) <= peak ({peak}) <= end ({end})"
                )

    return True
