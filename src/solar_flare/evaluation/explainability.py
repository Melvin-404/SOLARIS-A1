"""Model explainability and feature importance analysis for SOLARIS-A1 (Phase 4).

Provides reproducible calculation and artifact export for:
1. Impurity-based feature importance for tree models (Random Forest, XGBoost).
2. Permutation feature importance (model-agnostic, using held-out test data).
3. SHAP availability verification and explanation generation.
4. Export of structured CSV, JSON, and publication-quality plots.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

logger = logging.getLogger("solaris_a1.explainability")


def compute_tree_feature_importance(
    model: Any,
    feature_names: Sequence[str],
) -> pd.DataFrame:
    """Extract impurity-based (MDI) feature importances from fitted tree model.

    Parameters
    ----------
    model : fitted estimator
        Tree-based model exposing ``feature_importances_`` (e.g., RandomForestClassifier, XGBClassifier).
    feature_names : sequence of str
        Names corresponding to the input features.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['feature', 'importance'] sorted descending.

    Raises
    ------
    AttributeError
        If the model does not possess a ``feature_importances_`` attribute.
    """
    if not hasattr(model, "feature_importances_"):
        raise AttributeError(
            f"Model {type(model).__name__} does not expose 'feature_importances_'. "
            "Impurity-based importance is only defined for tree-based models."
        )

    importances = np.asarray(model.feature_importances_, dtype=float)
    if len(importances) != len(feature_names):
        raise ValueError(
            f"Length mismatch: model has {len(importances)} importances, "
            f"but {len(feature_names)} feature names were provided."
        )

    df = pd.DataFrame({
        "feature": list(feature_names),
        "importance": importances,
    }).sort_values(by="importance", ascending=False).reset_index(drop=True)

    return df


def compute_permutation_feature_importance(
    model: Any,
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series, Sequence],
    feature_names: Sequence[str],
    scoring: str = "f1",
    n_repeats: int = 10,
    random_state: int = 42,
) -> pd.DataFrame:
    """Compute permutation feature importance on held-out test data.

    Parameters
    ----------
    model : fitted estimator
        Fitted model with ``predict`` method.
    X : array-like or DataFrame
        Preprocessed test features matching model inputs.
    y : array-like or Series
        True binary labels.
    feature_names : sequence of str
        Names of the features.
    scoring : str, default="f1"
        Metric to evaluate decrease in performance.
    n_repeats : int, default=10
        Number of times each feature column is permuted.
    random_state : int, default=42
        Deterministic random seed.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['feature', 'importance_mean', 'importance_std'] sorted descending.
    """
    X_arr = np.asarray(X)
    y_arr = np.asarray(y)

    result = permutation_importance(
        estimator=model,
        X=X_arr,
        y=y_arr,
        scoring=scoring,
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=1,
    )

    df = pd.DataFrame({
        "feature": list(feature_names),
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std,
    }).sort_values(by="importance_mean", ascending=False).reset_index(drop=True)

    return df


def check_shap_available() -> Tuple[bool, str]:
    """Audit whether SHAP library is installed in the active environment.

    Returns
    -------
    tuple of (bool, str)
        Boolean flag and detailed diagnostic message.
    """
    try:
        import shap  # noqa: F401
        return True, "SHAP is installed and available."
    except (ImportError, ModuleNotFoundError) as err:
        return False, (
            f"SHAP dependency is not installed in the environment: {err}. "
            "To enable SHAP explanations, install shap via `pip install shap`."
        )


def generate_explainability_artifacts(
    model: Any,
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series, Sequence],
    feature_names: Sequence[str],
    model_name: str,
    output_dir: Union[Path, str],
    scoring: str = "f1",
    n_repeats: int = 10,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Generate and save reproducible feature importance artifacts (CSV, JSON, PNG).

    Parameters
    ----------
    model : fitted estimator
        Model artifact to explain.
    X : array-like or DataFrame
        Test feature matrix.
    y : array-like or Series
        Test target vector.
    feature_names : sequence of str
        Feature column names.
    model_name : str
        Name identifier for the model (e.g. 'random_forest', 'xgboost').
    output_dir : Path or str
        Destination directory for generated artifacts.
    scoring : str, default="f1"
        Scoring metric for permutation importance.
    n_repeats : int, default=10
        Permutation iterations.
    random_state : int, default=42
        Random seed.

    Returns
    -------
    dict
        Summary dictionary with artifact file paths and top features.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    has_tree_imp = hasattr(model, "feature_importances_")
    tree_df: Optional[pd.DataFrame] = None
    if has_tree_imp:
        tree_df = compute_tree_feature_importance(model, feature_names)

    perm_df = compute_permutation_feature_importance(
        model=model,
        X=X,
        y=y,
        feature_names=feature_names,
        scoring=scoring,
        n_repeats=n_repeats,
        random_state=random_state,
    )

    # Merge into comprehensive table
    if tree_df is not None:
        merged_df = perm_df.merge(tree_df, on="feature", how="left")
        merged_df.rename(columns={"importance": "impurity_importance"}, inplace=True)
    else:
        merged_df = perm_df.copy()
        merged_df["impurity_importance"] = np.nan

    csv_file = out_path / f"{model_name}_feature_importance.csv"
    merged_df.to_csv(csv_file, index=False)

    shap_ok, shap_msg = check_shap_available()

    json_file = out_path / f"{model_name}_feature_importance.json"
    meta = {
        "model_name": model_name,
        "model_class": model.__class__.__name__,
        "n_features": len(feature_names),
        "features": list(feature_names),
        "has_impurity_importance": has_tree_imp,
        "permutation_scoring": scoring,
        "permutation_repeats": n_repeats,
        "random_state": random_state,
        "shap_available": shap_ok,
        "shap_status": shap_msg,
        "top_features_by_permutation": merged_df["feature"].head(10).tolist(),
    }
    json_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Generate visual plot
    png_file = out_path / f"{model_name}_feature_importance.png"
    try:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt

        top_k = min(15, len(merged_df))
        plot_df = merged_df.head(top_k).iloc[::-1]  # reverse for horizontal bar chart

        fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
        y_pos = np.arange(len(plot_df))

        ax.barh(
            y_pos,
            plot_df["importance_mean"],
            xerr=plot_df["importance_std"],
            color="#2563EB",
            alpha=0.85,
            edgecolor="#1D4ED8",
            capsize=3,
        )
        ax.set_yticks(y_pos)
        ax.set_yticklabels(plot_df["feature"])
        ax.set_xlabel(f"Permutation Importance (Mean Decrease in {scoring.upper()})")
        ax.set_title(f"Feature Importance ({model_name.upper()}) — Permutation Impact on Test Set")
        ax.grid(axis="x", linestyle="--", alpha=0.5)

        plt.tight_layout()
        plt.savefig(png_file, dpi=150)
        plt.close(fig)
    except Exception as exc:
        logger.warning("Could not generate feature importance plot: %s", exc)

    return {
        "csv_path": str(csv_file),
        "json_path": str(json_file),
        "png_path": str(png_file) if png_file.is_file() else None,
        "top_features": merged_df["feature"].head(5).tolist(),
        "shap_available": shap_ok,
    }
