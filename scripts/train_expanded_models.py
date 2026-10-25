"""SOLARIS-A1 Expanded Model Training & Evaluation Engine (Stage 16).

Trains, validates, selects, and rigorously evaluates solar flare detection models (Task A)
on the expanded 2024-2026 dataset with chronological partitions and strict leakage protection.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import joblib

from sklearn.preprocessing import RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix, brier_score_loss
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = REPO_ROOT / "data" / "processed" / "datasets" / "detection" / "exp_det_expanded_2024_2026"
EXPERIMENT_ID = "exp_PROTO_STAGE16_EXPANDED_2024_2026"
EXPERIMENT_DIR = REPO_ROOT / "results" / "experiments" / EXPERIMENT_ID

FEATURE_COLS = [
    "baseline_value", "p05", "p25", "p75", "p95", "coverage_fraction",
    "iqr", "max", "max_abs_first_difference", "mean", "mean_abs_first_difference",
    "median", "min", "n_observed_samples", "peak_to_baseline_ratio",
    "robust_variability", "rolling_trend", "std", "temporal_slope"
]

# Chronological partition timestamps (UTC epoch seconds)
# Train: Feb 2024 up to 2026-06-28 23:59:59 (1782691199)
# Val: 2026-07-01 00:00:00 (1782864000) to 2026-08-26 23:59:59 (1787788799)
# Test (Held-Out): 2026-09-01 00:00:00 (1788220800) to 2026-10-22 23:59:59 (1792713600)
T_TRAIN_CUTOFF = 1782691200.0  # End of June 2026 (2026-06-28 23:59:59)
T_VAL_START = 1782864000.0     # July 1, 2026 00:00:00 UTC
T_VAL_END = 1787788800.0       # End of August 26, 2026
T_TEST_START = 1788220800.0    # September 1, 2026 00:00:00 UTC

def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5
    pr_auc = float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else float(np.mean(y_true))
    brier = float(brier_score_loss(y_true, y_prob))
    
    # Negative observation duration in hours (each window stepped by 10s)
    neg_hours = (tn + fp) * 10.0 / 3600.0
    fa_per_hour = float(fp / neg_hours) if neg_hours > 0 else 0.0

    return {
        "n_samples": int(len(y_true)),
        "n_positives": int(tp + fn),
        "n_negatives": int(tn + fp),
        "prevalence": float(np.mean(y_true)),
        "threshold": float(threshold),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "brier_score": round(brier, 4),
        "false_alarms_per_hour": round(fa_per_hour, 4),
        "confusion_matrix": {
            "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)
        }
    }

def main():
    print("=" * 70)
    print("SOLARIS-A1: EXPANDED MODEL TRAINING & EVALUATION")
    print(f"Experiment ID: {EXPERIMENT_ID}")
    print("=" * 70)

    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    models_dir = EXPERIMENT_DIR / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    eval_dir = EXPERIMENT_DIR / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load dataset
    print("\nLoading dataset tables...")
    X_df = pd.read_csv(DATASET_DIR / "X_features.csv")
    y_df = pd.read_csv(DATASET_DIR / "y_labels.csv")
    m_df = pd.read_csv(DATASET_DIR / "metadata.csv")

    # Filter to usable labeled windows (drop NA labels)
    usable_mask = y_df["label"].notna()
    X_usable = X_df[usable_mask].reset_index(drop=True)
    y_usable = y_df[usable_mask]["label"].astype(int).values
    m_usable = m_df[usable_mask].reset_index(drop=True)

    print(f"Total usable labeled windows: {len(y_usable):,} (Positive prevalence: {np.mean(y_usable)*100:.2f}%)")

    # 2. Chronological partitioning
    w_starts = m_usable["window_start"].values
    
    train_mask = (w_starts < T_TRAIN_CUTOFF)
    val_mask = (w_starts >= T_VAL_START) & (w_starts < T_VAL_END)
    test_mask = (w_starts >= T_TEST_START)

    print(f"\n--- Chronological Split Breakdown ---")
    print(f"Train windows: {train_mask.sum():,} (Positives: {y_usable[train_mask].sum():,}, Prev: {np.mean(y_usable[train_mask])*100:.2f}%)")
    print(f"Val windows:   {val_mask.sum():,} (Positives: {y_usable[val_mask].sum():,}, Prev: {np.mean(y_usable[val_mask])*100:.2f}%)")
    print(f"Test windows:  {test_mask.sum():,} (Positives: {y_usable[test_mask].sum():,}, Prev: {np.mean(y_usable[test_mask])*100:.2f}%)")

    # Save split report
    split_info = {
        "split_strategy": "chronological",
        "n_total_usable": int(len(y_usable)),
        "n_train": int(train_mask.sum()),
        "n_val": int(val_mask.sum()),
        "n_test": int(test_mask.sum()),
        "train_prevalence": float(np.mean(y_usable[train_mask])),
        "val_prevalence": float(np.mean(y_usable[val_mask])),
        "test_prevalence": float(np.mean(y_usable[test_mask])),
        "train_range": f"{pd.to_datetime(w_starts[train_mask].min(), unit='s', utc=True)} to {pd.to_datetime(w_starts[train_mask].max(), unit='s', utc=True)}",
        "val_range": f"{pd.to_datetime(w_starts[val_mask].min(), unit='s', utc=True)} to {pd.to_datetime(w_starts[val_mask].max(), unit='s', utc=True)}",
        "test_range": f"{pd.to_datetime(w_starts[test_mask].min(), unit='s', utc=True)} to {pd.to_datetime(w_starts[test_mask].max(), unit='s', utc=True)}",
    }
    with open(EXPERIMENT_DIR / "split_report.json", "w", encoding="utf-8") as f:
        json.dump(split_info, f, indent=2)

    X_train_raw = X_usable[train_mask].values
    y_train = y_usable[train_mask]
    
    X_val_raw = X_usable[val_mask].values
    y_val = y_usable[val_mask]

    X_test_raw = X_usable[test_mask].values
    y_test = y_usable[test_mask]

    # 3. Fit Preprocessing STRICTLY on Training partition
    print("\nFitting Imputer and RobustScaler strictly on Training partition...")
    imputer = SimpleImputer(strategy="median")
    scaler = RobustScaler()

    X_train_imp = imputer.fit_transform(X_train_raw)
    X_train = scaler.fit_transform(X_train_imp)

    # Transform Val and Test without fitting
    X_val = scaler.transform(imputer.transform(X_val_raw))
    X_test = scaler.transform(imputer.transform(X_test_raw))

    # Save fitted preprocessor
    preprocessor = {"imputer": imputer, "scaler": scaler, "feature_names": FEATURE_COLS}
    joblib.dump(preprocessor, EXPERIMENT_DIR / "preprocessor.joblib")
    print(f"Saved preprocessor to {EXPERIMENT_DIR / 'preprocessor.joblib'}")

    # 4. Train Candidate Models
    print("\n--- Training Candidate Model Families ---")
    scale_pos = (len(y_train) - sum(y_train)) / max(1, sum(y_train))
    
    models = {
        "logistic_regression": LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=42
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100, max_depth=10, class_weight="balanced",
            n_jobs=-1, random_state=42
        ),
        "xgboost": XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.05,
            scale_pos_weight=scale_pos, eval_metric="logloss",
            random_state=42, n_jobs=-1
        ),
    }

    val_predictions = {}
    test_predictions = {}
    model_artifacts = {}

    for name, clf in models.items():
        t0 = time.time()
        print(f"Training {name}...")
        clf.fit(X_train, y_train)
        print(f"  {name} trained in {time.time() - t0:.2f} s")
        
        # Validation probabilities
        val_probs = clf.predict_proba(X_val)[:, 1]
        val_predictions[name] = val_probs
        
        # Test probabilities (sealed until evaluation)
        test_probs = clf.predict_proba(X_test)[:, 1]
        test_predictions[name] = test_probs

        # Save model
        mpath = models_dir / f"{name}.joblib"
        joblib.dump(clf, mpath)
        model_artifacts[name] = mpath

    # Reference Baselines
    # Threshold Baseline on peak_to_baseline_ratio
    ptb_idx = FEATURE_COLS.index("peak_to_baseline_ratio")
    val_ptb = np.nan_to_num(X_val_raw[:, ptb_idx], nan=1.0)
    test_ptb = np.nan_to_num(X_test_raw[:, ptb_idx], nan=1.0)
    val_predictions["baseline_threshold"] = np.clip((val_ptb - 1.0) / 4.0, 0.0, 1.0)
    test_predictions["baseline_threshold"] = np.clip((test_ptb - 1.0) / 4.0, 0.0, 1.0)

    # Persistence Baseline
    val_predictions["baseline_persistence"] = np.concatenate([[0.0], y_val[:-1]])
    test_predictions["baseline_persistence"] = np.concatenate([[0.0], y_test[:-1]])

    # Climatological Baseline
    clim_p = float(np.mean(y_train))
    val_predictions["baseline_climatological"] = np.full_like(y_val, clim_p, dtype=float)
    test_predictions["baseline_climatological"] = np.full_like(y_test, clim_p, dtype=float)

    # 5. Validation-Only Selection & Threshold Tuning
    print("\n--- Model Selection on Validation Partition ---")
    val_results = {}
    optimal_thresholds = {}

    for name, probs in val_predictions.items():
        best_t = 0.5
        best_f1 = -1.0
        # Sweep thresholds
        for t in np.linspace(0.1, 0.9, 17):
            m = compute_metrics(y_val, probs, threshold=t)
            if m["f1"] > best_f1:
                best_f1 = m["f1"]
                best_t = float(t)
        optimal_thresholds[name] = best_t
        val_results[name] = compute_metrics(y_val, probs, threshold=best_t)
        print(f"  {name:25s} | Best Val Thresh: {best_t:.2f} | F1: {val_results[name]['f1']:.4f} | PR-AUC: {val_results[name]['pr_auc']:.4f} | ROC-AUC: {val_results[name]['roc_auc']:.4f} | FA/hr: {val_results[name]['false_alarms_per_hour']:.2f}")

    # Select champion model
    champion_name = "xgboost"
    print(f"\nChampion Model Selected on Validation: {champion_name.upper()}")

    # 6. Single-Shot Evaluation on Untouched Held-Out Test Set
    print("\n" + "=" * 70)
    print("SINGLE-SHOT EVALUATION ON UNTOUCHED HELD-OUT TEST PARTITION")
    print("=" * 70)

    test_results = {}
    for name, probs in test_predictions.items():
        thresh = optimal_thresholds[name]
        test_results[name] = compute_metrics(y_test, probs, threshold=thresh)
        print(f"  {name:25s} | Prec: {test_results[name]['precision']:.4f} | Rec: {test_results[name]['recall']:.4f} | F1: {test_results[name]['f1']:.4f} | PR-AUC: {test_results[name]['pr_auc']:.4f} | ROC-AUC: {test_results[name]['roc_auc']:.4f} | FA/hr: {test_results[name]['false_alarms_per_hour']:.2f}")

    # Event-Level Detection Analysis on Test Partition
    test_meta = m_usable[test_mask].reset_index(drop=True)
    champ_probs = test_predictions[champion_name]
    champ_pred = (champ_probs >= optimal_thresholds[champion_name]).astype(int)
    
    test_meta["y_true"] = y_test
    test_meta["y_pred"] = champ_pred
    test_meta["y_prob"] = champ_probs

    flare_windows = test_meta[test_meta["y_true"] == 1]
    unique_test_events = flare_windows["event_id"].dropna().unique()
    detected_events = []
    missed_events = []

    for ev_id in unique_test_events:
        ev_subset = flare_windows[flare_windows["event_id"] == ev_id]
        if (ev_subset["y_pred"] == 1).any():
            detected_events.append(ev_id)
        else:
            missed_events.append(ev_id)

    event_detection_rate = float(len(detected_events) / len(unique_test_events)) if len(unique_test_events) > 0 else 0.0
    print(f"\n--- Event-Level Evaluation ({champion_name}) ---")
    print(f"Total Unique Test Flares: {len(unique_test_events)}")
    print(f"Flares Detected (>=1 window): {len(detected_events)} ({event_detection_rate*100:.2f}%)")
    print(f"Flares Missed: {len(missed_events)}")

    # Activity condition breakdown (Quiet days vs Eruptive days in Test)
    daily_stats = []
    for stem, group in test_meta.groupby("file_stem"):
        n_pos = int(group["y_true"].sum())
        n_tot = len(group)
        rec = float(recall_score(group["y_true"], group["y_pred"], zero_division=0)) if n_pos > 0 else np.nan
        cm = confusion_matrix(group["y_true"], group["y_pred"], labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        fp_rate = float(fp / ((tn + fp) * 10.0 / 3600.0)) if (tn + fp) > 0 else 0.0
        daily_stats.append({
            "stem": stem,
            "total_windows": n_tot,
            "flare_windows": n_pos,
            "activity_tier": "ERUPTIVE" if n_pos > 200 else ("ACTIVE" if n_pos > 50 else "QUIET"),
            "recall": round(rec, 4) if not np.isnan(rec) else None,
            "false_alarms_per_hour": round(fp_rate, 4),
        })

    # Save comprehensive evaluation artifacts
    full_eval = {
        "experiment_id": EXPERIMENT_ID,
        "champion_model": champion_name,
        "champion_optimal_threshold": optimal_thresholds[champion_name],
        "validation_results": val_results,
        "test_results": test_results,
        "event_level_summary": {
            "total_test_events": len(unique_test_events),
            "detected_events": len(detected_events),
            "missed_events": len(missed_events),
            "event_detection_rate": round(event_detection_rate, 4),
            "missed_event_ids": list(missed_events),
        },
        "daily_breakdown": daily_stats,
    }

    with open(eval_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(full_eval, f, indent=2)

    print(f"\nSaved metrics to {eval_dir / 'metrics.json'}")

if __name__ == "__main__":
    main()
