"""Sliding windows and causal feature engineering subsystem for SOLARIS-A1 (Stage 8).

Provides continuous segmentation windowing, a mathematically defined causal feature library,
local causal background flux estimation, and temporal leakage verification.
"""

from __future__ import annotations

from solar_flare.features.windows import generate_windows, WindowRecord
from solar_flare.features.features import (
    calc_mean,
    calc_median,
    calc_std,
    calc_robust_variability,
    calc_min,
    calc_max,
    calc_percentiles,
    calc_iqr,
    calc_mean_abs_first_diff,
    calc_max_abs_first_diff,
    calc_temporal_slope,
    calc_rolling_trend,
    calc_peak_to_baseline_ratio,
    calc_coverage_fraction,
    calc_n_observed_samples,
)
from solar_flare.features.registry import FeatureRegistry, compute_features
from solar_flare.features.baseline import causal_baseline
from solar_flare.features.leakage_guard import (
    check_no_future_samples,
    check_inputs_causal,
    LeakageError,
)

__all__ = [
    "generate_windows",
    "WindowRecord",
    "calc_mean",
    "calc_median",
    "calc_std",
    "calc_robust_variability",
    "calc_min",
    "calc_max",
    "calc_percentiles",
    "calc_iqr",
    "calc_mean_abs_first_diff",
    "calc_max_abs_first_diff",
    "calc_temporal_slope",
    "calc_rolling_trend",
    "calc_peak_to_baseline_ratio",
    "calc_coverage_fraction",
    "calc_n_observed_samples",
    "FeatureRegistry",
    "compute_features",
    "causal_baseline",
    "check_no_future_samples",
    "check_inputs_causal",
    "LeakageError",
]
