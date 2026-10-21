"""Model Training and Validation-Only Selection Engine for SOLARIS-A1 (Stage 10).

CRITICAL SCIENTIFIC CONSTRAINTS:
1. Selection and tuning use VALIDATION DATA ONLY.
2. The function signature of run_selection DOES NOT ACCEPT test data.
3. Test evaluation is strictly PROHIBITED in Stage 10 (deferred to Stage 11).
4. Every trial (parameters, validation metric, seed, duration) is recorded in trials.csv.
5. All validation performance numbers must be explicitly labelled 'VALIDATION ONLY'.
"""

from __future__ import annotations

import itertools
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score

from solar_flare.modelling.model_factory import build_model, UnavailableModel

logger = logging.getLogger("solaris_a1.modelling")


def _evaluate_metric(
    model: Any,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    metric_name: str = "PR_AUC",
) -> float:
    """Evaluate candidate model on validation data using the approved metric."""
    y_true = np.asarray(y_val, dtype=np.int32)

    # Need probabilities for ranking metrics
    has_positives = (y_true == 1).sum() > 0
    has_negatives = (y_true == 0).sum() > 0

    if not (has_positives and has_negatives):
        # Single-class validation edge case: fallback to accuracy
        preds = model.predict(X_val)
        return float(np.mean(preds == y_true))

    m_name = metric_name.upper()
    try:
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X_val)[:, 1]
        else:
            probs = model.decision_function(X_val)

        if m_name in {"PR_AUC", "AVERAGE_PRECISION", "PR-AUC"}:
            return float(average_precision_score(y_true, probs))
        elif m_name in {"ROC_AUC", "ROC-AUC"}:
            return float(roc_auc_score(y_true, probs))
        elif m_name == "F1":
            preds = model.predict(X_val)
            return float(f1_score(y_true, preds, zero_division=0))
        else:
            preds = model.predict(X_val)
            return float(np.mean(preds == y_true))
    except Exception as exc:
        logger.warning("Metric evaluation fallback due to error: %s", exc)
        preds = model.predict(X_val)
        return float(np.mean(preds == y_true))


def run_selection(
    protocol: Dict[str, Any],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    out_dir: Union[Path, str],
) -> Dict[str, Any]:
    """Execute hyperparameter tuning and model selection on validation data only.
    
    NOTE ON SIGNATURE:
    Accepts X_train, y_train, X_val, y_val.
    Does NOT accept X_test or y_test under any circumstance.
    
    Parameters
    ----------
    protocol : dict
        Approved training protocol dictionary.
    X_train : pd.DataFrame
        Transformed training features.
    y_train : pd.Series
        Training labels.
    X_val : pd.DataFrame
        Transformed validation features.
    y_val : pd.Series
        Validation labels.
    out_dir : Path or str
        Destination directory for selection artifacts.
        
    Returns
    -------
    dict
        Summary of selected models, parameter configurations, and validation scores.
    """
    sel_dir = Path(out_dir) / "selection"
    models_dir = Path(out_dir) / "models"
    sel_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    metric_name = protocol.get("selection_metric", "PR_AUC")
    refit_mode = protocol.get("refit_final", "train_only")
    models_config = protocol.get("models", {})

    all_trials: List[Dict[str, Any]] = []
    selected_summary: Dict[str, Any] = {}
    model_manifest: Dict[str, Any] = {}

    for model_name, m_cfg in models_config.items():
        if not m_cfg.get("enabled", True):
            continue

        param_grid = m_cfg.get("param_grid", {})
        seed = int(m_cfg.get("deterministic_seed", 42))

        # Flatten grid
        keys = list(param_grid.keys())
        grid_combos = list(itertools.product(*[param_grid[k] for k in keys])) if keys else [{}]

        best_score = -float("inf")
        best_params: Dict[str, Any] = {}
        best_estimator: Any = None

        logger.info("Running validation selection for model '%s' (%d trial(s))...", model_name, len(grid_combos))

        for trial_idx, values in enumerate(grid_combos, start=1):
            trial_params = dict(zip(keys, values)) if keys else {}
            t0 = time.time()

            estimator = build_model(model_name, params=trial_params, random_state=seed)
            if isinstance(estimator, UnavailableModel):
                all_trials.append({
                    "model": model_name,
                    "trial_id": trial_idx,
                    "status": "UNAVAILABLE",
                    "reason": estimator.reason,
                    "val_metric_name": metric_name,
                    "val_score_validation_only": np.nan,
                    "duration_seconds": 0.0,
                })
                best_score = np.nan
                best_params = {}
                break

            try:
                estimator.fit(X_train, y_train)
                val_score = _evaluate_metric(estimator, X_val, y_val, metric_name=metric_name)
                duration = time.time() - t0

                all_trials.append({
                    "model": model_name,
                    "trial_id": trial_idx,
                    "status": "SUCCESS",
                    "params": json.dumps(trial_params, default=str),
                    "val_metric_name": metric_name,
                    "val_score_validation_only": round(val_score, 5),
                    "duration_seconds": round(duration, 3),
                    "random_seed": seed,
                })

                if val_score > best_score:
                    best_score = val_score
                    best_params = trial_params
                    best_estimator = estimator

            except Exception as exc:
                duration = time.time() - t0
                all_trials.append({
                    "model": model_name,
                    "trial_id": trial_idx,
                    "status": "FAIL",
                    "reason": str(exc),
                    "params": json.dumps(trial_params, default=str),
                    "val_metric_name": metric_name,
                    "val_score_validation_only": np.nan,
                    "duration_seconds": round(duration, 3),
                })

        # Refit final model
        if best_params is not None and not isinstance(best_estimator, UnavailableModel) and best_score != -float("inf"):
            final_estimator = build_model(model_name, params=best_params, random_state=seed)
            if refit_mode == "train_plus_validation":
                X_refit = pd.concat([X_train, X_val], ignore_index=True)
                y_refit = pd.concat([y_train, y_val], ignore_index=True)
            else:
                X_refit = X_train
                y_refit = y_train

            final_estimator.fit(X_refit, y_refit)

            # Save model artifact
            model_path = models_dir / f"{model_name}.joblib"
            joblib.dump(final_estimator, model_path)

            selected_summary[model_name] = {
                "status": "TRAINED",
                "selection_metric": metric_name,
                "best_validation_score": best_score,
                "best_parameters": best_params,
                "refit_mode": refit_mode,
                "artifact_path": str(model_path.relative_to(out_dir.parent.parent)),
            }
            model_manifest[model_name] = {
                "artifact_file": f"{model_name}.joblib",
                "model_class": final_estimator.__class__.__name__,
                "params": best_params,
            }
        else:
            selected_summary[model_name] = {
                "status": "UNAVAILABLE_OR_FAILED",
                "selection_metric": metric_name,
                "best_validation_score": np.nan,
                "best_parameters": {},
            }

    # Write trials.csv
    trials_df = pd.DataFrame(all_trials)
    trials_df.to_csv(sel_dir / "trials.csv", index=False)

    # Write selected_params.json
    (sel_dir / "selected_params.json").write_text(
        json.dumps(selected_summary, indent=2, default=str), encoding="utf-8"
    )

    # Write model_manifest.json
    (models_dir / "model_manifest.json").write_text(
        json.dumps(model_manifest, indent=2, default=str), encoding="utf-8"
    )

    # Write selection_report.md
    report_lines = [
        f"# MODEL SELECTION REPORT — VALIDATION ONLY",
        f"",
        f"> **GOVERNANCE NOTICE: VALIDATION METRICS ONLY**  ",
        f"> All performance metrics in this document were evaluated exclusively on the **VALIDATION partition**.  ",
        f"> The sealed TEST set was not read, scored, or evaluated in this stage.  ",
        f"",
        f"**Selection Metric:** `{metric_name}`  ",
        f"**Refit Mode:** `{refit_mode}`  ",
        f"",
        f"| Model Name | Status | Validation Score ({metric_name}) | Selected Hyperparameters |",
        f"|------------|:------:|:---------------------------------:|--------------------------|",
    ]
    for m_name, info in selected_summary.items():
        score_str = f"{info['best_validation_score']:.4f}" if np.isfinite(info['best_validation_score']) else "N/A"
        report_lines.append(f"| `{m_name}` | `{info['status']}` | **{score_str}** | `{info['best_parameters']}` |")

    (sel_dir / "selection_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return selected_summary
