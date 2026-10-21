"""Window-level classification metrics for SOLARIS-A1 (Stage 11).

Evaluates binary classification performance on discrete temporal windows:
- Precision, Recall, F1 score (with zero_division explicitly declared and tracked)
- Confusion matrix counts (TP, FP, TN, FN)
- PR-AUC (Average Precision score) - Primary imbalanced metric
- ROC-AUC (Secondary metric; handles degenerate class distributions)
- Mandatory prevalence reporting (n_pos / n_total)
- Auditable NA label tracking and exclusion
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Sequence, Union
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass(frozen=True)
class WindowMetricsReport:
    """Structured report of window-level classification performance."""

    n_total: int
    n_evaluated: int
    n_excluded_na: int
    n_pos: int
    n_neg: int
    prevalence: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float
    pr_auc: Optional[float]
    roc_auc: Optional[float]
    zero_division_value: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary representation."""
        return asdict(self)


def compute_window_metrics(
    y_true: Union[Sequence[Any], np.ndarray, pd.Series],
    y_pred: Union[Sequence[Any], np.ndarray, pd.Series],
    y_score: Optional[Union[Sequence[float], np.ndarray, pd.Series]] = None,
    zero_division: float = 0.0,
) -> WindowMetricsReport:
    """Compute comprehensive window-level metrics.

    Parameters
    ----------
    y_true : array-like
        Ground-truth labels (0, 1, or NaN/None for unverified).
    y_pred : array-like
        Binary predictions (0 or 1).
    y_score : array-like, optional
        Continuous predicted probability/score for positive class [0, 1].
    zero_division : float, default=0.0
        Value to assign when zero division occurs in precision/recall/F1.

    Returns
    -------
    WindowMetricsReport
        Dataclass containing all computed window metrics and prevalence.

    Raises
    ------
    ValueError
        If inputs are of mismatched lengths or contain non-binary labels (excluding NA).
    """
    y_t = pd.Series(y_true).copy()
    y_p = pd.Series(y_pred).copy()

    if len(y_t) != len(y_p):
        raise ValueError(
            f"Length mismatch between y_true ({len(y_t)}) and y_pred ({len(y_p)})"
        )

    n_total = len(y_t)

    # 1. Audit and exclude NA ground-truth labels
    na_mask = y_t.isna()
    n_excluded_na = int(na_mask.sum())

    valid_mask = ~na_mask
    y_t_valid = y_t[valid_mask].astype(float)
    y_p_valid = y_p[valid_mask].astype(float)

    n_evaluated = len(y_t_valid)
    if n_evaluated == 0:
        return WindowMetricsReport(
            n_total=n_total,
            n_evaluated=0,
            n_excluded_na=n_excluded_na,
            n_pos=0,
            n_neg=0,
            prevalence=0.0,
            true_positives=0,
            false_positives=0,
            true_negatives=0,
            false_negatives=0,
            precision=zero_division,
            recall=zero_division,
            f1=zero_division,
            pr_auc=None,
            roc_auc=None,
            zero_division_value=zero_division,
        )

    # 2. Strict binary validation
    unique_true = set(y_t_valid.unique())
    if not unique_true.issubset({0.0, 1.0}):
        raise ValueError(
            f"y_true contains non-binary values (after NA drop): {unique_true}. Only 0 and 1 are permitted."
        )

    unique_pred = set(y_p_valid.unique())
    if not unique_pred.issubset({0.0, 1.0}):
        raise ValueError(
            f"y_pred contains non-binary values: {unique_pred}. Only 0 and 1 are permitted."
        )

    y_t_int = y_t_valid.astype(int).values
    y_p_int = y_p_valid.astype(int).values

    n_pos = int((y_t_int == 1).sum())
    n_neg = int((y_t_int == 0).sum())
    prevalence = float(n_pos / n_evaluated) if n_evaluated > 0 else 0.0

    # 3. Confusion Matrix
    # Use labels=[0, 1] to guarantee 2x2 shape even if a class has 0 samples
    cm = confusion_matrix(y_t_int, y_p_int, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    # 4. Classification Metrics
    prec = float(precision_score(y_t_int, y_p_int, zero_division=zero_division))
    rec = float(recall_score(y_t_int, y_p_int, zero_division=zero_division))
    f1 = float(f1_score(y_t_int, y_p_int, zero_division=zero_division))

    # 5. Curve Metrics (PR-AUC and ROC-AUC)
    pr_auc: Optional[float] = None
    roc_auc: Optional[float] = None

    if y_score is not None:
        y_s = pd.Series(y_score)[valid_mask].astype(float).values
        if len(unique_true) > 1:
            try:
                pr_auc = float(average_precision_score(y_t_int, y_s))
            except Exception:
                pr_auc = None
            try:
                roc_auc = float(roc_auc_score(y_t_int, y_s))
            except Exception:
                roc_auc = None
        else:
            # Single class present in ground truth -> PR-AUC / ROC-AUC undefined
            pr_auc = None
            roc_auc = None

    return WindowMetricsReport(
        n_total=n_total,
        n_evaluated=n_evaluated,
        n_excluded_na=n_excluded_na,
        n_pos=n_pos,
        n_neg=n_neg,
        prevalence=prevalence,
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        precision=prec,
        recall=rec,
        f1=f1,
        pr_auc=pr_auc,
        roc_auc=roc_auc,
        zero_division_value=zero_division,
    )
