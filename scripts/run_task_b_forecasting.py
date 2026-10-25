"""SOLARIS-A1 Task B: Pre-Flare Activity Analysis & Forecasting Experiment.

Executes:
1. Physical precursor feature analysis comparing pre-flare windows [t_onset - 1800s, t_onset]
   against matched quiescent background.
2. Protocol-guarded pre-flare forecasting experiment predicting flare onsets in [t0, t0 + 1800s]
   with strict exclusion of ongoing flares, evaluated on held-out test partition.
"""

import os
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
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
EVENTS_CSV = REPO_ROOT / "data" / "manifests" / "event_records_approved_expanded_2024_2026.csv"
EXPERIMENT_ID = "exp_PROTO_STAGE16_EXPANDED_2024_2026"
FORECAST_DIR = REPO_ROOT / "results" / "experiments" / EXPERIMENT_ID / "forecasting"

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
    
    far = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    return {
        "n_samples": int(len(y_true)),
        "n_positives": int(tp + fn),
        "n_negatives": int(tn + fp),
        "prevalence": round(float(np.mean(y_true)), 4),
        "threshold": float(threshold),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "brier_score": round(brier, 4),
        "false_alarm_rate": round(far, 4),
        "confusion_matrix": {"tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)}
    }

def main():
    print("=" * 70)
    print("SOLARIS-A1 TASK B: PRE-FLARE FORECASTING & PRECURSOR ANALYSIS")
    print("=" * 70)

    FORECAST_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load dataset & approved events
    print("Loading expanded dataset tables and approved events...")
    X_df = pd.read_csv(DATASET_DIR / "X_features.csv")
    y_df = pd.read_csv(DATASET_DIR / "y_labels.csv")
    m_df = pd.read_csv(DATASET_DIR / "metadata.csv")
    events_df = pd.read_csv(EVENTS_CSV)

    onsets = events_df["onset_time"].values
    ends = events_df["end_time"].values

    # PART 1: PHYSICAL PRECURSOR STATISTICAL ANALYSIS
    print("\n--- Part 1: Physical Pre-Flare Precursor Analysis ---")
    # Identify pre-flare windows: outside flare, but within [onset - 1800s, onset]
    w_ends = m_df["window_end"].values
    is_flare = (y_df["label"] == 1).values
    
    is_preflare = np.zeros(len(m_df), dtype=bool)
    for onset in onsets:
        # Pre-flare window ends within 30 min before onset
        mask = (w_ends >= onset - 1800.0) & (w_ends <= onset) & (~is_flare)
        is_preflare |= mask

    is_quiet = (y_df["label"] == 0).values & (~is_preflare)

    print(f"Pre-flare windows identified: {is_preflare.sum():,}")
    print(f"Quiescent background windows: {is_quiet.sum():,}")

    precursor_stats = {}
    for feat in ["mean", "max", "std", "temporal_slope", "robust_variability", "peak_to_baseline_ratio"]:
        vals_pre = X_df.loc[is_preflare, feat].dropna().values
        vals_quiet = X_df.loc[is_quiet, feat].dropna().values
        
        if len(vals_pre) > 0 and len(vals_quiet) > 0:
            m_pre, s_pre = float(np.mean(vals_pre)), float(np.std(vals_pre))
            m_qui, s_qui = float(np.mean(vals_quiet)), float(np.std(vals_quiet))
            # Cohen's d effect size
            pooled_s = np.sqrt((s_pre**2 + s_qui**2) / 2.0)
            d = (m_pre - m_qui) / pooled_s if pooled_s > 0 else 0.0
            ks_stat, ks_pval = stats.ks_2samp(vals_pre[:5000], vals_quiet[:5000])
            
            precursor_stats[feat] = {
                "preflare_mean": round(m_pre, 3),
                "quiet_mean": round(m_qui, 3),
                "cohens_d": round(float(d), 3),
                "ks_stat": round(float(ks_stat), 3),
                "ks_pval": float(ks_pval)
            }
            print(f"  Feature '{feat:22s}' | Pre-flare Mean: {m_pre:7.2f} | Quiet Mean: {m_qui:7.2f} | Cohen's d: {d:+.3f} | KS p: {ks_pval:.2e}")

    with open(FORECAST_DIR / "task_b_precursor_analysis.json", "w", encoding="utf-8") as f:
        json.dump(precursor_stats, f, indent=2)

    # PART 2: PROTOCOL-GUARDED PRE-FLARE FORECASTING EXPERIMENT (30 MIN HORIZON)
    print("\n--- Part 2: Task B Pre-Flare Forecasting Experiment ---")
    print("Constructing 30-min horizon forecasting labels...")
    
    # Task B label logic:
    # 1. Exclude if ongoing flare at t0 (window_end)
    # 2. Label = 1 if ANY flare onset occurs in (t0, t0 + 1800s]
    # 3. Label = 0 if no flare onset and quiet background
    H = 1800.0  # 30 minutes
    
    task_b_labels = np.full(len(m_df), np.nan)
    task_b_reasons = []

    # Check ongoing flares
    ongoing_flare_mask = np.zeros(len(m_df), dtype=bool)
    for s, e in zip(onsets, ends):
        ongoing_flare_mask |= ((w_ends >= s) & (w_ends <= e))

    for idx in range(len(m_df)):
        t0 = w_ends[idx]
        if ongoing_flare_mask[idx]:
            task_b_reasons.append("ONGOING_FLARE_AT_T0_EXCLUDED")
            continue
        if m_df.loc[idx, "coverage_fraction"] < 0.80:
            task_b_reasons.append("LOW_COVERAGE_EXCLUDED")
            continue
            
        # Check onset in horizon (t0, t0 + H]
        onset_in_horizon = np.any((onsets > t0) & (onsets <= t0 + H))
        if onset_in_horizon:
            task_b_labels[idx] = 1
            task_b_reasons.append("ONSET_IN_HORIZON")
        elif y_df.loc[idx, "label"] == 0:
            task_b_labels[idx] = 0
            task_b_reasons.append("NO_ONSET_QUIET_HORIZON")
        else:
            task_b_reasons.append("AMBIGUOUS_BACKGROUND_EXCLUDED")

    b_usable = ~np.isnan(task_b_labels)
    X_b_usable = X_df[b_usable].reset_index(drop=True)
    y_b_usable = task_b_labels[b_usable].astype(int)
    m_b_usable = m_df[b_usable].reset_index(drop=True)

    print(f"Task B Usable forecasting instances: {len(y_b_usable):,} (Positive onsets: {y_b_usable.sum():,}, Prevalence: {np.mean(y_b_usable)*100:.2f}%)")

    # Chronological partition for Task B
    w_starts_b = m_b_usable["window_start"].values
    tr_mask = (w_starts_b < T_TRAIN_CUTOFF)
    va_mask = (w_starts_b >= T_VAL_START) & (w_starts_b < T_VAL_END)
    te_mask = (w_starts_b >= T_TEST_START)

    print(f"Task B Partitions -> Train: {tr_mask.sum():,} | Val: {va_mask.sum():,} | Test: {te_mask.sum():,}")

    # Impute & Scale strictly on Train
    imputer = SimpleImputer(strategy="median")
    scaler = RobustScaler()

    X_tr = scaler.fit_transform(imputer.fit_transform(X_b_usable[tr_mask].values))
    y_tr = y_b_usable[tr_mask]
    
    X_va = scaler.transform(imputer.transform(X_b_usable[va_mask].values))
    y_va = y_b_usable[va_mask]

    X_te = scaler.transform(imputer.transform(X_b_usable[te_mask].values))
    y_te = y_b_usable[te_mask]

    # Models
    models_b = {
        "baseline_climatological": None,
        "logistic_regression": LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
        "random_forest": RandomForestClassifier(n_estimators=100, max_depth=8, class_weight="balanced", random_state=42, n_jobs=-1),
        "xgboost": XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, eval_metric="logloss", random_state=42, n_jobs=-1),
    }

    test_forecast_results = {}
    p_train_clim = float(np.mean(y_tr))

    for name, clf in models_b.items():
        if name == "baseline_climatological":
            test_probs = np.full_like(y_te, p_train_clim, dtype=float)
        else:
            clf.fit(X_tr, y_tr)
            test_probs = clf.predict_proba(X_te)[:, 1]
            
        test_forecast_results[name] = compute_metrics(y_te, test_probs, threshold=0.5)
        print(f"  {name:25s} | Prec: {test_forecast_results[name]['precision']:.4f} | Rec: {test_forecast_results[name]['recall']:.4f} | F1: {test_forecast_results[name]['f1']:.4f} | PR-AUC: {test_forecast_results[name]['pr_auc']:.4f} | ROC-AUC: {test_forecast_results[name]['roc_auc']:.4f}")

    with open(FORECAST_DIR / "task_b_forecasting_metrics.json", "w", encoding="utf-8") as f:
        json.dump(test_forecast_results, f, indent=2)

    print("\nSaved Task B forecasting results to", FORECAST_DIR)

if __name__ == "__main__":
    main()
