"""Dataset Splitting Algorithms for SOLARIS-A1 (Stage 10).

Provides:
1. chronological_split: Strict time-ordered splitting with temporal embargo buffers applied
   between train-val and val-test partitions to prevent boundary leakage.
2. event_grouped_split: Grouped splitting by contiguous segment or flare event ID, guaranteeing
   that all windows from an event or segment reside entirely within a single partition.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Random row-level splitting (e.g. standard shuffle) is STRICTLY PROHIBITED due to the 83.3%
   window overlap (stride S=10s, length W=60s) which causes catastrophic temporal leakage.
2. Any PENDING split parameter raises SplitNotApprovedError immediately.
3. Every split returns a comprehensive, hash-verified SplitReport detailing exact row counts,
   class distributions, and dropped embargo samples.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
import pandas as pd

from solar_flare.modelling.guards import SplitNotApprovedError


@dataclass
class SplitReport:
    """Auditable summary of dataset partition counts, class balances, and embargo metrics."""
    split_strategy: str
    n_total: int
    n_train: int
    n_val: int
    n_test: int
    n_dropped_embargo: int
    train_class_counts: Dict[str, int]
    val_class_counts: Dict[str, int]
    test_class_counts: Dict[str, int]
    embargo_seconds: float
    split_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _compute_split_hash(train_idx: np.ndarray, val_idx: np.ndarray, test_idx: np.ndarray) -> str:
    """Compute deterministic SHA-256 hash over split index arrays."""
    data = (
        train_idx.tobytes() + b":" +
        val_idx.tobytes() + b":" +
        test_idx.tobytes()
    )
    return hashlib.sha256(data).hexdigest()[:16]


def _extract_class_counts(labels: Optional[pd.Series], indices: np.ndarray) -> Dict[str, int]:
    """Compute integer counts of positives (1), negatives (0), and unverified (NA)."""
    if labels is None or len(indices) == 0:
        return {"positives": 0, "negatives": 0, "excluded_na": 0}

    sub = labels.iloc[indices] if hasattr(labels, "iloc") else pd.Series(labels)[indices]
    n_pos = int((sub == 1).sum())
    n_neg = int((sub == 0).sum())
    n_na = int(sub.isna().sum())
    return {"positives": n_pos, "negatives": n_neg, "excluded_na": n_na}


def chronological_split(
    metadata: pd.DataFrame,
    train_end: float,
    val_end: float,
    embargo_seconds: float = 300.0,
    labels: Optional[pd.Series] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, SplitReport]:
    """Perform strict chronological splitting with temporal embargo buffers.
    
    Partitions:
    - Train: window_end <= train_end
    - Embargo 1: (train_end, train_end + embargo_seconds) -> DROPPED
    - Validation: window_start >= train_end + embargo_seconds AND window_end <= val_end
    - Embargo 2: (val_end, val_end + embargo_seconds) -> DROPPED
    - Test: window_start >= val_end + embargo_seconds
    
    Parameters
    ----------
    metadata : pd.DataFrame
        Table containing window_start and window_end timestamps.
    train_end : float
        End timestamp of training partition.
    val_end : float
        End timestamp of validation partition.
    embargo_seconds : float
        Buffer duration applied after train_end and val_end.
    labels : Optional[pd.Series]
        Target labels for class distribution tracking.
        
    Returns
    -------
    Tuple[train_idx, val_idx, test_idx, SplitReport]
    
    Raises
    -------
    SplitNotApprovedError
        If parameters are None, inverted, or marked PENDING.
    """
    for name, val in [("train_end", train_end), ("val_end", val_end), ("embargo_seconds", embargo_seconds)]:
        if val is None or (isinstance(val, str) and "PENDING" in str(val).upper()):
            raise SplitNotApprovedError(f"Split parameter '{name}' is PENDING human approval.")

    t_end = float(train_end)
    v_end = float(val_end)
    emb = float(embargo_seconds)

    if v_end <= t_end:
        raise SplitNotApprovedError(f"val_end ({v_end}) must be strictly greater than train_end ({t_end}).")
    if emb < 0.0:
        raise SplitNotApprovedError(f"embargo_seconds cannot be negative, got {emb}")

    win_start = metadata["window_start"].to_numpy(dtype=np.float64)
    win_end = metadata["window_end"].to_numpy(dtype=np.float64)
    n_samples = len(metadata)
    all_indices = np.arange(n_samples)

    # 1. Identify partitions
    train_mask = win_end <= t_end
    val_mask = (win_start >= (t_end + emb)) & (win_end <= v_end)
    test_mask = win_start >= (v_end + emb)

    train_idx = all_indices[train_mask]
    val_idx = all_indices[val_mask]
    test_idx = all_indices[test_mask]

    # Dropped windows (falling into either embargo buffer or spanning boundary)
    used_mask = train_mask | val_mask | test_mask
    n_dropped = int((~used_mask).sum())

    # Verify mutual exclusivity
    assert len(set(train_idx).intersection(set(val_idx))) == 0
    assert len(set(val_idx).intersection(set(test_idx))) == 0
    assert len(set(train_idx).intersection(set(test_idx))) == 0

    train_classes = _extract_class_counts(labels, train_idx)
    val_classes = _extract_class_counts(labels, val_idx)
    test_classes = _extract_class_counts(labels, test_idx)

    split_hash = _compute_split_hash(train_idx, val_idx, test_idx)

    report = SplitReport(
        split_strategy="chronological",
        n_total=n_samples,
        n_train=len(train_idx),
        n_val=len(val_idx),
        n_test=len(test_idx),
        n_dropped_embargo=n_dropped,
        train_class_counts=train_classes,
        val_class_counts=val_classes,
        test_class_counts=test_classes,
        embargo_seconds=emb,
        split_hash=split_hash,
    )

    return train_idx, val_idx, test_idx, report


def event_grouped_split(
    metadata: pd.DataFrame,
    group_col: str,
    fractions: Sequence[float] = (0.60, 0.20, 0.20),
    random_state: int = 42,
    embargo_seconds: float = 0.0,
    labels: Optional[pd.Series] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, SplitReport]:
    """Perform group-based splitting ensuring no group is split across train/val/test partitions.
    
    Parameters
    ----------
    metadata : pd.DataFrame
        Table containing group column (e.g. segment_id or event_id).
    group_col : str
        Column name used for grouping.
    fractions : tuple of float
        Target proportions for (train, val, test), summing to 1.0.
    random_state : int
        Deterministic random seed for group permutation.
    embargo_seconds : float
        Embargo duration.
    labels : Optional[pd.Series]
        Target labels.
        
    Returns
    -------
    Tuple[train_idx, val_idx, test_idx, SplitReport]
    """
    if group_col not in metadata.columns:
        raise SplitNotApprovedError(f"group_column '{group_col}' not found in metadata.")

    if len(fractions) != 3 or not np.isclose(sum(fractions), 1.0):
        raise SplitNotApprovedError(f"fractions must be 3 positive numbers summing to 1.0, got {fractions}")

    unique_groups = metadata[group_col].dropna().unique()
    n_groups = len(unique_groups)

    if n_groups < 3:
        raise SplitNotApprovedError(
            f"event_grouped_split requires at least 3 distinct groups, found {n_groups} in '{group_col}'."
        )

    rng = np.random.RandomState(random_state)
    shuffled_groups = rng.permutation(unique_groups)

    n_train_g = max(1, int(round(n_groups * fractions[0])))
    n_val_g = max(1, int(round(n_groups * fractions[1])))
    # Remainder goes to test
    if n_train_g + n_val_g >= n_groups:
        n_train_g = n_groups - 2
        n_val_g = 1

    train_groups = set(shuffled_groups[:n_train_g])
    val_groups = set(shuffled_groups[n_train_g:n_train_g + n_val_g])
    test_groups = set(shuffled_groups[n_train_g + n_val_g:])

    # Strict assertion: zero group overlap
    assert len(train_groups.intersection(val_groups)) == 0
    assert len(val_groups.intersection(test_groups)) == 0
    assert len(train_groups.intersection(test_groups)) == 0

    all_indices = np.arange(len(metadata))
    group_series = metadata[group_col]

    train_idx = all_indices[group_series.isin(train_groups)]
    val_idx = all_indices[group_series.isin(val_groups)]
    test_idx = all_indices[group_series.isin(test_groups)]

    train_classes = _extract_class_counts(labels, train_idx)
    val_classes = _extract_class_counts(labels, val_idx)
    test_classes = _extract_class_counts(labels, test_idx)
    split_hash = _compute_split_hash(train_idx, val_idx, test_idx)

    report = SplitReport(
        split_strategy="event_grouped",
        n_total=len(metadata),
        n_train=len(train_idx),
        n_val=len(val_idx),
        n_test=len(test_idx),
        n_dropped_embargo=0,
        train_class_counts=train_classes,
        val_class_counts=val_classes,
        test_class_counts=test_classes,
        embargo_seconds=float(embargo_seconds),
        split_hash=split_hash,
    )

    return train_idx, val_idx, test_idx, report
