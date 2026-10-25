"""FastAPI service for SOLARIS-A1 solar flare prediction platform.

Provides clean REST endpoints with Pydantic validation, CORS headers for external websites,
comprehensive OpenAPI documentation (/docs), and direct connection to the trained model pipeline.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd

from solar_flare.paths import project_root
from solar_flare.inference.pipeline import (
    InferencePipeline,
    get_default_pipeline,
    get_pipeline as get_pipeline_by_profile,
    classify_risk,
    EXPERIMENT_PROFILES,
    DEFAULT_PROFILE_ID,
)
from solar_flare.api.schemas import (
    HealthResponse,
    ModelInfoResponse,
    ExperimentProfileInfo,
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    TimeSeriesPredictionRequest,
    TimeSeriesPredictionResponse,
)

logger = logging.getLogger("solaris_a1.api")

_PIPELINE: Optional[InferencePipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cache the model inference pipeline upon service startup."""
    global _PIPELINE
    try:
        # Strictly initialize default October 2026 pilot pipeline
        _PIPELINE = get_default_pipeline()
        logger.info("FastAPI service successfully loaded default pilot model: %s", _PIPELINE.version_info)
    except Exception as exc:
        logger.error("Failed to initialize inference pipeline on startup: %s", exc)
        _PIPELINE = None
    yield


app = FastAPI(
    title="SOLARIS-A1 Space-Weather Flare Prediction API",
    description=(
        "Research-grade machine learning prediction API for solar flare detection and pre-flare "
        "activity analysis using Aditya-L1 SoLEXS Level-1 observations. "
        "Provides calibrated flaring probabilities, risk tiering, and time-series evaluation. "
        "NOTICE: Research benchmark only. Does not guarantee operational space-weather alerting."
    ),
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS for external developer integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def resolve_pipeline(profile: Optional[str] = None, model_name: str = "xgboost") -> InferencePipeline:
    """Retrieve active pipeline for requested profile and model family.
    
    The October 2026 pilot MUST remain the default when profile is omitted or None.
    """
    target_prof = profile or DEFAULT_PROFILE_ID
    try:
        return get_pipeline_by_profile(target_prof, model_name=model_name)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model inference pipeline is not available for profile '{target_prof}': {exc}",
        )


def get_pipeline() -> InferencePipeline:
    """Helper to retrieve default October 2026 pilot inference pipeline or raise 503."""
    return resolve_pipeline(DEFAULT_PROFILE_ID, "xgboost")


@app.get("/", summary="API Root", tags=["System"])
async def root_endpoint() -> Dict[str, Any]:
    """Return platform metadata, service health, and documentation links."""
    pipeline = get_pipeline()
    v = pipeline.version_info
    return {
        "service": "SOLARIS-A1 Solar Flare Prediction API",
        "instrument": "Aditya-L1 SoLEXS (Level-1 Science)",
        "status": "OPERATIONAL",
        "version": "1.1.0",
        "default_profile": v["profile_id"],
        "active_model": v["model_name"],
        "model_version": v["experiment_id"],
        "dataset_cohort": v["dataset_cohort"],
        "production_ready": False,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "health": "/health",
            "models": "/models",
            "model_info": "/model/info",
            "predict": "/predict",
            "predict_batch": "/predict/batch",
            "predict_timeseries": "/predict/timeseries",
            "latest_observations": "/observations/latest",
            "heldout_metrics": "/metrics/heldout",
        },
    }


@app.get("/health", response_model=HealthResponse, summary="Health Check", tags=["System"])
async def health_check() -> HealthResponse:
    """Check system operational status and model readiness."""
    pipeline = get_pipeline()
    v = pipeline.version_info
    return HealthResponse(
        status="healthy",
        model_loaded=True,
        model_name=v["model_name"],
        model_version=f"{v['model_name']}@{v['experiment_id']}",
        service_timestamp_utc=datetime.now(timezone.utc).isoformat(),
        profile=v["profile_id"],
        dataset_cohort=v["dataset_cohort"],
        production_ready=False,
    )


@app.get("/models", response_model=List[ExperimentProfileInfo], summary="Available Experiment Profiles", tags=["Model"])
async def list_models() -> List[ExperimentProfileInfo]:
    """Return all available frozen experiment profiles in the SOLARIS-A1 model registry."""
    profiles_list = []
    for prof in EXPERIMENT_PROFILES.values():
        profiles_list.append(
            ExperimentProfileInfo(
                profile_id=prof.profile_id,
                display_name=prof.display_name,
                experiment_id=prof.experiment_id,
                dataset_cohort=prof.dataset_cohort,
                protocol_id=prof.protocol_id,
                task=prof.task,
                is_default=prof.is_default,
                governance_status=prof.governance_status,
                production_ready=False,
                evaluation_window=prof.evaluation_window,
                description=prof.description,
                limitations=prof.limitations,
                false_alarm_rate_summary=prof.false_alarm_rate_summary,
            )
        )
    return profiles_list


@app.get("/model/info", response_model=ModelInfoResponse, summary="Model Metadata & Governance", tags=["Model"])
async def model_info(profile: Optional[str] = None, model_name: str = "xgboost") -> ModelInfoResponse:
    """Retrieve full model specifications, feature definitions, and test performance.
    
    If `profile` is omitted, defaults strictly to the October 2026 pilot baseline.
    """
    pipeline = resolve_pipeline(profile, model_name=model_name)
    v = pipeline.version_info

    metrics_summary: Optional[Dict[str, Any]] = None
    if pipeline.metrics_df is not None and not pipeline.metrics_df.empty:
        m_rows = pipeline.metrics_df[pipeline.metrics_df["model_name"] == v["model_name"]]
        if not m_rows.empty:
            metrics_summary = m_rows.iloc[0].to_dict()

    prof_meta = EXPERIMENT_PROFILES.get(v["profile_id"])
    far_info = prof_meta.false_alarm_rate_summary if prof_meta else None

    return ModelInfoResponse(
        model_name=v["model_name"],
        model_class=v["model_class"],
        model_version=f"{v['model_name']}@{v['experiment_id']}",
        experiment_id=v["experiment_id"],
        expected_features=v["expected_features"],
        feature_count=v["features_count"],
        scaler=v["scaler"],
        imputer=v["imputer"],
        forecast_horizon_seconds=v["forecast_horizon_seconds"],
        window_duration_seconds=v["window_duration_seconds"],
        task=v["task"],
        decision_d15_status="PILOT" if v["profile_id"] == "pilot_20261018" else "EXPANDED_BENCHMARK",
        profile_id=v["profile_id"],
        dataset_cohort=v["dataset_cohort"],
        governance_status=v["governance_status"],
        production_ready=False,
        limitations=v["limitations"],
        false_alarm_rate_info=far_info,
        test_metrics=metrics_summary,
    )


@app.post("/predict", response_model=PredictionResponse, summary="Predict Single Observation Window", tags=["Inference"])
async def predict_single(req: PredictionRequest) -> PredictionResponse:
    """Predict solar flare probability for a single observation window.
    
    Accepts either:
    1. A dictionary of pre-computed `features` matching the model schema.
    2. A list of raw `counts` (detector count rates) at 1.0 s cadence from which features are extracted dynamically.
    Optional `profile` selects the experiment profile (defaults to October 2026 pilot).
    """
    pipeline = resolve_pipeline(req.profile, model_name=req.model_name or "xgboost")

    if req.features is not None:
        try:
            preds = pipeline.predict(req.features, threshold=req.threshold or 0.50)
            return PredictionResponse(**preds[0])
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Inference failed on provided features: {exc}",
            )
    elif req.counts is not None:
        if len(req.counts) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Count array must contain at least 10 samples (received {len(req.counts)}).",
            )
        try:
            res = pipeline.predict_from_counts(
                counts=req.counts,
                times=req.timestamps,
                threshold=req.threshold or 0.50,
            )
            return PredictionResponse(**res)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Feature extraction or inference failed on raw count array: {exc}",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'features' dictionary or 'counts' list must be provided.",
        )


@app.post("/predict/batch", response_model=BatchPredictionResponse, summary="Batch Window Predictions", tags=["Inference"])
async def predict_batch(req: BatchPredictionRequest) -> BatchPredictionResponse:
    """Predict flare probabilities for a batch of feature windows."""
    pipeline = resolve_pipeline(req.profile, model_name=req.model_name or "xgboost")
    if not req.windows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Windows list cannot be empty.",
        )

    try:
        preds = pipeline.predict(req.windows, threshold=req.threshold or 0.50)
        res_list = [PredictionResponse(**p) for p in preds]

        probs = [p.flare_probability for p in res_list]
        max_p = max(probs) if probs else 0.0
        flares_count = sum(1 for p in res_list if p.flare_detected)

        return BatchPredictionResponse(
            total_evaluated=len(res_list),
            flares_detected_count=flares_count,
            max_probability=round(max_p, 4),
            overall_risk_level=classify_risk(max_p),
            profile=pipeline.version_info["profile_id"],
            dataset_cohort=pipeline.version_info["dataset_cohort"],
            production_ready=False,
            predictions=res_list,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch prediction failed: {exc}",
        )


@app.post("/predict/timeseries", response_model=TimeSeriesPredictionResponse, summary="Sliding Window Light-Curve Evaluation", tags=["Inference"])
async def predict_timeseries(req: TimeSeriesPredictionRequest) -> TimeSeriesPredictionResponse:
    """Extract sliding windows across a continuous count rate time-series and return prediction timeline."""
    pipeline = resolve_pipeline(req.profile, model_name=req.model_name or "xgboost")
    counts = np.asarray(req.counts, dtype=np.float64)
    w_len = req.window_length
    stride = req.stride

    if len(counts) < w_len:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Time-series length ({len(counts)}) must be >= window length ({w_len}).",
        )

    times = np.asarray(req.times, dtype=np.float64) if req.times is not None else np.arange(len(counts), dtype=np.float64)

    timeline = []
    max_prob = 0.0
    peak_t = None
    flares_detected = 0

    # Slide window
    for start_idx in range(0, len(counts) - w_len + 1, stride):
        end_idx = start_idx + w_len
        w_counts = counts[start_idx:end_idx]
        w_times = times[start_idx:end_idx]

        try:
            res = pipeline.predict_from_counts(
                counts=w_counts,
                times=w_times,
                threshold=req.threshold,
            )
            p = res["flare_probability"]
            is_f = res["flare_detected"]
            if is_f:
                flares_detected += 1
            if p > max_prob:
                max_prob = p
                peak_t = float(w_times[-1])

            timeline.append({
                "window_start": float(w_times[0]),
                "window_end": float(w_times[-1]),
                "flare_probability": p,
                "flare_detected": is_f,
                "risk_level": res["risk_level"],
                "expected_flare_class": res["expected_flare_class"],
            })
        except Exception:
            continue

    return TimeSeriesPredictionResponse(
        total_windows=len(timeline),
        flares_detected=flares_detected,
        max_flare_probability=round(max_prob, 4),
        peak_timestamp=peak_t,
        peak_risk_level=classify_risk(max_prob),
        profile=pipeline.version_info["profile_id"],
        dataset_cohort=pipeline.version_info["dataset_cohort"],
        production_ready=False,
        timeline=timeline,
    )


@app.get("/observations/latest", summary="Latest Observation Status", tags=["Data"])
async def latest_observation_status() -> Dict[str, Any]:
    """Retrieve metadata and science status of the latest available SoLEXS Level-1 observation."""
    root = project_root()
    manifest_file = root / "data" / "manifests" / "manifest.csv"
    if not manifest_file.is_file():
        raise HTTPException(status_code=404, detail="Data manifest not found")

    df_man = pd.read_csv(manifest_file)
    lc_rows = df_man[df_man["file_type"] == "LIGHTCURVE"]
    if lc_rows.empty:
        raise HTTPException(status_code=404, detail="No light-curve files found in manifest")

    latest_file = lc_rows.iloc[-1]
    return {
        "observation_id": str(latest_file.get("observation_id")),
        "file_name": str(latest_file.get("file_name")),
        "start_time_utc": str(latest_file.get("start_time_as_displayed")),
        "end_time_utc": str(latest_file.get("end_time_as_displayed")),
        "instrument": "Aditya-L1 SoLEXS SDD2",
        "data_level": "Level-1",
        "cadence_seconds": 1.0,
        "gti_pairing": str(latest_file.get("paired_gti_file")),
        "pairing_verified": str(latest_file.get("pairing_verified")),
        "data_status": "HISTORICAL_SCIENCE_ARCHIVE",
        "is_live_stream": False,
        "note": "Official Level-1 PRADAN science observation from Aditya-L1 SoLEXS.",
    }


@app.get("/metrics/heldout", summary="Held-Out Test Set Metrics", tags=["Model"])
async def held_out_metrics(profile: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return the complete table of scientific evaluation metrics calculated on the sealed test set."""
    pipeline = resolve_pipeline(profile)
    if pipeline.metrics_df is None or pipeline.metrics_df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation metrics table not found for profile '{pipeline.version_info['profile_id']}'.",
        )
    return pipeline.metrics_df.to_dict(orient="records")


@app.get("/predictions/history", summary="Recent Prediction History", tags=["Inference"])
async def prediction_history() -> List[Dict[str, Any]]:
    """Return in-memory history of recent model inferences."""
    pipeline = get_pipeline()
    return pipeline.history
