"""Labels subsystem for SOLARIS-A1 (Stage 6).

Contains schema definitions, policy assertions, source provenance tracking,
temporal compatibility checkers, and guarded label generation skeletons.
All supervised labeling is blocked until Gate G3 approval.
"""

from __future__ import annotations

from solar_flare.labels.schema import EventRecord, validate_event_records
from solar_flare.labels.policy import assert_labelling_approved, LabellingNotApprovedError
from solar_flare.labels.compatibility import (
    report_temporal_overlap,
    assess_source_compatibility,
    generate_compatibility_report,
)
from solar_flare.labels.matching import (
    interval_overlap_seconds,
    is_event_in_window,
)

__all__ = [
    "EventRecord",
    "validate_event_records",
    "assert_labelling_approved",
    "LabellingNotApprovedError",
    "report_temporal_overlap",
    "assess_source_compatibility",
    "generate_compatibility_report",
    "interval_overlap_seconds",
    "is_event_in_window",
]
