"""Training-Only Preprocessing Engine for SOLARIS-A1 (Stage 10).

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Preprocessors (scalers, feature selectors) are fitted STRICTLY on the training partition.
2. Passing validation or test indices into the fit method immediately raises TestLeakageError.
3. Imputation is NONE by default: any NaN in features raises MissingFeatureError with per-column counts.
   Silent imputation is strictly forbidden.
4. Records fit row count and index hash for auditability.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler

from solar_flare.modelling.guards import assert_no_test_in_fit, MissingFeatureError, TestLeakageError


class TrainingOnlyPreprocessor:
    """Preprocessor that fits exclusively on training indices, preventing feature leakage."""

    def __init__(
        self,
        scaler: str = "StandardScaler",
        imputer: str = "NONE",
        feature_selection: str = "NONE",
    ) -> None:
        self.scaler_name = scaler
        self.imputer_name = imputer
        self.feature_selection_name = feature_selection

        self.scaler = None
        self.is_fitted = False
        self.feature_names_in_: List[str] = []
        self.fit_row_count: int = 0
        self.fit_indices_hash: str = ""

    def fit(
        self,
        X: pd.DataFrame,
        y: Optional[pd.Series] = None,
        fit_indices: Optional[Sequence[int]] = None,
        val_indices: Optional[Sequence[int]] = None,
        test_indices: Optional[Sequence[int]] = None,
    ) -> TrainingOnlyPreprocessor:
        """Fit preprocessor parameters strictly on designated training samples.
        
        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix.
        y : Optional[pd.Series]
            Target labels.
        fit_indices : Optional[Sequence[int]]
            Indices of training samples. If None, assumes X is already sliced to training only.
        val_indices : Optional[Sequence[int]]
            Indices of validation partition for leakage verification.
        test_indices : Optional[Sequence[int]]
            Indices of test partition for leakage verification.
            
        Raises
        -------
        TestLeakageError
            If fit_indices overlap validation or test indices.
        MissingFeatureError
            If NaN values exist in training features under imputer='NONE'.
        """
        # 1. Verify index isolation
        if fit_indices is not None:
            if test_indices is not None:
                assert_no_test_in_fit(fit_indices, test_indices)
            if val_indices is not None:
                # Same leakage guard applies to validation indices
                overlap_val = set(fit_indices).intersection(set(val_indices))
                if overlap_val:
                    raise TestLeakageError(
                        f"VALIDATION LEAKAGE: {len(overlap_val)} validation sample(s) included in fit_indices!"
                    )
            X_fit = X.iloc[fit_indices]
            y_fit = y.iloc[fit_indices] if y is not None else None
            idx_bytes = np.asarray(fit_indices, dtype=np.int64).tobytes()
            self.fit_indices_hash = hashlib.sha256(idx_bytes).hexdigest()[:16]
            self.fit_row_count = len(fit_indices)
        else:
            X_fit = X
            y_fit = y
            self.fit_row_count = len(X)
            self.fit_indices_hash = "unindexed_slice"

        self.feature_names_in_ = list(X.columns)

        # 2. Strict NaN check
        if self.imputer_name.upper() == "NONE":
            nan_counts = X_fit.isna().sum()
            bad_cols = nan_counts[nan_counts > 0].to_dict()
            if bad_cols:
                raise MissingFeatureError(
                    f"NaN values encountered in training features with imputer='NONE': {bad_cols}. "
                    "Silent imputation is prohibited."
                )

        # 3. Fit Scaler
        s_choice = self.scaler_name.upper()
        if s_choice == "STANDARDSCALER":
            self.scaler = StandardScaler()
            self.scaler.fit(X_fit)
        elif s_choice == "ROBUSTSCALER":
            self.scaler = RobustScaler()
            self.scaler.fit(X_fit)
        elif s_choice == "NONE":
            self.scaler = None
        else:
            raise ValueError(f"Unsupported scaler '{self.scaler_name}'. Must be StandardScaler, RobustScaler, or NONE.")

        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Apply learned transformations to arbitrary feature partitions."""
        if not self.is_fitted:
            raise RuntimeError("TrainingOnlyPreprocessor must be fitted before transform.")

        # Check for NaN in input under imputer=NONE
        if self.imputer_name.upper() == "NONE":
            nan_counts = X.isna().sum()
            bad_cols = nan_counts[nan_counts > 0].to_dict()
            if bad_cols:
                raise MissingFeatureError(
                    f"NaN values encountered during transform with imputer='NONE': {bad_cols}."
                )

        if self.scaler is not None:
            arr_scaled = self.scaler.transform(X)
            return pd.DataFrame(arr_scaled, columns=self.feature_names_in_, index=X.index)
        return X.copy()
