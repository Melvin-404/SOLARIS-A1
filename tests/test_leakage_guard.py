"""Unit tests for solar_flare.features.leakage_guard module.

Tests temporal leakage detection, future sample access prevention, and clean verification.
All synthetic fixtures are named fixture_synthetic_*.
"""

from __future__ import annotations

import pandas as pd
import pytest

from solar_flare.features.leakage_guard import (
    check_no_future_samples,
    check_inputs_causal,
    LeakageError,
)


@pytest.fixture
def fixture_synthetic_clean_windows() -> pd.DataFrame:
    """Create a DataFrame of clean sliding windows where max_time_used <= window_end."""
    return pd.DataFrame([
        {"window_id": "W001", "window_start": 0.0, "window_end": 60.0, "max_time_used": 60.0},
        {"window_id": "W002", "window_start": 10.0, "window_end": 70.0, "max_time_used": 69.5},
        {"window_id": "W003", "window_start": 20.0, "window_end": 80.0, "max_time_used": 80.0},
    ])


@pytest.fixture
def fixture_synthetic_leaking_windows() -> pd.DataFrame:
    """Create a DataFrame where a future sample is erroneously accessed."""
    return pd.DataFrame([
        {"window_id": "W001", "window_start": 0.0, "window_end": 60.0, "max_time_used": 60.0},
        # W002 accesses a sample at 71.5s > window_end=70.0s (LEAKAGE)
        {"window_id": "W002", "window_start": 10.0, "window_end": 70.0, "max_time_used": 71.5},
    ])


def test_clean_windows_pass_leakage_guard(fixture_synthetic_clean_windows):
    """Verify that clean windows pass the leakage guard without error."""
    assert check_no_future_samples(fixture_synthetic_clean_windows) is True


def test_injected_future_sample_triggers_leakage_error(fixture_synthetic_leaking_windows):
    """Verify that accessing any sample with t > window_end raises LeakageError."""
    with pytest.raises(LeakageError) as exc_info:
        check_no_future_samples(fixture_synthetic_leaking_windows)
    assert "CRITICAL TEMPORAL LEAKAGE DETECTED" in str(exc_info.value)
    assert "W002" in str(exc_info.value)
    assert "window_end=70.0" in str(exc_info.value)


def test_check_inputs_causal():
    """Verify that check_inputs_causal validates feature tables correctly."""
    clean_table = pd.DataFrame({
        "window_end": [60.0, 70.0, 80.0],
        "max_time_used": [59.0, 70.0, 79.9],
    })
    assert check_inputs_causal(clean_table, t0_column="window_end", observation_times_column="max_time_used") is True

    leaking_table = pd.DataFrame({
        "window_end": [60.0, 70.0],
        "max_time_used": [59.0, 70.5],
    })
    with pytest.raises(LeakageError) as exc_info:
        check_inputs_causal(leaking_table, t0_column="window_end", observation_times_column="max_time_used")
    assert "Causality violation" in str(exc_info.value)
