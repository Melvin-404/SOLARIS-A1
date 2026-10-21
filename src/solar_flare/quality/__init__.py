"""Data quality assessment subsystem for SOLARIS-A1.

Provides non-destructive quality checks, cadence diagnostics, GTI coverage
quantification, column-role evidence compilation, and per-file quality reporting.
All metrics are observational and non-mutating.
"""

from solar_flare.quality.checks import (
    check_non_finite,
    check_negative_values,
    check_duplicate_timestamps,
    check_time_ordering,
    check_zero_runs,
    check_quality_flags,
    check_candidate_spikes,
)
from solar_flare.quality.cadence import (
    estimate_cadence,
    find_cadence_gaps,
)
from solar_flare.quality.gti_coverage import (
    load_gti_intervals,
    compute_coverage,
)
from solar_flare.quality.roles import generate_column_role_evidence

__all__ = [
    "check_non_finite",
    "check_negative_values",
    "check_duplicate_timestamps",
    "check_time_ordering",
    "check_zero_runs",
    "check_quality_flags",
    "check_candidate_spikes",
    "estimate_cadence",
    "find_cadence_gaps",
    "load_gti_intervals",
    "compute_coverage",
    "generate_column_role_evidence",
]
