"""Static verification test ensuring no unverified or invented sources exist in documentation.

Enforces that every URL cited in docs/07_ground_truth_research.md is strictly registered
in data/manifests/event_sources.csv under the url_accessed column.
"""

from __future__ import annotations

import csv
from pathlib import Path
import re
import pytest

from solar_flare.paths import project_root


def test_no_invented_sources_in_docs07():
    """Verify that every URL in docs/07 is present in data/manifests/event_sources.csv."""
    root = project_root()
    doc_path = root / "docs" / "07_ground_truth_research.md"
    csv_path = root / "data" / "manifests" / "event_sources.csv"

    assert doc_path.is_file(), "docs/07_ground_truth_research.md does not exist"
    assert csv_path.is_file(), "data/manifests/event_sources.csv does not exist"

    # Extract registered URLs from CSV
    registered_urls = set()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("url_accessed", "").strip()
            if url:
                # Store normalized URL without trailing slash
                registered_urls.add(url.rstrip("/"))

    assert len(registered_urls) > 0, "No URLs registered in event_sources.csv"

    # Extract all URLs from docs/07
    doc_text = doc_path.read_text(encoding="utf-8")
    url_pattern = re.compile(r"https?://[^\s)\]>`\"']+", re.IGNORECASE)
    doc_urls = url_pattern.findall(doc_text)

    # Check each extracted URL
    unregistered_urls = []
    for raw_url in doc_urls:
        norm_url = raw_url.strip().rstrip(".,;:)")
        norm_url = norm_url.rstrip("/")
        if norm_url not in registered_urls:
            unregistered_urls.append(raw_url)

    assert not unregistered_urls, (
        f"Unregistered URL(s) detected in docs/07_ground_truth_research.md: {unregistered_urls}. "
        "Every URL mentioned in documentation must be recorded in data/manifests/event_sources.csv."
    )
