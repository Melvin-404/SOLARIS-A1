"""Run explainability, event-level evaluation, and paired bootstrap comparisons on locked models.

Generates reproducible numerical tables and figures for the validation audit.
Strictly read-only with respect to locked models and datasets.
Writes outputs strictly to results/evaluation/.
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from solar_flare.evaluation.event_metrics import (
    PredictedInterval,
    compute_event_metrics,
    merge_positive_windows,
)
from solar_flare.evaluation.false_alarms import (
    compute_false_alarm_analysis,
)
from solar_flare.evaluation.uncertainty import (
    compute_paired_bootstrap_comparison,
    create_temporal_clusters,
)
from solar_flare.evaluation.explainability import (
    check_shap_available,
    generate_explainability_artifacts,
)


def run_explainability():
    print("--- 1. Generating Explainability Artifacts ---")
    base_dir = Path("results/evaluation/explainability")
    base_dir.mkdir(parents=True, exist_ok=True)

    experiments = {
        "pilot": {
            "exp_dir": Path("results/experiments/exp_PROTO_STAGE10_PILOT_001_20261023_141429"),
            "models": ["random_forest", "xgboost"],
        },
        "july2024": {
            "exp_dir": Path("results/experiments/exp_PROTO_STAGE10_EXPANDED_002_20261023_162431"),
            "models": ["random_forest", "xgboost"],
        },
    }

    for exp_key, exp_info in experiments.items():
        exp_dir = exp_info["exp_dir"]
        target_dir = base_dir / exp_key
        target_dir.mkdir(parents=True, exist_ok=True)

        preproc_path = exp_dir / "preprocessor.joblib"
        preprocessor = joblib.load(preproc_path)
        feature_names = list(preprocessor.feature_names_in_)

        test_csv = exp_dir / "sealed" / "test_set.csv"
        test_df = pd.read_csv(test_csv)
        feat_cols = [c for c in test_df.columns if c.startswith("feat_")]
        clean_feat_names = [c[len("feat_"):] for c in feat_cols]
        X_test_raw = test_df[feat_cols].copy()
        X_test_raw.columns = clean_feat_names
        X_test = X_test_raw[feature_names]
        y_test = test_df["label"].values

        X_trans = preprocessor.transform(X_test)

        X_trans_arr = np.asarray(X_trans)
        for m_name in exp_info["models"]:
            m_path = exp_dir / "models" / f"{m_name}.joblib"
            if not m_path.is_file():
                continue
            model = joblib.load(m_path)
            print(f"  Generating explainability for {exp_key} - {m_name}...")
            # For July 2024 (15k rows), subsample 2000 for permutation importance to be fast & reproducible
            if len(X_trans_arr) > 2000:
                rng = np.random.default_rng(42)
                idx = rng.choice(len(X_trans_arr), size=2000, replace=False)
                X_sub = X_trans_arr[idx]
                y_sub = y_test[idx]
            else:
                X_sub = X_trans_arr
                y_sub = y_test

            res = generate_explainability_artifacts(
                model=model,
                X=X_sub,
                y=y_sub,
                feature_names=feature_names,
                model_name=m_name,
                output_dir=target_dir,
                scoring="f1",
                n_repeats=5,
                random_state=42,
            )
            print(f"    Saved: {res['csv_path']}, Top features: {res['top_features'][:3]}")


def run_event_level_eval():
    print("--- 2. Generating Event-Level & False Alarm Artifacts ---")
    out_dir = Path("results/evaluation/event_level")
    out_dir.mkdir(parents=True, exist_ok=True)

    ref_events_file = Path("data/manifests/event_records_approved.csv")
    ref_events = pd.read_csv(ref_events_file)

    experiments = {
        "pilot": Path("results/experiments/exp_PROTO_STAGE10_PILOT_001_20261023_141429"),
        "july2024": Path("results/experiments/exp_PROTO_STAGE10_EXPANDED_002_20261023_162431"),
    }

    results = {}
    for exp_key, exp_dir in experiments.items():
        preds_file = exp_dir / "evaluation" / "test_predictions.csv"
        test_file = exp_dir / "sealed" / "test_set.csv"
        if not preds_file.is_file() or not test_file.is_file():
            continue

        preds_df = pd.read_csv(preds_file)
        test_df = pd.read_csv(test_file)

        w_start = test_df["window_start"].values
        w_end = test_df["window_end"].values
        w_times = list(zip(w_start, w_end))
        covered_sec = float(w_end.max() - w_start.min())

        exp_results = {}
        for m_name in ["xgboost", "random_forest", "logistic_regression"]:
            m_preds_df = preds_df[preds_df["model_name"] == m_name]
            if len(m_preds_df) == 0:
                continue

            preds = m_preds_df["pred"].values
            scores = m_preds_df["score"].values

            pos_times = [w_times[i] for i, p in enumerate(preds) if p == 1]
            pos_scores = [scores[i] for i, p in enumerate(preds) if p == 1]

            merged_intervals = merge_positive_windows(pos_times, pos_scores, merge_gap_seconds=60.0)

            # Filter reference events to those falling within the test period window [min - 3600, max + 3600]
            start_min = w_start.min() - 3600.0
            end_max = w_end.max() + 3600.0
            scoped_ref = ref_events[(ref_events["onset_time"] >= start_min) & (ref_events["end_time"] <= end_max)]
            if len(scoped_ref) == 0:
                # If no reference event within exact range, use all reference events for evaluation
                scoped_ref = ref_events

            event_rep = compute_event_metrics(
                reference_events=scoped_ref,
                predicted_intervals=merged_intervals,
                task="detection",
                merge_gap_seconds=60.0,
                tolerance_seconds=30.0,
            )

            fa_rep = compute_false_alarm_analysis(
                predicted_intervals=merged_intervals,
                reference_events=scoped_ref,
                covered_duration_seconds=covered_sec,
                task="detection",
                tolerance_seconds=30.0,
            )

            exp_results[m_name] = {
                "event_metrics": event_rep.to_dict(),
                "false_alarms": fa_rep.to_dict(),
            }
            print(f"  {exp_key} - {m_name}: Reference={event_rep.n_reference_events}, Detected={event_rep.n_detected_events} ({event_rep.event_detection_rate*100:.1f}%), FA Intervals={event_rep.n_false_alarm_intervals}, FA/hr={fa_rep.false_alarm_rate_per_hour:.2f}, FA/day={fa_rep.false_alarm_episodes_per_day:.2f}")

        results[exp_key] = exp_results
        out_file = out_dir / f"{exp_key}_event_level_evaluation.json"
        out_file.write_text(json.dumps(exp_results, indent=2), encoding="utf-8")


def run_paired_comparisons():
    print("--- 3. Generating Paired Bootstrap Comparisons ---")
    out_dir = Path("results/evaluation/paired_comparisons")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Use July 2024 test predictions (N=15,872)
    exp_dir = Path("results/experiments/exp_PROTO_STAGE10_EXPANDED_002_20261023_162431")
    preds_file = exp_dir / "evaluation" / "test_predictions.csv"
    test_file = exp_dir / "sealed" / "test_set.csv"

    preds_df = pd.read_csv(preds_file)
    test_df = pd.read_csv(test_file)

    # Pivot predictions by model
    xgb_df = preds_df[preds_df["model_name"] == "xgboost"].reset_index(drop=True)
    rf_df = preds_df[preds_df["model_name"] == "random_forest"].reset_index(drop=True)
    lr_df = preds_df[preds_df["model_name"] == "logistic_regression"].reset_index(drop=True)

    combined_df = pd.DataFrame({
        "label": xgb_df["label"].values,
        "window_start": test_df["window_start"].values,
        "pred_xgb": xgb_df["pred"].values,
        "score_xgb": xgb_df["score"].values,
        "pred_rf": rf_df["pred"].values,
        "score_rf": rf_df["score"].values,
        "pred_lr": lr_df["pred"].values,
        "score_lr": lr_df["score"].values,
        "segment_id": test_df["segment_id"].values,
    })

    # Segment ID has 4 segments; create 30-min temporal clusters for valid block resampling (>= 5 blocks)
    combined_df["cluster_id"] = create_temporal_clusters(combined_df, time_col="window_start", cluster_duration_seconds=1800.0)
    n_clusters = combined_df["cluster_id"].nunique()
    print(f"  Created {n_clusters} 30-min temporal clusters across July 2024 test set.")

    comparisons = [
        ("xgboost", "random_forest", "pred_xgb", "pred_rf", "score_xgb", "score_rf"),
        ("xgboost", "logistic_regression", "pred_xgb", "pred_lr", "score_xgb", "score_lr"),
        ("random_forest", "logistic_regression", "pred_rf", "pred_lr", "score_rf", "score_lr"),
    ]

    comp_results = {}
    for m_a, m_b, p_a, p_b, s_a, s_b in comparisons:
        rep = compute_paired_bootstrap_comparison(
            data=combined_df,
            model_a_pred_col=p_a,
            model_b_pred_col=p_b,
            model_a_score_col=s_a,
            model_b_score_col=s_b,
            y_true_col="label",
            block_col="cluster_id",
            model_a_name=m_a,
            model_b_name=m_b,
            min_independent_blocks=5,
            n_resamples=500,
            ci_level=0.95,
            random_state=42,
        )
        comp_results[f"{m_a}_vs_{m_b}"] = rep.to_dict()
        diff_f1 = rep.differences.get("f1")
        diff_prauc = rep.differences.get("pr_auc")
        print(f"  {m_a} vs {m_b}:")
        if diff_f1:
            print(f"    Delta F1: {diff_f1.diff_point_estimate:+.4f} (95% CI: [{diff_f1.ci_lower:+.4f}, {diff_f1.ci_upper:+.4f}], p={diff_f1.p_value:.4f}, Sig={diff_f1.is_significant})")
        if diff_prauc:
            print(f"    Delta PR-AUC: {diff_prauc.diff_point_estimate:+.4f} (95% CI: [{diff_prauc.ci_lower:+.4f}, {diff_prauc.ci_upper:+.4f}], p={diff_prauc.p_value:.4f}, Sig={diff_prauc.is_significant})")

    out_file = out_dir / "july2024_paired_comparisons.json"
    out_file.write_text(json.dumps(comp_results, indent=2), encoding="utf-8")
    print(f"  Saved paired comparisons to {out_file}")


if __name__ == "__main__":
    run_explainability()
    run_event_level_eval()
    run_paired_comparisons()
    print("ALL AUDIT ARTIFACTS COMPLETED SUCCESSFULLY.")
