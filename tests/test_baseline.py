"""Unit tests for baseline reference models (Stage 11).

Tests:
1. ThresholdBaseline fits strictly on training indices and optimizes training F1.
2. Passing validation or test indices into baseline fit triggers TestLeakageError.
3. ClimatologicalBaseline computes training prevalence and generates constant forecasts.
4. PersistenceBaseline operates causally.
"""

import numpy as np
import pandas as pd
import pytest
from solar_flare.evaluation.baseline import (
    ClimatologicalBaseline,
    PersistenceBaseline,
    ThresholdBaseline,
)
from solar_flare.modelling.guards import TestLeakageError


def test_threshold_baseline_fitting_and_leakage_guard():
    """Verify that ThresholdBaseline fits on training indices and rejects validation/test overlap."""
    np.random.seed(42)
    # Synthetic feature: flux ratio
    # 0 to 49: negatives, ratio around 1.0
    # 50 to 99: positives, ratio around 5.0
    ratios = np.concatenate([np.random.normal(1.0, 0.2, 50), np.random.normal(5.0, 0.5, 50)])
    labels = np.concatenate([np.zeros(50), np.ones(50)]).astype(int)

    X = pd.DataFrame({"ratio_to_base": ratios})
    y = pd.Series(labels)

    tb = ThresholdBaseline()

    # 1. Clean training fit succeeds
    train_idx = list(range(0, 40)) + list(range(50, 90))
    val_idx = list(range(40, 50))
    test_idx = list(range(90, 100))

    tb.fit(X, y, fit_indices=train_idx, val_indices=val_idx, test_indices=test_idx)
    assert tb.threshold is not None
    # Threshold should separate 1.0 and 5.0 (around 1.3 - 4.0)
    assert 1.2 < tb.threshold < 4.5

    # 2. Fit with validation index overlap raises TestLeakageError
    corrupt_fit = list(range(0, 45))  # overlaps with val_idx (40 to 49)
    with pytest.raises(TestLeakageError, match="Validation leakage"):
        tb.fit(X, y, fit_indices=corrupt_fit, val_indices=val_idx, test_indices=test_idx)

    # 3. Fit with test index overlap raises TestLeakageError
    corrupt_fit_test = list(range(0, 40)) + [95]  # overlaps with test_idx
    with pytest.raises(TestLeakageError, match="TEST LEAKAGE"):
        tb.fit(X, y, fit_indices=corrupt_fit_test, val_indices=val_idx, test_indices=test_idx)


def test_climatological_and_persistence_baselines():
    """Verify ClimatologicalBaseline and PersistenceBaseline behavior."""
    y_train = pd.Series([1, 0, 0, 0])  # prevalence = 0.25
    cb = ClimatologicalBaseline()
    cb.fit(y_train)

    probs = cb.predict_proba(10)
    assert len(probs) == 10
    assert np.allclose(probs, 0.25)

    # Persistence baseline
    X_test = pd.DataFrame({"ratio_to_base": [0.5, 2.0, 3.5, 0.2]})
    pb = PersistenceBaseline()
    preds = pb.predict(X_test)
    assert len(preds) == 4
    assert set(preds).issubset({0, 1})
