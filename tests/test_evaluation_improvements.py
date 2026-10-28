"""Unit tests for evaluation improvements, explainability, and paired comparisons.

Validates:
1. Event-level metrics with boundary tolerance (Decision D-02).
2. Detection delay reporting (median_detection_delay_sec).
3. False-alarm rate episodes per valid observing day.
4. Paired block bootstrap comparison and statistical significance testing.
5. Temporal clustering utility for block resampling.
6. Tree-based impurity feature importance.
7. Model-agnostic permutation feature importance.
8. SHAP environment detection and reporting.
9. InferencePipeline compatibility with dictionary-format preprocessors.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

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
    compute_permutation_feature_importance,
    compute_tree_feature_importance,
    generate_explainability_artifacts,
)
from solar_flare.inference.pipeline import InferencePipeline


def test_event_boundary_tolerance_matching():
    """Verify that event matching respects tolerance_seconds (Decision D-02)."""
    # Event: [100.0, 200.0]
    ref_events = pd.DataFrame([
        {"event_id": "EVT_01", "start_sec": 100.0, "end_sec": 200.0}
    ])

    # Predicted interval starts at 215.0 and ends at 260.0
    # With tolerance = 0.0s: interval [215, 260] does NOT overlap [100, 200]
    # With tolerance = 20.0s: expanded event window is [80, 220], so [215, 260] overlaps!
    preds = [
        PredictedInterval(start_sec=215.0, end_sec=260.0, duration_sec=45.0, n_windows=1, max_score=0.8)
    ]

    rep_zero = compute_event_metrics(
        reference_events=ref_events,
        predicted_intervals=preds,
        task="detection",
        tolerance_seconds=0.0,
    )
    assert rep_zero.n_detected_events == 0
    assert rep_zero.n_missed_events == 1

    rep_tol = compute_event_metrics(
        reference_events=ref_events,
        predicted_intervals=preds,
        task="detection",
        tolerance_seconds=20.0,
    )
    assert rep_tol.n_detected_events == 1
    assert rep_tol.n_missed_events == 0
    assert rep_tol.tolerance_seconds == 20.0
    assert rep_tol.median_detection_delay_sec == 115.0  # 215 - 100


def test_false_alarm_episodes_per_day():
    """Verify false-alarm rate is normalized to valid observing days."""
    ref_events = pd.DataFrame([
        {"event_id": "EVT_01", "start_sec": 1000.0, "end_sec": 2000.0}
    ])
    # 2 false alarms
    preds = [
        PredictedInterval(start_sec=3000.0, end_sec=3100.0, duration_sec=100.0, n_windows=1, max_score=0.7),
        PredictedInterval(start_sec=5000.0, end_sec=5100.0, duration_sec=100.0, n_windows=1, max_score=0.7),
    ]
    # 12 observation hours = 0.5 observing days
    covered_sec = 12.0 * 3600.0

    fa_rep = compute_false_alarm_analysis(
        predicted_intervals=preds,
        reference_events=ref_events,
        covered_duration_seconds=covered_sec,
    )
    assert fa_rep.n_false_alarms == 2
    assert pytest.approx(fa_rep.false_alarm_rate_per_hour, 1e-5) == 2.0 / 12.0
    # Episodes per observing day = (2 / 12) * 24 = 4.0
    assert pytest.approx(fa_rep.false_alarm_episodes_per_day, 1e-5) == 4.0


def test_paired_bootstrap_comparison():
    """Verify paired comparison computes differences, CIs, and detects significance."""
    rng = np.random.default_rng(42)
    n_per_block = 100
    n_blocks = 8

    dfs = []
    for b in range(n_blocks):
        y_true = rng.choice([0, 1], size=n_per_block, p=[0.8, 0.2])
        # Model A is highly accurate
        p_a = y_true.copy()
        # Model B is random
        p_b = rng.choice([0, 1], size=n_per_block, p=[0.5, 0.5])
        df_b = pd.DataFrame({
            "label": y_true,
            "pred_a": p_a,
            "pred_b": p_b,
            "score_a": p_a.astype(float),
            "score_b": p_b.astype(float),
            "block_id": f"blk_{b}",
        })
        dfs.append(df_b)

    test_data = pd.concat(dfs, ignore_index=True)

    report = compute_paired_bootstrap_comparison(
        data=test_data,
        model_a_pred_col="pred_a",
        model_b_pred_col="pred_b",
        model_a_score_col="score_a",
        model_b_score_col="score_b",
        y_true_col="label",
        block_col="block_id",
        model_a_name="SuperiorModel",
        model_b_name="InferiorModel",
        min_independent_blocks=5,
        n_resamples=100,
        random_state=42,
    )

    assert report.computed is True
    assert "f1" in report.differences
    diff_f1 = report.differences["f1"]
    assert diff_f1.diff_point_estimate > 0.3
    assert diff_f1.ci_lower > 0.0  # Statistically significant advantage for Model A
    assert diff_f1.is_significant is True
    assert diff_f1.p_value < 0.05


def test_temporal_clustering():
    """Verify temporal clustering splits timestamps into discrete duration blocks."""
    times = [0.0, 100.0, 600.0, 1799.0, 1801.0, 2500.0, 3600.0]
    df = pd.DataFrame({"window_start": times})
    clusters = create_temporal_clusters(df, time_col="window_start", cluster_duration_seconds=1800.0)

    assert len(clusters) == 7
    # First 4 timestamps are within [0, 1800) -> cluster_0000
    assert clusters.iloc[0] == "cluster_0000"
    assert clusters.iloc[3] == "cluster_0000"
    # 1801.0 and 2500.0 are in [1800, 3600) -> cluster_0001
    assert clusters.iloc[4] == "cluster_0001"
    # 3600.0 is in [3600, 5400) -> cluster_0002
    assert clusters.iloc[6] == "cluster_0002"


def test_tree_feature_importance():
    """Verify tree impurity importance calculation and validation."""
    X = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.0, 0.0]] * 10)
    y = np.array([1, 0, 1, 0] * 10)
    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    rf.fit(X, y)

    df_imp = compute_tree_feature_importance(rf, ["f1", "f2"])
    assert len(df_imp) == 2
    assert set(df_imp["feature"]) == {"f1", "f2"}
    assert pytest.approx(df_imp["importance"].sum(), 1e-4) == 1.0

    # Non-tree model raises AttributeError
    lr = LogisticRegression()
    lr.fit(X, y)
    with pytest.raises(AttributeError, match="does not expose"):
        compute_tree_feature_importance(lr, ["f1", "f2"])


def test_permutation_feature_importance():
    """Verify permutation feature importance identifies key predictive features."""
    rng = np.random.default_rng(42)
    # Feature 0 is predictive, Feature 1 is pure noise
    X = rng.normal(size=(100, 2))
    y = (X[:, 0] > 0.0).astype(int)

    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    rf.fit(X, y)

    p_df = compute_permutation_feature_importance(rf, X, y, ["predictive", "noise"], scoring="f1", random_state=42)
    assert len(p_df) == 2
    # Predictive feature should have higher importance than noise
    assert p_df.iloc[0]["feature"] == "predictive"
    assert p_df.iloc[0]["importance_mean"] > p_df.iloc[1]["importance_mean"]


def test_shap_availability_check():
    """Verify check_shap_available returns boolean and descriptive string."""
    ok, msg = check_shap_available()
    assert isinstance(ok, bool)
    assert isinstance(msg, str)
    assert len(msg) > 0


def test_inference_pipeline_dict_preprocessor():
    """Verify InferencePipeline loads and predicts using Stage 16 dictionary preprocessor."""
    pipe = InferencePipeline(experiment_id="exp_PROTO_STAGE16_EXPANDED_2024_2026")
    assert pipe.exp_id == "exp_PROTO_STAGE16_EXPANDED_2024_2026"
    assert len(pipe.expected_features) == 19
    sample = {f: 0.5 for f in pipe.expected_features}
    probs = pipe.predict_proba(sample)
    assert len(probs) == 1
    assert 0.0 <= probs[0] <= 1.0
    preds = pipe.predict(sample)
    assert "risk_level" in preds[0]
