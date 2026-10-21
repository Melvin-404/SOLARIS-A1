"""Unit tests for solar_flare.features.baseline module.

Tests causal lookback interval boundaries, sample floor safeguards, and acausality isolation.
All synthetic fixtures are named fixture_synthetic_*.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from solar_flare.features.baseline import causal_baseline


@pytest.fixture
def fixture_synthetic_segment_for_baseline() -> pd.DataFrame:
    """Create a continuous segment covering timestamps 0.0 to 1000.0 s.
    
    1001 samples at 1.0 s cadence:
    - Pre-window region [0.0, 600.0): constant counts = 20.0
    - Active region [600.0, 1000.0]: constant counts = 100.0
    """
    times = [float(i) for i in range(1001)]
    counts = [20.0 if t < 600.0 else 100.0 for t in times]
    return pd.DataFrame({"TIME": times, "COUNTS": counts})


def test_baseline_causality_never_uses_present_or_future_samples(
    fixture_synthetic_segment_for_baseline,
):
    """Verify that baseline at window_start=600.0 only uses samples with t < 600.0 (value 20.0, not 100.0)."""
    df = fixture_synthetic_segment_for_baseline

    val, rsn = causal_baseline(
        segment_df=df,
        window_start=600.0,
        lookback_seconds=600.0,
        min_samples=30,
    )

    assert val == 20.0
    assert rsn is None


def test_baseline_insufficient_lookback_samples_returns_nan():
    """Verify that if fewer than min_samples exist in the lookback window, returns NaN with reason."""
    # Only 10 samples in lookback interval
    df = pd.DataFrame({
        "TIME": [590.0 + float(i) for i in range(10)] + [600.0, 601.0, 602.0],
        "COUNTS": [15.0] * 13,
    })

    val, rsn = causal_baseline(
        segment_df=df,
        window_start=600.0,
        lookback_seconds=600.0,
        min_samples=30,
    )

    assert np.isnan(val)
    assert "BASELINE_INSUFFICIENT" in rsn
