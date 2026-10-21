"""Unit tests for dataset splitting algorithms (Stage 10).

Validates:
- Chronological split enforces embargo buffers on both train-val and val-test boundaries.
- Event-grouped split never assigns an event/segment group to multiple partitions.
- PENDING split parameters raise SplitNotApprovedError.
- SplitReport counts reconcile with total dataset size.
"""

from __future__ import annotations

import pytest
import numpy as np
import pandas as pd

from solar_flare.modelling.splits import chronological_split, event_grouped_split
from solar_flare.modelling.guards import SplitNotApprovedError


@pytest.fixture
def fixture_synthetic_continuous_windows():
    """Create synthetic continuous window metadata spanning 1000s."""
    n_windows = 100
    w_len = 60.0
    w_stride = 10.0
    starts = [float(i * w_stride) for i in range(n_windows)]
    ends = [float(s + w_len) for s in starts]
    labels = [1 if i % 10 == 0 else 0 for i in range(n_windows)]

    meta = pd.DataFrame({
        "window_id": [f"win_{i:04d}" for i in range(n_windows)],
        "segment_id": ["seg_01" if i < 50 else "seg_02" for i in range(n_windows)],
        "window_start": starts,
        "window_end": ends,
    })
    return meta, pd.Series(labels)


def test_chronological_split_embargo_and_reconciliation(fixture_synthetic_continuous_windows):
    """Verify chronological split enforces embargo buffers and reconciles all sample counts."""
    meta, labels = fixture_synthetic_continuous_windows
    # Window spans from 0s to 1050s
    train_end = 400.0
    val_end = 700.0
    embargo = 50.0

    train_idx, val_idx, test_idx, report = chronological_split(
        metadata=meta,
        train_end=train_end,
        val_end=val_end,
        embargo_seconds=embargo,
        labels=labels,
    )

    # 1. Total count reconciliation: train + val + test + dropped == total
    assert len(train_idx) + len(val_idx) + len(test_idx) + report.n_dropped_embargo == len(meta)

    # 2. Strict boundary assertions
    train_ends = meta.iloc[train_idx]["window_end"]
    assert all(train_ends <= train_end)

    val_starts = meta.iloc[val_idx]["window_start"]
    val_ends = meta.iloc[val_idx]["window_end"]
    assert all(val_starts >= (train_end + embargo))
    assert all(val_ends <= val_end)

    test_starts = meta.iloc[test_idx]["window_start"]
    assert all(test_starts >= (val_end + embargo))

    # 3. Disjoint set assertion
    assert len(set(train_idx).intersection(set(val_idx))) == 0
    assert len(set(val_idx).intersection(set(test_idx))) == 0
    assert len(set(train_idx).intersection(set(test_idx))) == 0
    assert report.n_dropped_embargo > 0


def test_chronological_split_pending_parameter_raises(fixture_synthetic_continuous_windows):
    """Verify that a PENDING train_end or val_end raises SplitNotApprovedError."""
    meta, labels = fixture_synthetic_continuous_windows

    with pytest.raises(SplitNotApprovedError, match="PENDING"):
        chronological_split(
            metadata=meta,
            train_end="PENDING",
            val_end=500.0,
            embargo_seconds=50.0,
        )


def test_event_grouped_split_zero_group_leakage():
    """Verify that event_grouped_split never places windows from the same group in two sets."""
    n_windows = 90
    groups = ["seg_A"] * 30 + ["seg_B"] * 30 + ["seg_C"] * 30
    meta = pd.DataFrame({
        "window_id": [f"w_{i}" for i in range(n_windows)],
        "segment_id": groups,
        "window_start": [float(i * 10) for i in range(n_windows)],
        "window_end": [float(i * 10 + 60) for i in range(n_windows)],
    })

    train_idx, val_idx, test_idx, report = event_grouped_split(
        metadata=meta,
        group_col="segment_id",
        fractions=(0.34, 0.33, 0.33),
        random_state=42,
    )

    train_groups = set(meta.iloc[train_idx]["segment_id"])
    val_groups = set(meta.iloc[val_idx]["segment_id"])
    test_groups = set(meta.iloc[test_idx]["segment_id"])

    assert len(train_groups.intersection(val_groups)) == 0
    assert len(val_groups.intersection(test_groups)) == 0
    assert len(train_groups.intersection(test_groups)) == 0
    assert len(train_idx) + len(val_idx) + len(test_idx) == n_windows
