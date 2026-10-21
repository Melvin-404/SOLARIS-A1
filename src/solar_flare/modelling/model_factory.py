"""Model Factory for SOLARIS-A1 Estimators (Stage 10).

Instantiates unfitted estimators for:
1. Logistic Regression (scikit-learn)
2. Random Forest (scikit-learn)
3. XGBoost (xgboost)

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Returns strictly UNFITTED estimators. Calling check_is_fitted on output must raise NotFittedError.
2. XGBoost is imported dynamically inside the builder function. If xgboost is not installed,
   it returns an estimator marked UNAVAILABLE rather than crashing the pipeline.
3. Random seeds are explicitly passed and pinned for full reproducibility.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple, Union
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

logger = logging.getLogger("solaris_a1.modelling")


class UnavailableModel:
    """Placeholder representing an estimator library that could not be imported."""
    def __init__(self, name: str, reason: str) -> None:
        self.name = name
        self.reason = reason
        self.is_available = False

    def fit(self, *args, **kwargs):
        raise RuntimeError(f"Cannot fit '{self.name}': {self.reason}")

    def predict(self, *args, **kwargs):
        raise RuntimeError(f"Cannot predict with '{self.name}': {self.reason}")


def build_model(
    name: str,
    params: Optional[Dict[str, Any]] = None,
    random_state: int = 42,
) -> Any:
    """Build an unfitted estimator instance configured with approved hyperparameters.
    
    Parameters
    ----------
    name : str
        Model identifier: 'logistic_regression', 'random_forest', or 'xgboost'.
    params : Optional[dict]
        Hyperparameter dictionary.
    random_state : int
        Deterministic random seed.
        
    Returns
    -------
    BaseEstimator or UnavailableModel
        Unfitted estimator.
        
    Raises
    -------
    ValueError
        If model name is not recognized.
    """
    clean_name = name.strip().lower()
    p = dict(params) if params else {}

    if clean_name in {"logistic_regression", "lr"}:
        default_lr = {
            "C": 1.0,
            "solver": "lbfgs",
            "max_iter": 1000,
            "random_state": random_state,
        }
        default_lr.update(p)
        return LogisticRegression(**default_lr)

    elif clean_name in {"random_forest", "rf"}:
        default_rf = {
            "n_estimators": 100,
            "random_state": random_state,
            "n_jobs": 1,
        }
        default_rf.update(p)
        return RandomForestClassifier(**default_rf)

    elif clean_name in {"xgboost", "xgb"}:
        try:
            import xgboost as xgb
        except ImportError as exc:
            logger.warning("XGBoost is not installed or unavailable: %s", exc)
            return UnavailableModel(name="xgboost", reason=str(exc))

        default_xgb = {
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 3,
            "tree_method": "hist",
            "random_state": random_state,
            "n_jobs": 1,
            "eval_metric": "logloss",
        }
        default_xgb.update(p)
        return xgb.XGBClassifier(**default_xgb)

    else:
        raise ValueError(
            f"Unknown model name '{name}'. Approved models are: "
            "['logistic_regression', 'random_forest', 'xgboost']."
        )
