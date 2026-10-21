"""Feature registry and batch feature extractor for SOLARIS-A1 (Stage 8).

Defines metadata (units, formulas, causality notes, approval statuses) for all 18 features
and executes extraction per sliding window.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
import numpy as np

from solar_flare.features import features as F


@dataclass
class FeatureMetadata:
    """Metadata specification for an individual registered feature."""
    name: str
    description: str
    units: str
    formula_text: str
    requires_baseline: bool
    requires_time: bool
    leakage_note: str
    status: str  # 'PROVISIONAL' or 'APPROVED'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FeatureRegistry:
    """Central registry cataloging all time-series feature extractors and metadata."""

    def __init__(self) -> None:
        self._registry: Dict[str, Tuple[Callable, FeatureMetadata]] = {}
        self._register_default_features()

    def register(
        self,
        name: str,
        func: Callable,
        description: str,
        units: str,
        formula_text: str,
        requires_baseline: bool = False,
        requires_time: bool = False,
        leakage_note: str = "Causal: strictly uses samples within [window_start, window_end].",
        status: str = "PROVISIONAL",
    ) -> None:
        """Register a feature calculation function and associated scientific metadata."""
        meta = FeatureMetadata(
            name=name,
            description=description,
            units=units,
            formula_text=formula_text,
            requires_baseline=requires_baseline,
            requires_time=requires_time,
            leakage_note=leakage_note,
            status=status,
        )
        self._registry[name] = (func, meta)

    def get_metadata(self, name: str) -> FeatureMetadata:
        """Retrieve metadata for a registered feature."""
        if name not in self._registry:
            raise KeyError(f"Feature '{name}' not found in registry.")
        return self._registry[name][1]

    def get(self, name: str) -> Optional[FeatureMetadata]:
        """Retrieve metadata for a registered feature or None if not found."""
        if name in self._registry:
            return self._registry[name][1]
        return None

    def list_features(self) -> List[str]:
        """Return list of all registered feature names."""
        return sorted(list(self._registry.keys()))

    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Return metadata for all registered features."""
        return {k: v[1].to_dict() for k, v in self._registry.items()}

    def _register_default_features(self) -> None:
        """Register the standard set of 18 solar flare time-series features."""
        self.register(
            name="mean",
            func=F.calc_mean,
            description="Arithmetic mean of photon count rate in window",
            units="Counts",
            formula_text="(1 / N) * sum(x_i)",
            requires_baseline=False,
            requires_time=False,
        )
        self.register(
            name="median",
            func=F.calc_median,
            description="Sample median (50th percentile) of count rate in window",
            units="Counts",
            formula_text="50th percentile of x_i",
            requires_baseline=False,
            requires_time=False,
        )
        self.register(
            name="std",
            func=F.calc_std,
            description="Sample standard deviation with Bessel correction (ddof=1)",
            units="Counts",
            formula_text="sqrt( (1 / (N - 1)) * sum((x_i - mean)^2) )",
            requires_baseline=False,
            requires_time=False,
        )
        self.register(
            name="robust_variability",
            func=F.calc_robust_variability,
            description="Normalized Median Absolute Deviation (MAD * 1.4826)",
            units="Counts",
            formula_text="1.4826 * median( |x_i - median(x)| )",
            requires_baseline=False,
            requires_time=False,
        )
        self.register(
            name="min",
            func=F.calc_min,
            description="Minimum observed count rate in window",
            units="Counts",
            formula_text="min(x_i)",
            requires_baseline=False,
            requires_time=False,
        )
        self.register(
            name="max",
            func=F.calc_max,
            description="Maximum observed count rate in window (peak flux)",
            units="Counts",
            formula_text="max(x_i)",
            requires_baseline=False,
            requires_time=False,
        )
        self.register(
            name="iqr",
            func=F.calc_iqr,
            description="Interquartile Range (75th minus 25th percentile)",
            units="Counts",
            formula_text="p75 - p25",
            requires_baseline=False,
            requires_time=False,
        )
        self.register(
            name="mean_abs_first_difference",
            func=F.calc_mean_abs_first_diff,
            description="Mean absolute first difference between adjacent chronological steps",
            units="Counts",
            formula_text="(1 / (N - 1)) * sum( |x_{i+1} - x_i| )",
            requires_baseline=False,
            requires_time=False,
        )
        self.register(
            name="max_abs_first_difference",
            func=F.calc_max_abs_first_diff,
            description="Maximum absolute first difference (single-step impulsive jump)",
            units="Counts",
            formula_text="max( |x_{i+1} - x_i| )",
            requires_baseline=False,
            requires_time=False,
        )
        self.register(
            name="temporal_slope",
            func=F.calc_temporal_slope,
            description="Ordinary least-squares linear slope across full window",
            units="Counts / second",
            formula_text="Cov(x, t) / Var(t)",
            requires_baseline=False,
            requires_time=True,
        )
        self.register(
            name="rolling_trend",
            func=F.calc_rolling_trend,
            description="Least-squares linear slope across trailing K seconds of window",
            units="Counts / second",
            formula_text="Slope over samples where t >= window_end - K",
            requires_baseline=False,
            requires_time=True,
            status="PROVISIONAL",
        )
        self.register(
            name="peak_to_baseline_ratio",
            func=F.calc_peak_to_baseline_ratio,
            description="Ratio of window maximum to local pre-window causal baseline flux",
            units="Dimensionless",
            formula_text="max(x_i) / baseline",
            requires_baseline=True,
            requires_time=False,
            leakage_note="Causal: baseline uses strictly pre-window interval [window_start - lookback, window_start).",
            status="PROVISIONAL",
        )
        self.register(
            name="coverage_fraction",
            func=F.calc_coverage_fraction,
            description="Fraction of observed valid samples relative to expected count",
            units="Dimensionless",
            formula_text="n_observed / n_expected",
            requires_baseline=False,
            requires_time=False,
        )
        self.register(
            name="n_observed_samples",
            func=F.calc_n_observed_samples,
            description="Count of valid finite observations present in window",
            units="Count",
            formula_text="count(finite x_i)",
            requires_baseline=False,
            requires_time=False,
        )


# Global default registry instance
GLOBAL_REGISTRY = FeatureRegistry()
DEFAULT_REGISTRY = GLOBAL_REGISTRY


def compute_features(
    window_values: Sequence[float],
    window_times: Sequence[float],
    baseline_value: Optional[float] = None,
    enabled_features: Optional[Sequence[str]] = None,
    n_expected_samples: int = 60,
    rolling_trend_k: float = 15.0,
    percentile_levels: Sequence[float] = (5, 25, 75, 95),
    registry: Optional[FeatureRegistry] = None,
) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """Compute enabled feature values and reason codes for a single observation window.
    
    Parameters
    ----------
    window_values : Sequence[float]
        Photon counts or count rates in the window.
    window_times : Sequence[float]
        Observation timestamps corresponding to values.
    baseline_value : Optional[float]
        Pre-window causal baseline flux (from causal_baseline).
    enabled_features : Optional[Sequence[str]]
        Subset of features to extract. If None, computes all registered features.
    n_expected_samples : int
        Expected count of samples for coverage calculation.
    rolling_trend_k : float
        Trailing duration K (s) for rolling trend.
    percentile_levels : Sequence[float]
        Levels for percentile extraction.
    registry : Optional[FeatureRegistry]
        Registry instance (defaults to GLOBAL_REGISTRY).
        
    Returns
    -------
    Tuple[Dict[str, float], Dict[str, Optional[str]]]
        (feature_values, feature_reasons)
        feature_values: float values per feature (NaN if edge case occurred).
        feature_reasons: None if successful, or reason code string if NaN.
    """
    reg = registry or GLOBAL_REGISTRY
    values_out: Dict[str, float] = {}
    reasons_out: Dict[str, Optional[str]] = {}

    target_features = list(enabled_features) if enabled_features else reg.list_features()

    # Percentiles helper extraction
    pct_dict = F.calc_percentiles(window_values, levels=percentile_levels)
    for lvl in percentile_levels:
        key = f"p{int(lvl):02d}" if lvl == int(lvl) else f"p{lvl}"
        val, rsn = pct_dict.get(key, (np.nan, "NOT_COMPUTED"))
        values_out[key] = val
        reasons_out[key] = rsn

    # Compute individual registered features
    for name in target_features:
        if name.startswith("p") and name[1:].isdigit():
            # Already computed above
            continue

        if name not in reg._registry:
            continue

        func, meta = reg._registry[name]

        try:
            if meta.requires_baseline:
                val, rsn = func(window_values, baseline_value=baseline_value)
            elif meta.requires_time:
                if name == "rolling_trend":
                    val, rsn = func(window_values, window_times, k_seconds=rolling_trend_k)
                else:
                    val, rsn = func(window_values, window_times)
            elif name == "coverage_fraction":
                val, rsn = func(window_values, n_expected=n_expected_samples)
            else:
                val, rsn = func(window_values)
        except Exception as exc:
            val, rsn = np.nan, f"ERROR: {exc}"

        values_out[name] = val
        reasons_out[name] = rsn

    return values_out, reasons_out
