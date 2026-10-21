"""Probability calibration evaluation for SOLARIS-A1 (Stage 11).

Assesses probabilistic output reliability without modifying or recalibrating model scores:
- Reliability diagram binning (equal-width interval bins).
- Mean predicted probability vs. empirical observed fraction per bin.
- Expected Calibration Error (ECE) and Maximum Calibration Error (MCE).
- Brier score.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss


@dataclass(frozen=True)
class CalibrationBin:
    """Statistics for an individual probability bin."""

    bin_index: int
    bin_lower: float
    bin_upper: float
    n_samples: int
    mean_predicted: float
    observed_fraction: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CalibrationReport:
    """Structured report of probability calibration metrics."""

    brier_score: float
    expected_calibration_error: float
    max_calibration_error: float
    n_bins: int
    bins: List[CalibrationBin]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brier_score": self.brier_score,
            "expected_calibration_error": self.expected_calibration_error,
            "max_calibration_error": self.max_calibration_error,
            "n_bins": self.n_bins,
            "bins": [b.to_dict() for b in self.bins],
        }


def compute_calibration_assessment(
    y_true: Union[Sequence[Any], np.ndarray, pd.Series],
    y_prob: Union[Sequence[float], np.ndarray, pd.Series],
    n_bins: int = 10,
) -> CalibrationReport:
    """Compute calibration curve, ECE, MCE, and Brier score.

    Parameters
    ----------
    y_true : array-like
        Binary ground-truth labels (0 or 1).
    y_prob : array-like
        Predicted probabilities [0, 1].
    n_bins : int, default=10
        Number of equal-width probability bins.

    Returns
    -------
    CalibrationReport
        Dataclass containing calibration metrics and bin-level statistics.
    """
    y_t = pd.Series(y_true).dropna().astype(int).values
    y_p = pd.Series(y_prob).dropna().astype(float).values

    if len(y_t) != len(y_p):
        raise ValueError(
            f"Length mismatch: y_true ({len(y_t)}) vs y_prob ({len(y_p)})"
        )

    n_samples = len(y_t)
    if n_samples == 0:
        return CalibrationReport(
            brier_score=0.0,
            expected_calibration_error=0.0,
            max_calibration_error=0.0,
            n_bins=n_bins,
            bins=[],
        )

    # 1. Brier Score
    brier = float(brier_score_loss(y_t, y_p))

    # 2. Equal-width binning in [0, 1]
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins_data: List[CalibrationBin] = []
    weighted_abs_diff_sum = 0.0
    max_diff = 0.0

    for i in range(n_bins):
        lower = float(bin_edges[i])
        upper = float(bin_edges[i + 1])

        # Right-inclusive on last bin
        if i == n_bins - 1:
            mask = (y_p >= lower) & (y_p <= upper)
        else:
            mask = (y_p >= lower) & (y_p < upper)

        bin_count = int(np.sum(mask))
        if bin_count > 0:
            mean_pred = float(np.mean(y_p[mask]))
            obs_frac = float(np.mean(y_t[mask]))
            diff = abs(mean_pred - obs_frac)
            weighted_abs_diff_sum += (bin_count / n_samples) * diff
            max_diff = max(max_diff, diff)
        else:
            mean_pred = (lower + upper) / 2.0
            obs_frac = 0.0

        bins_data.append(
            CalibrationBin(
                bin_index=i,
                bin_lower=lower,
                bin_upper=upper,
                n_samples=bin_count,
                mean_predicted=mean_pred,
                observed_fraction=obs_frac,
            )
        )

    ece = float(weighted_abs_diff_sum)
    mce = float(max_diff)

    return CalibrationReport(
        brier_score=brier,
        expected_calibration_error=ece,
        max_calibration_error=mce,
        n_bins=n_bins,
        bins=bins_data,
    )
