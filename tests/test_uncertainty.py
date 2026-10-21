"""Unit tests for block bootstrap uncertainty estimation (Stage 11).

Tests:
1. Block bootstrap withholds CI computation and reports refusal reason when
   number of independent blocks is below scientific threshold.
2. Block bootstrap computes valid percentile intervals when block floor is satisfied.
"""

import numpy as np
import pandas as pd
import pytest
from solar_flare.evaluation.uncertainty import compute_block_bootstrap_ci


def test_ci_not_computed_when_blocks_below_minimum():
    """Verify that CI is withheld with explicit message when independent blocks < min_required."""
    # Only 2 independent observation segments
    df = pd.DataFrame({
        "label": [1, 0, 1, 0, 0, 0],
        "pred": [1, 0, 0, 0, 1, 0],
        "score": [0.8, 0.2, 0.4, 0.1, 0.7, 0.3],
        "segment_id": ["seg_01", "seg_01", "seg_01", "seg_02", "seg_02", "seg_02"],
    })

    rep = compute_block_bootstrap_ci(df, min_independent_blocks=5, block_col="segment_id")

    assert rep.computed is False
    assert "CI NOT COMPUTED — insufficient independent blocks (n=2)" in rep.status_message
    assert rep.n_blocks == 2
    assert rep.min_required_blocks == 5
    assert len(rep.metrics_ci) == 0


def test_ci_computed_when_blocks_sufficient():
    """Verify that valid empirical confidence intervals are computed when block count >= min_required."""
    # 6 independent blocks
    records = []
    for b_idx in range(6):
        b_name = f"seg_{b_idx:02d}"
        for _ in range(10):
            lbl = np.random.choice([0, 1], p=[0.7, 0.3])
            sc = 0.8 if lbl == 1 else 0.2
            records.append({
                "label": lbl,
                "pred": int(sc >= 0.5),
                "score": sc,
                "segment_id": b_name,
            })
    df = pd.DataFrame(records)

    rep = compute_block_bootstrap_ci(
        df,
        min_independent_blocks=5,
        n_resamples=50,
        random_state=42,
    )

    assert rep.computed is True
    assert rep.status_message == "COMPUTED"
    assert rep.n_blocks == 6
    assert "f1" in rep.metrics_ci
    assert "precision" in rep.metrics_ci
    assert "recall" in rep.metrics_ci
    assert rep.metrics_ci["f1"].ci_lower <= rep.metrics_ci["f1"].ci_upper
