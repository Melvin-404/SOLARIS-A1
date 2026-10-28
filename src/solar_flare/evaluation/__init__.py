"""SOLARIS-A1 Evaluation Framework (Stage 11).

Provides modular, auditable, and single-shot evaluation utilities:
- Window metrics (precision, recall, F1, PR-AUC, ROC-AUC, prevalence, confusion matrix).
- Event-level detection metrics (overlap matching, detection rate, timing errors).
- False alarm analysis normalized by GTI-covered observation hours.
- Reference baselines (threshold, climatological, persistence).
- Calibration assessment (ECE, MCE, Brier score).
- Block bootstrap uncertainty estimation.
- Auditable multi-format evaluation reporting.
"""

from solar_flare.evaluation.window_metrics import (
    WindowMetricsReport,
    compute_window_metrics,
)
from solar_flare.evaluation.event_metrics import (
    EventMetricsReport,
    PredictedInterval,
    compute_event_metrics,
    merge_positive_windows,
)
from solar_flare.evaluation.false_alarms import (
    FalseAlarmRecord,
    FalseAlarmReport,
    MissedEventRecord,
    compute_false_alarm_analysis,
)
from solar_flare.evaluation.baseline import (
    ClimatologicalBaseline,
    PersistenceBaseline,
    ThresholdBaseline,
)
from solar_flare.evaluation.calibration import (
    CalibrationBin,
    CalibrationReport,
    compute_calibration_assessment,
)
from solar_flare.evaluation.uncertainty import (
    BootstrapUncertaintyReport,
    MetricCI,
    PairedComparisonReport,
    PairedDifferenceCI,
    compute_block_bootstrap_ci,
    compute_paired_bootstrap_comparison,
    create_temporal_clusters,
)
from solar_flare.evaluation.explainability import (
    check_shap_available,
    compute_permutation_feature_importance,
    compute_tree_feature_importance,
    generate_explainability_artifacts,
)
from solar_flare.evaluation.reporting import (
    MANDATORY_DISCLAIMER,
    PREDICTION_SKILL_DISCLAIMER,
    build_evaluation_report,
    write_dashboard_contract,
)

__all__ = [
    "WindowMetricsReport",
    "compute_window_metrics",
    "PredictedInterval",
    "EventMetricsReport",
    "merge_positive_windows",
    "compute_event_metrics",
    "FalseAlarmRecord",
    "MissedEventRecord",
    "FalseAlarmReport",
    "compute_false_alarm_analysis",
    "ThresholdBaseline",
    "ClimatologicalBaseline",
    "PersistenceBaseline",
    "CalibrationBin",
    "CalibrationReport",
    "compute_calibration_assessment",
    "MetricCI",
    "BootstrapUncertaintyReport",
    "compute_block_bootstrap_ci",
    "PairedDifferenceCI",
    "PairedComparisonReport",
    "compute_paired_bootstrap_comparison",
    "create_temporal_clusters",
    "check_shap_available",
    "compute_permutation_feature_importance",
    "compute_tree_feature_importance",
    "generate_explainability_artifacts",
    "MANDATORY_DISCLAIMER",
    "PREDICTION_SKILL_DISCLAIMER",
    "build_evaluation_report",
    "write_dashboard_contract",
]
