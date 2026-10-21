"""Unit tests for training-only preprocessing engine (Stage 10).

Validates:
- Preprocessor fit strictly rejects overlapping validation or test indices.
- Unhandled NaN values trigger MissingFeatureError under default imputer='NONE'.
- Clean training-only fit transforms novel data consistently without leakage.
"""

from __future__ import annotations

import pytest
import numpy as np
import pandas as pd

from solar_flare.modelling.preprocessing_fit import TrainingOnlyPreprocessor
from solar_flare.modelling.guards import TestLeakageError, MissingFeatureError


def test_fit_with_validation_indices_raises_leakage():
    """Verify that including validation indices in fit_indices raises TestLeakageError."""
    X = pd.DataFrame({"feat1": [1.0, 2.0, 3.0, 4.0, 5.0]})
    prep = TrainingOnlyPreprocessor(scaler="StandardScaler")

    fit_idx = [0, 1, 2]
    val_idx = [2, 3]  # Overlap at index 2

    with pytest.raises(TestLeakageError, match="VALIDATION LEAKAGE"):
        prep.fit(X, fit_indices=fit_idx, val_indices=val_idx)


def test_fit_with_test_indices_raises_leakage():
    """Verify that including test indices in fit_indices raises TestLeakageError."""
    X = pd.DataFrame({"feat1": [1.0, 2.0, 3.0, 4.0, 5.0]})
    prep = TrainingOnlyPreprocessor(scaler="StandardScaler")

    fit_idx = [0, 1, 4]
    test_idx = [3, 4]  # Overlap at index 4

    with pytest.raises(TestLeakageError, match="CRITICAL TEST LEAKAGE"):
        prep.fit(X, fit_indices=fit_idx, test_indices=test_idx)


def test_nan_in_training_features_raises_missing_feature_error():
    """Verify that NaN in training features raises MissingFeatureError under imputer='NONE'."""
    X = pd.DataFrame({
        "feat_clean": [1.0, 2.0, 3.0],
        "feat_nan": [1.0, np.nan, 3.0],
    })
    prep = TrainingOnlyPreprocessor(scaler="StandardScaler", imputer="NONE")

    with pytest.raises(MissingFeatureError, match="NaN values encountered"):
        prep.fit(X, fit_indices=[0, 1, 2])


def test_clean_training_only_fit_and_transform():
    """Verify that clean training-only fit learns mean/scale and transforms correctly."""
    X = pd.DataFrame({
        "feat1": [10.0, 20.0, 30.0, 40.0],
    })
    prep = TrainingOnlyPreprocessor(scaler="StandardScaler", imputer="NONE")

    # Fit on first 3 samples: mean = 20.0, std = sqrt(200/3) = 8.1649...
    prep.fit(X, fit_indices=[0, 1, 2])
    assert prep.is_fitted
    assert prep.fit_row_count == 3

    # Transform all 4 samples
    X_trans = prep.transform(X)
    assert len(X_trans) == 4
    # Mean of first 3 in X_trans should be 0.0
    assert np.isclose(X_trans.iloc[:3]["feat1"].mean(), 0.0)
