"""SOLARIS-A1 Pre-Flare Forecasting Module (Task B)."""

from __future__ import annotations

from solar_flare.forecasting.pipeline import (
    ForecastingPipeline,
    get_forecasting_pipeline,
    classify_pre_flare_risk,
)

__all__ = [
    "ForecastingPipeline",
    "get_forecasting_pipeline",
    "classify_pre_flare_risk",
]
