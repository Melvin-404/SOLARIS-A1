"""SOLARIS-A1 Dataset Export and Label Integration Subsystem (Stage 9).

Provides policy-guarded joining of feature windows with verified ground-truth labels,
and strict, auditable dataset export for Task A (Detection) and Task B (Forecasting).
"""

from __future__ import annotations

from solar_flare.export.join_labels import (
    load_approved_events,
    label_windows_detection,
    UnhandledPolicyCase,
)
from solar_flare.export.targets import (
    detection_target,
    prediction_target,
    assert_forecasting_approved,
    ForecastingNotApprovedError,
)
from solar_flare.export.dictionary import generate_data_dictionary
from solar_flare.export.export import (
    export_dataset,
    compute_export_id,
    DatasetExportError,
)

__all__ = [
    "load_approved_events",
    "label_windows_detection",
    "UnhandledPolicyCase",
    "detection_target",
    "prediction_target",
    "assert_forecasting_approved",
    "ForecastingNotApprovedError",
    "generate_data_dictionary",
    "export_dataset",
    "compute_export_id",
    "DatasetExportError",
]
