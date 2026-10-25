"""Pydantic schemas for SOLARIS-A1 FastAPI service.

Strict, self-documenting request and response schemas suitable for external website integration.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field("healthy", description="Operational health status of the service.")
    model_loaded: bool = Field(True, description="Whether the trained ML model is loaded in memory.")
    model_name: str = Field(..., description="Active champion model identifier.")
    model_version: str = Field(..., description="Version string with experiment ID anchor.")
    service_timestamp_utc: str = Field(..., description="Current server UTC timestamp.")
    profile: str = Field("pilot_20261018", description="Active experiment profile identifier.")
    dataset_cohort: str = Field("pilot_october2026", description="Active dataset cohort.")
    production_ready: bool = Field(False, description="Whether model is certified for operational production (False).")


class ExperimentProfileInfo(BaseModel):
    """Summary of a frozen experiment profile available in the model registry."""
    profile_id: str = Field(..., description="Unique profile identifier (e.g. 'pilot_20261018', 'expanded_july2024').")
    display_name: str = Field(..., description="Human-readable title.")
    experiment_id: str = Field(..., description="Underlying experiment directory name.")
    dataset_cohort: str = Field(..., description="Dataset cohort tag.")
    protocol_id: str = Field(..., description="Protocol configuration file name.")
    task: str = Field("window_flare_detection", description="Task semantics (Task A: 60s window detection).")
    is_default: bool = Field(..., description="True if this is the default profile (strictly October 2026 pilot).")
    governance_status: str = Field(..., description="Governance status (PILOT_FROZEN, BENCHMARK_FROZEN).")
    production_ready: bool = Field(False, description="Production readiness guarantee (strictly False).")
    evaluation_window: str = Field(..., description="Evaluation observation window.")
    description: str = Field(..., description="Profile description.")
    limitations: str = Field(..., description="Specific documented scientific limitations.")
    false_alarm_rate_summary: Dict[str, Any] = Field(..., description="False alarm rate summary with units.")


class ModelInfoResponse(BaseModel):
    """Model metadata and governance specification."""
    model_name: str = Field(..., description="Estimator family (e.g. xgboost, logistic_regression).")
    model_class: str = Field(..., description="Concrete scikit-learn or XGBoost class name.")
    model_version: str = Field(..., description="Unambiguous, full model identifier with complete experiment ID.")
    experiment_id: str = Field(..., description="Cryptographically anchored experiment directory ID.")
    expected_features: List[str] = Field(..., description="Ordered list of required feature names.")
    feature_count: int = Field(..., description="Total number of features expected.")
    scaler: str = Field(..., description="Normalization scaler fitted on training partition.")
    imputer: str = Field(..., description="Missing-value strategy fitted on training partition.")
    forecast_horizon_seconds: Optional[float] = Field(
        None,
        deprecated=True,
        description="DEPRECATED: Models perform Task A 60-second window detection, not pre-flare forecasting.",
    )
    window_duration_seconds: float = Field(60.0, description="Duration of observation window evaluated in seconds.")
    task: str = Field("window_flare_detection", description="Model inference task (Task A: 60s window detection).")
    decision_d15_status: str = Field("PILOT", description="Dataset sample scale governance status.")
    profile_id: str = Field("pilot_20261018", description="Active experiment profile identifier.")
    dataset_cohort: str = Field("pilot_october2026", description="Dataset cohort used to train this model.")
    governance_status: str = Field("PILOT_FROZEN", description="Governance status of model artifacts.")
    production_ready: bool = Field(False, description="Production readiness guarantee (strictly False).")
    limitations: str = Field("", description="Documented research limitations.")
    false_alarm_rate_info: Optional[Dict[str, Any]] = Field(None, description="False-alarm rate metrics with units.")
    test_metrics: Optional[Dict[str, Any]] = Field(None, description="Held-out test set performance summary.")


class WindowFeaturesInput(BaseModel):
    """Pre-computed feature input for a single 60-second observation window."""
    mean: float = Field(..., description="Mean detector count rate across window.")
    std: float = Field(..., description="Standard deviation of count rate.")
    min: float = Field(..., description="Minimum observed count rate.")
    max: float = Field(..., description="Maximum observed count rate (peak flux).")
    median: float = Field(..., description="Median count rate.")
    iqr: float = Field(..., description="Interquartile range (p75 - p25).")
    p05: float = Field(..., description="5th percentile count rate.")
    p25: float = Field(..., description="25th percentile count rate.")
    p75: float = Field(..., description="75th percentile count rate.")
    p95: float = Field(..., description="95th percentile count rate.")
    temporal_slope: float = Field(..., description="Linear slope across full window (counts/s).")
    rolling_trend: float = Field(..., description="Linear slope across trailing 15 seconds (counts/s).")
    mean_abs_first_difference: float = Field(..., description="Mean absolute step-to-step derivative.")
    max_abs_first_difference: float = Field(..., description="Maximum impulsive single-step jump.")
    coverage_fraction: float = Field(1.0, description="Fraction of valid observed bins (0.0 to 1.0).")
    n_observed_samples: int = Field(60, description="Count of finite samples observed.")
    baseline_value: Optional[float] = Field(None, description="Local quiet-Sun background flux.")
    peak_to_baseline_ratio: Optional[float] = Field(None, description="Max counts divided by baseline.")
    robust_variability: Optional[float] = Field(None, description="MAD-based robust variability measure.")


class PredictionRequest(BaseModel):
    """Prediction request allowing either direct features or raw count rates."""
    features: Optional[Dict[str, float]] = Field(
        None,
        description="Dictionary of engineered feature key-value pairs matching model schema.",
        examples=[{
            "mean": 14.7, "std": 15.6, "min": 10.0, "max": 80.0, "median": 10.0,
            "iqr": 0.0, "p05": 10.0, "p25": 10.0, "p75": 10.0, "p95": 53.0,
            "temporal_slope": 0.47, "rolling_trend": 4.28, "mean_abs_first_difference": 1.85,
            "max_abs_first_difference": 35.0, "coverage_fraction": 1.0, "n_observed_samples": 60,
            "baseline_value": 10.0, "peak_to_baseline_ratio": 8.0, "robust_variability": 0.0,
        }],
    )
    counts: Optional[List[float]] = Field(
        None,
        description="Raw 1.0 s cadence count rate observations (minimum 10 samples, ideally 60).",
        examples=[[10.0] * 50 + [35.0, 50.0, 75.0, 80.0, 60.0, 45.0, 30.0, 20.0, 15.0, 10.0]],
    )
    timestamps: Optional[List[float]] = Field(
        None,
        description="Optional timestamps in UTC seconds corresponding to counts.",
    )
    threshold: Optional[float] = Field(0.50, description="Decision threshold for flare classification (0.0 to 1.0).")
    profile: Optional[str] = Field(
        None,
        description="Experiment profile name ('pilot_20261018' [default] or 'expanded_july2024').",
    )
    model_name: Optional[str] = Field(
        "xgboost",
        description="Model estimator identifier: 'xgboost', 'random_forest', 'logistic_regression'.",
    )


class PredictionResponse(BaseModel):
    """Structured response from the model prediction pipeline."""
    flare_detected: bool = Field(..., description="Binary detection: True if flare_probability >= threshold.")
    flare_probability: float = Field(..., description="Model predicted probability score for flare presence in 60s window [0.0, 1.0]. (Uncalibrated model score).")
    boundary_margin: float = Field(..., description="Normalized distance from decision boundary |P - 0.5| * 2.0 in [0.0, 1.0]. Represents classification margin, NOT statistical confidence or credible interval.")
    confidence: Optional[float] = Field(None, deprecated=True, description="DEPRECATED alias for boundary_margin. Does NOT represent Bayesian or frequentist statistical confidence.")
    risk_level: str = Field(..., description="Operational risk tier: LOW, MODERATE, HIGH, or SEVERE based on probability score.")
    expected_flare_class: Optional[str] = Field(
        "NOT_EVALUATED_BINARY_DETECTOR_ONLY",
        deprecated=True,
        description="DEPRECATED & UNAVAILABLE: Current models are binary flare detectors (flare vs quiet). Flare class classification requires a separately validated multi-class model and is not provided.",
    )
    threshold_used: float = Field(..., description="Decision threshold applied.")
    forecast_horizon_seconds: Optional[float] = Field(
        None,
        deprecated=True,
        description="DEPRECATED: Models perform Task A 60-second window detection, not pre-flare lead-time forecasting.",
    )
    window_duration_seconds: float = Field(60.0, description="Duration of observation window evaluated in seconds.")
    inference_timestamp_utc: str = Field(..., description="Server ISO 8601 UTC timestamp when inference was computed.")
    observation_timestamp_utc: Optional[str] = Field(None, description="Observation window start/epoch if provided in input; None if not provided (never fabricated).")
    prediction_timestamp_utc: Optional[str] = Field(None, deprecated=True, description="DEPRECATED alias for inference_timestamp_utc.")
    model_version: str = Field(..., description="Unambiguous, full model identifier with complete experiment ID (e.g. 'xgboost@exp_PROTO_STAGE10_PILOT_001_20261023_141429').")
    experiment_id: str = Field("exp_PROTO_STAGE10_PILOT_001_20261023_141429", description="Full experiment identifier.")
    extracted_features: Optional[Dict[str, float]] = Field(None, description="Features extracted if raw counts provided.")
    profile: str = Field("pilot_20261018", description="Active experiment profile identifier.")
    dataset_cohort: str = Field("pilot_october2026", description="Dataset cohort used to train this model.")
    task: str = Field("window_flare_detection", description="Model inference task (Task A: 60s window detection).")
    production_ready: bool = Field(False, description="Research benchmark status flag (strictly False).")
    advisory: str = Field(
        "RESEARCH BENCHMARK: Task A 60-second window flare detection. Not certified for operational space-weather alerting.",
        description="Operational use disclaimer.",
    )


class BatchPredictionRequest(BaseModel):
    """Batch prediction request for multiple observation windows."""
    windows: List[Dict[str, float]] = Field(..., description="List of feature dictionaries.")
    threshold: Optional[float] = Field(0.50, description="Decision threshold.")
    profile: Optional[str] = Field(None, description="Optional experiment profile ('pilot_20261018' or 'expanded_july2024').")
    model_name: Optional[str] = Field("xgboost", description="Model estimator identifier.")


class BatchPredictionResponse(BaseModel):
    """Batch prediction response containing multiple window inferences."""
    total_evaluated: int = Field(..., description="Count of evaluated windows.")
    flares_detected_count: int = Field(..., description="Count of windows with flare_detected=True.")
    max_probability: float = Field(..., description="Highest flaring probability observed across batch.")
    overall_risk_level: str = Field(..., description="Maximum operational risk level across batch.")
    profile: str = Field("pilot_20261018", description="Active experiment profile identifier.")
    dataset_cohort: str = Field("pilot_october2026", description="Active dataset cohort.")
    production_ready: bool = Field(False, description="Research benchmark status flag (strictly False).")
    predictions: List[PredictionResponse] = Field(..., description="Per-window predictions.")


class TimeSeriesPredictionRequest(BaseModel):
    """Continuous light-curve time-series prediction request."""
    counts: List[float] = Field(..., description="Continuous series of count rates at 1.0 s cadence.")
    times: Optional[List[float]] = Field(None, description="Optional observation timestamps.")
    window_length: int = Field(60, description="Sliding window size in seconds.")
    stride: int = Field(10, description="Window stride in seconds.")
    threshold: float = Field(0.50, description="Decision threshold.")
    profile: Optional[str] = Field(None, description="Optional experiment profile ('pilot_20261018' or 'expanded_july2024').")
    model_name: Optional[str] = Field("xgboost", description="Model estimator identifier.")


class TimeSeriesPredictionResponse(BaseModel):
    """Result of continuous time-series sliding window evaluation."""
    total_windows: int = Field(..., description="Total number of windows extracted and evaluated.")
    flares_detected: int = Field(..., description="Number of windows where flare was detected.")
    max_flare_probability: float = Field(..., description="Peak flare probability across entire time series.")
    peak_timestamp: Optional[float] = Field(None, description="Timestamp of highest flaring probability.")
    peak_risk_level: str = Field(..., description="Highest risk tier observed across series.")
    profile: str = Field("pilot_20261018", description="Active experiment profile identifier.")
    dataset_cohort: str = Field("pilot_october2026", description="Active dataset cohort.")
    production_ready: bool = Field(False, description="Research benchmark status flag (strictly False).")
    timeline: List[Dict[str, Any]] = Field(..., description="Time-series prediction coordinates for plotting.")
