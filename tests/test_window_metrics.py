"""Unit tests for window-level evaluation metrics (Stage 11).

Tests:
1. Exact confusion matrix and hand-computed precision, recall, F1.
2. Auditable NA label exclusion and reporting.
3. Strict non-binary label rejection.
4. Zero-division handling and explicit parameter reporting.
5. Prevalence calculation across balanced and imbalanced synthetic datasets.
"""

import numpy as np
import pandas as pd
import pytest
from solar_flare.evaluation.window_metrics import compute_window_metrics, WindowMetricsReport


def test_hand_computed_confusion_matrix_and_metrics():
    """Verify exact hand-computed confusion matrix, precision, recall, F1, and prevalence."""
    # 10 samples: 3 positives, 7 negatives
    # y_true: [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
    # y_pred: [1, 1, 0, 1, 0, 0, 0, 0, 0, 0]
    # TP: 2, FN: 1, FP: 1, TN: 6
    # Precision: 2 / (2 + 1) = 2/3 = 0.6666667
    # Recall: 2 / (2 + 1) = 2/3 = 0.6666667
    # F1: 2 * (2/3 * 2/3) / (2/3 + 2/3) = 2/3 = 0.6666667
    # Prevalence: 3 / 10 = 0.3
    y_true = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
    y_pred = [1, 1, 0, 1, 0, 0, 0, 0, 0, 0]
    y_score = [0.9, 0.8, 0.4, 0.7, 0.2, 0.1, 0.3, 0.1, 0.2, 0.05]

    rep = compute_window_metrics(y_true, y_pred, y_score)

    assert rep.n_total == 10
    assert rep.n_evaluated == 10
    assert rep.n_excluded_na == 0
    assert rep.n_pos == 3
    assert rep.n_neg == 7
    assert pytest.approx(rep.prevalence, 1e-5) == 0.3
    assert rep.true_positives == 2
    assert rep.false_positives == 1
    assert rep.false_negatives == 1
    assert rep.true_negatives == 6
    assert pytest.approx(rep.precision, 1e-5) == 2.0 / 3.0
    assert pytest.approx(rep.recall, 1e-5) == 2.0 / 3.0
    assert pytest.approx(rep.f1, 1e-5) == 2.0 / 3.0
    assert rep.pr_auc is not None and 0.0 <= rep.pr_auc <= 1.0
    assert rep.roc_auc is not None and 0.0 <= rep.roc_auc <= 1.0


def test_na_label_exclusion():
    """Verify that unverified NA labels are excluded and accurately audited."""
    # 8 samples with 3 NaN values in ground truth
    y_true = [1, 0, np.nan, 1, np.nan, 0, None, 0]
    y_pred = [1, 0, 0, 0, 1, 0, 1, 0]

    rep = compute_window_metrics(y_true, y_pred)

    assert rep.n_total == 8
    assert rep.n_excluded_na == 3
    assert rep.n_evaluated == 5
    # Evaluated y_true: [1, 0, 1, 0, 0] -> 2 positives, 3 negatives
    assert rep.n_pos == 2
    assert rep.n_neg == 3
    assert pytest.approx(rep.prevalence, 1e-5) == 2.0 / 5.0


def test_non_binary_labels_raise():
    """Verify that non-binary target or prediction values raise ValueError."""
    y_true = [0, 1, 2]
    y_pred = [0, 1, 1]
    with pytest.raises(ValueError, match="non-binary"):
        compute_window_metrics(y_true, y_pred)

    y_true_valid = [0, 1, 0]
    y_pred_invalid = [0, 0.5, 1]
    with pytest.raises(ValueError, match="non-binary"):
        compute_window_metrics(y_true_valid, y_pred_invalid)


def test_zero_division_handling_and_reporting():
    """Verify that zero-division cases (e.g. 0 positive predictions) return configured zero_division value."""
    # No predicted positives: TP=0, FP=0 -> Precision denominator is 0
    y_true = [1, 1, 0, 0]
    y_pred = [0, 0, 0, 0]

    rep = compute_window_metrics(y_true, y_pred, zero_division=0.0)

    assert rep.true_positives == 0
    assert rep.false_positives == 0
    assert rep.precision == 0.0
    assert rep.recall == 0.0
    assert rep.f1 == 0.0
    assert rep.zero_division_value == 0.0
