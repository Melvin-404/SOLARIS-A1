"""Block bootstrap uncertainty estimation for SOLARIS-A1 (Stage 11).

Estimates sampling distribution confidence intervals using block resampling over
independent continuous observation segments or flare events.

Crucial Governance:
- Overlapping sliding windows within the same segment violate independence assumptions.
- Standard i.i.d. row bootstrap yields severely overconfident confidence intervals.
- Block bootstrap resamples entire observation segments.
- If the number of distinct blocks is below the scientific threshold (e.g. < 5 or 10),
  computation is withheld and reported as:
  'CI NOT COMPUTED — insufficient independent blocks (n=<n>)'
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from solar_flare.evaluation.window_metrics import compute_window_metrics


@dataclass(frozen=True)
class MetricCI:
    """Confidence interval for a single metric."""

    metric_name: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    ci_level: float


@dataclass(frozen=True)
class BootstrapUncertaintyReport:
    """Structured report of block bootstrap uncertainty."""

    computed: bool
    status_message: str
    n_blocks: int
    min_required_blocks: int
    n_resamples: int
    ci_level: float
    metrics_ci: Dict[str, MetricCI]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "computed": self.computed,
            "status_message": self.status_message,
            "n_blocks": self.n_blocks,
            "min_required_blocks": self.min_required_blocks,
            "n_resamples": self.n_resamples,
            "ci_level": self.ci_level,
            "metrics_ci": {
                k: asdict(v) for k, v in self.metrics_ci.items()
            },
        }


@dataclass(frozen=True)
class PairedDifferenceCI:
    """Confidence interval for the difference between two models (Model A - Model B)."""

    metric_name: str
    diff_point_estimate: float
    ci_lower: float
    ci_upper: float
    ci_level: float
    p_value: float
    is_significant: bool


@dataclass(frozen=True)
class PairedComparisonReport:
    """Structured report of paired block bootstrap comparison between two models."""

    computed: bool
    status_message: str
    model_a_name: str
    model_b_name: str
    n_blocks: int
    min_required_blocks: int
    n_resamples: int
    ci_level: float
    differences: Dict[str, PairedDifferenceCI]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "computed": self.computed,
            "status_message": self.status_message,
            "model_a_name": self.model_a_name,
            "model_b_name": self.model_b_name,
            "n_blocks": self.n_blocks,
            "min_required_blocks": self.min_required_blocks,
            "n_resamples": self.n_resamples,
            "ci_level": self.ci_level,
            "differences": {k: asdict(v) for k, v in self.differences.items()},
        }


def compute_block_bootstrap_ci(
    data: pd.DataFrame,
    y_true_col: str = "label",
    y_pred_col: str = "pred",
    y_score_col: Optional[str] = "score",
    block_col: str = "segment_id",
    min_independent_blocks: int = 5,
    n_resamples: int = 500,
    ci_level: float = 0.95,
    random_state: int = 42,
) -> BootstrapUncertaintyReport:
    """Compute block bootstrap confidence intervals across independent segments/events.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing ground-truth, predictions, scores, and block identifier.
    y_true_col : str
        Name of ground-truth binary label column.
    y_pred_col : str
        Name of binary prediction column.
    y_score_col : str, optional
        Name of continuous score column.
    block_col : str
        Name of grouping column (e.g. 'segment_id' or 'event_id').
    min_independent_blocks : int, default=5
        Minimum unique blocks required to produce a valid bootstrap distribution.
    n_resamples : int, default=500
        Number of bootstrap iterations.
    ci_level : float, default=0.95
        Coverage level (e.g. 0.95 for 95% CI).
    random_state : int, default=42
        Deterministic random seed.

    Returns
    -------
    BootstrapUncertaintyReport
        Report with empirical percentile confidence intervals or refusal message.
    """
    if block_col not in data.columns:
        return BootstrapUncertaintyReport(
            computed=False,
            status_message=f"CI NOT COMPUTED — block column '{block_col}' missing in dataset",
            n_blocks=0,
            min_required_blocks=min_independent_blocks,
            n_resamples=n_resamples,
            ci_level=ci_level,
            metrics_ci={},
        )

    unique_blocks = list(data[block_col].dropna().unique())
    n_blocks = len(unique_blocks)

    if n_blocks < min_independent_blocks:
        return BootstrapUncertaintyReport(
            computed=False,
            status_message=f"CI NOT COMPUTED — insufficient independent blocks (n={n_blocks})",
            n_blocks=n_blocks,
            min_required_blocks=min_independent_blocks,
            n_resamples=n_resamples,
            ci_level=ci_level,
            metrics_ci={},
        )

    # Pre-group data by block for fast sampling
    grouped = {b: group for b, group in data.groupby(block_col)}
    rng = np.random.default_rng(random_state)

    f1_list: List[float] = []
    prec_list: List[float] = []
    rec_list: List[float] = []
    prauc_list: List[float] = []

    alpha = (1.0 - ci_level) / 2.0
    lower_pct = alpha * 100.0
    upper_pct = (1.0 - alpha) * 100.0

    for _ in range(n_resamples):
        sampled_blocks = rng.choice(unique_blocks, size=n_blocks, replace=True)
        resampled_dfs = [grouped[b] for b in sampled_blocks]
        resampled_df = pd.concat(resampled_dfs, ignore_index=True)

        y_t = resampled_df[y_true_col]
        y_p = resampled_df[y_pred_col]
        y_s = resampled_df[y_score_col] if y_score_col and y_score_col in resampled_df.columns else None

        rep = compute_window_metrics(y_t, y_p, y_s)
        f1_list.append(rep.f1)
        prec_list.append(rep.precision)
        rec_list.append(rep.recall)
        if rep.pr_auc is not None:
            prauc_list.append(rep.pr_auc)

    # Point estimates on full dataset
    full_rep = compute_window_metrics(
        data[y_true_col],
        data[y_pred_col],
        data[y_score_col] if y_score_col and y_score_col in data.columns else None,
    )

    metrics_ci: Dict[str, MetricCI] = {}
    for name, sample_list, pt_val in [
        ("f1", f1_list, full_rep.f1),
        ("precision", prec_list, full_rep.precision),
        ("recall", rec_list, full_rep.recall),
    ]:
        low = float(np.percentile(sample_list, lower_pct))
        high = float(np.percentile(sample_list, upper_pct))
        metrics_ci[name] = MetricCI(
            metric_name=name,
            point_estimate=pt_val,
            ci_lower=low,
            ci_upper=high,
            ci_level=ci_level,
        )

    if prauc_list and full_rep.pr_auc is not None:
        low = float(np.percentile(prauc_list, lower_pct))
        high = float(np.percentile(prauc_list, upper_pct))
        metrics_ci["pr_auc"] = MetricCI(
            metric_name="pr_auc",
            point_estimate=full_rep.pr_auc,
            ci_lower=low,
            ci_upper=high,
            ci_level=ci_level,
        )

    return BootstrapUncertaintyReport(
        computed=True,
        status_message="COMPUTED",
        n_blocks=n_blocks,
        min_required_blocks=min_independent_blocks,
        n_resamples=n_resamples,
        ci_level=ci_level,
        metrics_ci=metrics_ci,
    )


def create_temporal_clusters(
    data: pd.DataFrame,
    time_col: str = "window_start",
    cluster_duration_seconds: float = 1800.0,
) -> pd.Series:
    """Group continuous timestamps into non-overlapping temporal clusters for block resampling.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing a continuous timestamp column.
    time_col : str, default="window_start"
        Timestamp column name.
    cluster_duration_seconds : float, default=1800.0
        Duration in seconds for each cluster block (default 30 minutes).

    Returns
    -------
    pd.Series
        Series of cluster identifiers matching data indices.
    """
    if time_col not in data.columns:
        raise KeyError(f"Timestamp column '{time_col}' not found in DataFrame.")

    times = pd.to_numeric(data[time_col], errors="coerce").fillna(0.0)
    min_time = float(times.min())
    cluster_ids = ((times - min_time) // cluster_duration_seconds).astype(int)
    return cluster_ids.map(lambda c: f"cluster_{c:04d}")


def compute_paired_bootstrap_comparison(
    data: pd.DataFrame,
    model_a_pred_col: str,
    model_b_pred_col: str,
    model_a_score_col: Optional[str] = None,
    model_b_score_col: Optional[str] = None,
    y_true_col: str = "label",
    block_col: str = "segment_id",
    model_a_name: str = "model_a",
    model_b_name: str = "model_b",
    min_independent_blocks: int = 5,
    n_resamples: int = 500,
    ci_level: float = 0.95,
    random_state: int = 42,
) -> PairedComparisonReport:
    """Compute paired block bootstrap comparison between two models.

    Computes empirical distributions of differences (Model A - Model B) across
    resampled independent blocks, evaluating whether observed performance differences
    are statistically distinguishable from zero.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing ground-truth, predictions, scores, and block identifier.
    model_a_pred_col : str
        Prediction column for Model A.
    model_b_pred_col : str
        Prediction column for Model B.
    model_a_score_col : str, optional
        Continuous probability/score column for Model A.
    model_b_score_col : str, optional
        Continuous probability/score column for Model B.
    y_true_col : str, default="label"
        Ground truth binary label column.
    block_col : str, default="segment_id"
        Grouping column for independent block resampling.
    model_a_name : str, default="model_a"
        Display name for Model A.
    model_b_name : str, default="model_b"
        Display name for Model B.
    min_independent_blocks : int, default=5
        Minimum unique blocks required.
    n_resamples : int, default=500
        Number of bootstrap iterations.
    ci_level : float, default=0.95
        Confidence level.
    random_state : int, default=42
        Deterministic random seed.

    Returns
    -------
    PairedComparisonReport
        Detailed paired comparison report with differences, 95% CIs, and empirical p-values.
    """
    if block_col not in data.columns:
        return PairedComparisonReport(
            computed=False,
            status_message=f"COMPARISON NOT COMPUTED — block column '{block_col}' missing in dataset",
            model_a_name=model_a_name,
            model_b_name=model_b_name,
            n_blocks=0,
            min_required_blocks=min_independent_blocks,
            n_resamples=n_resamples,
            ci_level=ci_level,
            differences={},
        )

    unique_blocks = list(data[block_col].dropna().unique())
    n_blocks = len(unique_blocks)

    if n_blocks < min_independent_blocks:
        return PairedComparisonReport(
            computed=False,
            status_message=f"COMPARISON NOT COMPUTED — insufficient independent blocks (n={n_blocks} < {min_independent_blocks})",
            model_a_name=model_a_name,
            model_b_name=model_b_name,
            n_blocks=n_blocks,
            min_required_blocks=min_independent_blocks,
            n_resamples=n_resamples,
            ci_level=ci_level,
            differences={},
        )

    grouped = {b: group for b, group in data.groupby(block_col)}
    rng = np.random.default_rng(random_state)

    f1_diffs: List[float] = []
    prec_diffs: List[float] = []
    rec_diffs: List[float] = []
    prauc_diffs: List[float] = []
    rocauc_diffs: List[float] = []

    alpha = (1.0 - ci_level) / 2.0
    lower_pct = alpha * 100.0
    upper_pct = (1.0 - alpha) * 100.0

    for _ in range(n_resamples):
        sampled_blocks = rng.choice(unique_blocks, size=n_blocks, replace=True)
        resampled_dfs = [grouped[b] for b in sampled_blocks]
        resampled_df = pd.concat(resampled_dfs, ignore_index=True)

        y_t = resampled_df[y_true_col]
        y_pa = resampled_df[model_a_pred_col]
        y_pb = resampled_df[model_b_pred_col]
        y_sa = resampled_df[model_a_score_col] if model_a_score_col and model_a_score_col in resampled_df.columns else None
        y_sb = resampled_df[model_b_score_col] if model_b_score_col and model_b_score_col in resampled_df.columns else None

        rep_a = compute_window_metrics(y_t, y_pa, y_sa)
        rep_b = compute_window_metrics(y_t, y_pb, y_sb)

        f1_diffs.append(rep_a.f1 - rep_b.f1)
        prec_diffs.append(rep_a.precision - rep_b.precision)
        rec_diffs.append(rep_a.recall - rep_b.recall)

        if rep_a.pr_auc is not None and rep_b.pr_auc is not None:
            prauc_diffs.append(rep_a.pr_auc - rep_b.pr_auc)
        if rep_a.roc_auc is not None and rep_b.roc_auc is not None:
            rocauc_diffs.append(rep_a.roc_auc - rep_b.roc_auc)

    # Point estimates on full dataset
    y_full_t = data[y_true_col]
    full_rep_a = compute_window_metrics(
        y_full_t,
        data[model_a_pred_col],
        data[model_a_score_col] if model_a_score_col and model_a_score_col in data.columns else None,
    )
    full_rep_b = compute_window_metrics(
        y_full_t,
        data[model_b_pred_col],
        data[model_b_score_col] if model_b_score_col and model_b_score_col in data.columns else None,
    )

    diff_records: Dict[str, PairedDifferenceCI] = {}
    metrics_to_eval = [
        ("f1", f1_diffs, full_rep_a.f1 - full_rep_b.f1),
        ("precision", prec_diffs, full_rep_a.precision - full_rep_b.precision),
        ("recall", rec_diffs, full_rep_a.recall - full_rep_b.recall),
    ]
    if prauc_diffs and full_rep_a.pr_auc is not None and full_rep_b.pr_auc is not None:
        metrics_to_eval.append(("pr_auc", prauc_diffs, full_rep_a.pr_auc - full_rep_b.pr_auc))
    if rocauc_diffs and full_rep_a.roc_auc is not None and full_rep_b.roc_auc is not None:
        metrics_to_eval.append(("roc_auc", rocauc_diffs, full_rep_a.roc_auc - full_rep_b.roc_auc))

    for name, diff_list, pt_diff in metrics_to_eval:
        low = float(np.percentile(diff_list, lower_pct))
        high = float(np.percentile(diff_list, upper_pct))
        # Two-sided empirical p-value
        p_val = float(min(1.0, 2.0 * min(np.mean([d <= 0.0 for d in diff_list]), np.mean([d >= 0.0 for d in diff_list]))))
        # Statistically significant if zero is outside CI
        is_sig = bool(low > 0.0 or high < 0.0)

        diff_records[name] = PairedDifferenceCI(
            metric_name=name,
            diff_point_estimate=float(pt_diff),
            ci_lower=low,
            ci_upper=high,
            ci_level=ci_level,
            p_value=p_val,
            is_significant=is_sig,
        )

    return PairedComparisonReport(
        computed=True,
        status_message="COMPUTED",
        model_a_name=model_a_name,
        model_b_name=model_b_name,
        n_blocks=n_blocks,
        min_required_blocks=min_independent_blocks,
        n_resamples=n_resamples,
        ci_level=ci_level,
        differences=diff_records,
    )
