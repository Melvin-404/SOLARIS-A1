"""Preprocessing and GTI-aware segmentation subsystem for SOLARIS-A1 (Stage 7).

Provides non-destructive filtering, GTI boundary application, continuous segmentation,
and mathematical reconciliation of sample exclusions.
"""

from __future__ import annotations

from solar_flare.preprocessing.filters import (
    exclude_non_finite,
    exclude_flagged,
    exclude_negative,
    resolve_duplicate_timestamps,
    sort_by_time,
    DuplicateTimestampError,
)
from solar_flare.preprocessing.gti_apply import apply_gti
from solar_flare.preprocessing.segmentation import (
    segment_continuous,
    Segment,
    ParameterPendingError,
)
from solar_flare.preprocessing.audit import (
    ProcessingAudit,
    ReconciliationError,
    write_audit,
)

__all__ = [
    "exclude_non_finite",
    "exclude_flagged",
    "exclude_negative",
    "resolve_duplicate_timestamps",
    "sort_by_time",
    "DuplicateTimestampError",
    "apply_gti",
    "segment_continuous",
    "Segment",
    "ParameterPendingError",
    "ProcessingAudit",
    "ReconciliationError",
    "write_audit",
]
