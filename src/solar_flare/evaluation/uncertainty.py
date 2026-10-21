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
