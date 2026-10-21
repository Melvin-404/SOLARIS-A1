"""SOLARIS-A1 Model Training and Experimentation Subsystem (Stage 10).

Provides:
- Strict split generators with temporal embargo buffers (splits.py)
- Cryptographic test set sealing and access lockdown (lock.py)
- Training-only preprocessing fit preventing feature leakage (preprocessing_fit.py)
- Reproducible model factory for scikit-learn and XGBoost (model_factory.py)
- Validation-only hyperparameter tuning and model selection (training.py)
- Rigorous leakage, split, and protocol guards (guards.py)
"""

from __future__ import annotations

from solar_flare.modelling.guards import (
    TestLeakageError,
    SplitNotApprovedError,
    ProtocolNotFrozenError,
    MissingFeatureError,
    assert_no_test_in_fit,
    assert_split_embargo_respected,
    assert_selection_uses_validation_only,
    assert_protocol_frozen,
)
from solar_flare.modelling.splits import (
    chronological_split,
    event_grouped_split,
    SplitReport,
)
from solar_flare.modelling.lock import (
    seal_test_set,
    verify_lock,
    log_test_access,
    read_sealed_test_set,
)
from solar_flare.modelling.preprocessing_fit import (
    TrainingOnlyPreprocessor,
)
from solar_flare.modelling.model_factory import (
    build_model,
    UnavailableModel,
)
from solar_flare.modelling.training import (
    run_selection,
)

__all__ = [
    "TestLeakageError",
    "SplitNotApprovedError",
    "ProtocolNotFrozenError",
    "MissingFeatureError",
    "assert_no_test_in_fit",
    "assert_split_embargo_respected",
    "assert_selection_uses_validation_only",
    "assert_protocol_frozen",
    "chronological_split",
    "event_grouped_split",
    "SplitReport",
    "seal_test_set",
    "verify_lock",
    "log_test_access",
    "read_sealed_test_set",
    "TrainingOnlyPreprocessor",
    "build_model",
    "UnavailableModel",
    "run_selection",
]
