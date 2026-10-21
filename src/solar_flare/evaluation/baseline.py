"""Baseline reference models for solar flare evaluation (Stage 11).

Provides non-learning, physics-based, and statistical reference benchmarks:
1. Threshold Baseline: Causal peak-to-baseline flux ratio threshold tuned strictly on
   training data to maximize training F1 (guarded against test/val leakage).
2. Climatological Baseline: Constant probability forecast based strictly on training prevalence.
3. Persistence Baseline: Forecasts that the future state equals the current observed causal state.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from solar_flare.evaluation.window_metrics import WindowMetricsReport, compute_window_metrics
from solar_flare.modelling.guards import TestLeakageError, assert_no_test_in_fit


class ThresholdBaseline:
    """Heuristic baseline threshold fitted strictly on training data."""

    def __init__(self, objective: str = "max_f1") -> None:
        self.objective = objective
        self.threshold: Optional[float] = None
        self.fit_feature_name: Optional[str] = None

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        fit_indices: Optional[Sequence[int]] = None,
        val_indices: Optional[Sequence[int]] = None,
        test_indices: Optional[Sequence[int]] = None,
        feature_name: Optional[str] = None,
    ) -> ThresholdBaseline:
        """Fit optimal threshold on training data only.

        Raises TestLeakageError if validation or test indices overlap with fit indices.
        """
        if fit_indices is not None:
            if test_indices is not None:
                assert_no_test_in_fit(fit_indices, test_indices)
            if val_indices is not None:
                val_overlap = set(fit_indices).intersection(set(val_indices))
                if val_overlap:
                    raise TestLeakageError(
                        f"Validation leakage in baseline fitting: {len(val_overlap)} overlapping indices."
                    )
            X_fit = X_train.iloc[fit_indices]
            y_fit = y_train.iloc[fit_indices]
        else:
            X_fit = X_train
            y_fit = y_train

        # Identify candidate feature (ratio_to_base, peak_to_baseline, or first column)
        col_candidates = [
            c for c in X_fit.columns
            if any(term in c.lower() for term in ["ratio_to_base", "peak_to_base", "ratio", "flux_max", "mean"])
        ]
        chosen_col = feature_name or (col_candidates[0] if col_candidates else X_fit.columns[0])
        self.fit_feature_name = chosen_col

        feat_values = X_fit[chosen_col].dropna().values
        y_vals = y_fit.values

        if len(feat_values) == 0 or len(np.unique(y_vals)) < 2:
            self.threshold = float(np.median(feat_values)) if len(feat_values) > 0 else 1.0
            return self

        # Search candidate thresholds over empirical percentiles
        percentiles = np.linspace(10, 95, 30)
        candidates = np.percentile(feat_values, percentiles)

        best_score = -1.0
        best_candidates = [float(candidates[0])]

        for cand in candidates:
            preds = (feat_values >= cand).astype(int)
            score = f1_score(y_vals, preds, zero_division=0.0)
            if score > best_score:
                best_score = score
                best_candidates = [float(cand)]
            elif score == best_score:
                best_candidates.append(float(cand))

        self.threshold = float(np.median(best_candidates))
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict binary class using the learned threshold."""
        if self.threshold is None or self.fit_feature_name is None:
            raise RuntimeError("ThresholdBaseline estimator must be fitted before predict.")
        col = self.fit_feature_name
        values = X[col].values
        return (values >= self.threshold).astype(int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict pseudo-probability scaled monotonically by feature distance."""
        if self.threshold is None or self.fit_feature_name is None:
            raise RuntimeError("ThresholdBaseline estimator must be fitted before predict_proba.")
        col = self.fit_feature_name
        values = X[col].values
        # Logistic sigmoid centered at threshold
        scale = np.std(values) if np.std(values) > 1e-6 else 1.0
        z = (values - self.threshold) / scale
        return 1.0 / (1.0 + np.exp(-z))


class ClimatologicalBaseline:
    """Climatological baseline predicting constant historical training prevalence."""

    def __init__(self) -> None:
        self.prevalence: Optional[float] = None

    def fit(
        self,
        y_train: pd.Series,
        fit_indices: Optional[Sequence[int]] = None,
        val_indices: Optional[Sequence[int]] = None,
        test_indices: Optional[Sequence[int]] = None,
    ) -> ClimatologicalBaseline:
        """Fit historical prevalence on training labels only."""
        if fit_indices is not None:
            if test_indices is not None:
                assert_no_test_in_fit(fit_indices, test_indices)
            if val_indices is not None:
                val_overlap = set(fit_indices).intersection(set(val_indices))
                if val_overlap:
                    raise TestLeakageError(
                        f"Validation leakage in climatological fitting: {len(val_overlap)} overlapping indices."
                    )
            y_fit = y_train.iloc[fit_indices]
        else:
            y_fit = y_train

        valid_y = y_fit.dropna().astype(int)
        self.prevalence = float(valid_y.mean()) if len(valid_y) > 0 else 0.0
        return self

    def predict_proba(self, n_samples: int) -> np.ndarray:
        """Return constant probability array."""
        if self.prevalence is None:
            raise RuntimeError("ClimatologicalBaseline must be fitted before predict_proba.")
        return np.full(n_samples, fill_value=self.prevalence, dtype=float)

    def predict(self, n_samples: int, threshold: float = 0.5) -> np.ndarray:
        """Return binary prediction based on decision threshold."""
        p = self.predict_proba(n_samples)
        return (p >= threshold).astype(int)


class PersistenceBaseline:
    """Persistence baseline: current observed window state persists into horizon."""

    def __init__(self, state_column: Optional[str] = None) -> None:
        self.state_column = state_column

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict future state using causal window feature at t0."""
        if self.state_column and self.state_column in X.columns:
            return (X[self.state_column].values > 0.0).astype(int)
        # Default heuristic: if any ratio or flux exceeds standard nominal baseline
        cols = [c for c in X.columns if "ratio" in c.lower() or "mean" in c.lower()]
        target_col = cols[0] if cols else X.columns[0]
        vals = X[target_col].values
        # Above median represents active state
        return (vals > np.nanmedian(vals)).astype(int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return binary pseudo-probabilities for persistence."""
        preds = self.predict(X)
        return preds.astype(float)
