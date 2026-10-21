"""Provenance management for external solar flare event sources (Stage 6).

Reads and writes data/manifests/event_sources.csv.
Guarantees:
- Header consistency
- Preserves human-entered rows exactly
- Never inserts or fabricates rows automatically
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from solar_flare.paths import project_root

EVENT_SOURCES_HEADER = [
    "source_id",
    "source_name",
    "url_accessed",
    "access_date",
    "version",
    "instrument",
    "energy_band_as_stated",
    "time_system_as_stated",
    "coverage_start",
    "coverage_end",
    "event_definition_as_stated",
    "classification_method_as_stated",
    "licence_or_terms_as_stated",
    "independent_of_solarsoft_heuristic",
    "verified_by_human",
    "notes",
]


def get_default_event_sources_path() -> Path:
    """Return default path to data/manifests/event_sources.csv."""
    return project_root() / "data" / "manifests" / "event_sources.csv"


def read_event_sources(
    csv_path: Optional[Union[Path, str]] = None,
) -> List[Dict[str, str]]:
    """Read event sources manifest into a list of row dictionaries.
    
    Parameters
    ----------
    csv_path : Optional[Path or str]
        Path to event_sources.csv. Defaults to data/manifests/event_sources.csv.
        
    Returns
    -------
    list of dict
        Registered source rows.
    """
    path = Path(csv_path) if csv_path else get_default_event_sources_path()
    if not path.is_file():
        return []

    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(dict(r))
    return rows


def write_event_sources(
    sources: List[Dict[str, Any]],
    csv_path: Optional[Union[Path, str]] = None,
) -> Path:
    """Write sources to event_sources.csv with exact standardized schema.
    
    Never synthesizes automatic records; writes only explicit provided sources.
    
    Parameters
    ----------
    sources : list of dict
        Source records to write.
    csv_path : Optional[Path or str]
        Destination path.
        
    Returns
    -------
    Path
        Destination path.
    """
    path = Path(csv_path) if csv_path else get_default_event_sources_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EVENT_SOURCES_HEADER)
        writer.writeheader()
        for s in sources:
            # Map existing fields, default to empty string for missing
            row = {col: s.get(col, "") for col in EVENT_SOURCES_HEADER}
            writer.writerow(row)

    return path
