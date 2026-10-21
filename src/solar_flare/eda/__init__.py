"""Exploratory Data Analysis (EDA) module for SOLARIS-A1 (Stage 5).

Provides pure functional routines for variability statistics, running robust baselines,
candidate transient detection, diagnostic plotting, and event comparison scaffolding.
All candidate intervals are strictly tagged as 'CANDIDATE — UNVERIFIED'.
No output represents a flare label, ground truth, or training target.
"""

from __future__ import annotations

from solar_flare.eda.variability import (
    rolling_summary,
    variability_stats,
    count_histogram_data,
)
from solar_flare.eda.bursts import (
    robust_baseline,
    candidate_intervals,
)
from solar_flare.eda.event_comparison import (
    compare_candidates_to_events,
)

__all__ = [
    "rolling_summary",
    "variability_stats",
    "count_histogram_data",
    "robust_baseline",
    "candidate_intervals",
    "compare_candidates_to_events",
]
