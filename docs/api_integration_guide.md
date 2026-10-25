# SOLARIS-A1 REST API: Website Developer Integration Guide

**API Version:** `1.0.0`  
**Base URL (Local):** `http://127.0.0.1:8000`  
**Interactive Swagger UI:** `http://127.0.0.1:8000/docs`  
**OpenAPI Specification:** `http://127.0.0.1:8000/openapi.json`  

---

## 1. Quick Start: Launching the Backend and Frontend

### Step 1: Start the FastAPI Backend Service
From the repository root, start the Uvicorn server:
```bash
# Windows PowerShell
.venv\Scripts\python -m uvicorn solar_flare.api.main:app --host 127.0.0.1 --port 8000 --reload
```
Once launched, verify health:
```bash
curl -X GET http://127.0.0.1:8000/health
```

### Step 2: Start the Streamlit Dashboard (Optional)
In a separate terminal:
```bash
# Windows PowerShell
.venv\Scripts\python -m streamlit run dashboard/app.py
```
Access the dashboard at `http://localhost:8501`.

---

## 2. API Endpoints Reference

### 2.1 Service Health
`GET /health`
Returns the status of the API service, active model loading state, and telemetry readiness.

#### Response (`200 OK`)
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-10-23T14:30:00Z",
  "model_loaded": true,
  "champion_model": "xgboost"
}
```

---

### 2.2 Model Metadata & Performance
`GET /model/info`
Returns architecture parameters, training protocol IDs, features consumed, and verification metrics.

#### Response (`200 OK`)
```json
{
  "model_name": "xgboost",
  "task": "detection",
  "experiment_id": "exp_PROTO_STAGE10_PILOT_001_20261023_141429",
  "protocol_id": "PROTO_STAGE10_PILOT_001",
  "features_required": [
    "mean_counts", "std_counts", "min_counts", "max_counts", "median_counts",
    "peak_to_baseline_ratio", "baseline_value", "skewness", "kurtosis",
    "rise_rate", "decay_rate", "count_gradient_max", "coverage_fraction",
    "flag_ratio", "duration_seconds", "hardness_ratio"
  ],
  "f1_score": 0.8571,
  "precision": 1.0,
  "recall": 0.75,
  "roc_auc": 0.999
}
```

---

### 2.3 Single Feature-Vector Prediction
`POST /predict`
Submit pre-computed physical features for single-window inference.

#### Request Body
```json
{
  "mean_counts": 2450.5,
  "std_counts": 420.2,
  "min_counts": 1820.0,
  "max_counts": 4120.0,
  "median_counts": 2350.0,
  "peak_to_baseline_ratio": 3.85,
  "baseline_value": 1070.0,
  "skewness": 1.45,
  "kurtosis": 2.10,
  "rise_rate": 45.2,
  "decay_rate": 0.012,
  "count_gradient_max": 180.5,
  "coverage_fraction": 1.0,
  "flag_ratio": 0.0,
  "duration_seconds": 60.0,
  "hardness_ratio": 0.18
}
```

#### Response (`200 OK`)
```json
{
  "model_name": "xgboost",
  "flare_probability": 0.8842,
  "is_flare": true,
  "risk_tier": "HIGH",
  "threshold_applied": 0.5,
  "inference_latency_ms": 0.62
}
```

---

### 2.4 Raw Time-Series Sequence Prediction
`POST /predict/timeseries`
Supply 10 to 60 raw 1-second photon counts. The backend automatically extracts all 16 physical features, computes rolling baselines, executes the preprocessor, and returns the model classification.

#### Request Body
```json
{
  "raw_counts": [
    1200.0, 1220.0, 1250.0, 1310.0, 1450.0, 1680.0, 2050.0, 2600.0,
    3100.0, 3650.0, 3900.0, 3950.0, 3800.0, 3600.0, 3400.0, 3200.0,
    3050.0, 2900.0, 2800.0, 2700.0, 2600.0, 2550.0, 2500.0, 2450.0
  ],
  "baseline_counts": 1150.0,
  "cadence_seconds": 1.0
}
```

#### Response (`200 OK`)
```json
{
  "model_name": "xgboost",
  "flare_probability": 0.9412,
  "is_flare": true,
  "risk_tier": "SEVERE",
  "threshold_applied": 0.5,
  "inference_latency_ms": 0.85,
  "features_extracted": {
    "mean_counts": 2686.67,
    "std_counts": 883.45,
    "min_counts": 1200.0,
    "max_counts": 3950.0,
    "median_counts": 2750.0,
    "peak_to_baseline_ratio": 3.43,
    "baseline_value": 1150.0,
    "skewness": -0.21,
    "kurtosis": -1.28,
    "rise_rate": 275.0,
    "decay_rate": 0.038,
    "count_gradient_max": 550.0,
    "coverage_fraction": 1.0,
    "flag_ratio": 0.0,
    "duration_seconds": 24.0,
    "hardness_ratio": 0.05
  }
}
```

---

### 2.5 Batch Predictions
`POST /predict/batch`
Score up to 10,000 feature windows in parallel.

#### Request Body
```json
{
  "instances": [
    { "mean_counts": 800.0, "std_counts": 25.0, "peak_to_baseline_ratio": 1.02, ... },
    { "mean_counts": 3400.0, "std_counts": 450.0, "peak_to_baseline_ratio": 4.10, ... }
  ]
}
```

---

### 2.6 Latest Observations & Held-Out Metrics
- `GET /observations/latest?limit=60`: Fetches real Level-1 observation stream window.
- `GET /metrics/heldout`: Returns official Stage 11 test set benchmark table comparing XGBoost, Logistic Regression, Random Forest, and Baselines.

---

## 3. Client Integration Code Examples

### 3.1 JavaScript / TypeScript (`fetch`)
```javascript
async function assessSolarFlareRisk(rawCounts, baseline = 1000.0) {
  try {
    const response = await fetch("http://127.0.0.1:8000/predict/timeseries", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        raw_counts: rawCounts,
        baseline_counts: baseline,
        cadence_seconds: 1.0,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log(`Flare Prob: ${(result.flare_probability * 100).toFixed(1)}% | Risk: ${result.risk_tier}`);
    return result;
  } catch (error) {
    console.error("Failed to query SOLARIS-A1 inference engine:", error);
    throw error;
  }
}
```

### 3.2 Python (`requests`)
```python
import requests

def query_solaris_model(features: dict) -> dict:
    url = "http://127.0.0.1:8000/predict"
    response = requests.post(url, json=features, timeout=5.0)
    response.raise_for_status()
    data = response.json()
    print(f"Prediction: {data['is_flare']} (p={data['flare_probability']:.4f}, tier={data['risk_tier']})")
    return data
```

### 3.3 cURL
```bash
curl -X POST "http://127.0.0.1:8000/predict/timeseries" \
     -H "Content-Type: application/json" \
     -d '{"raw_counts": [1000, 1100, 1500, 2500, 3800, 4200, 3900, 3100, 2400, 1800], "baseline_counts": 980.0}'
```

---

## 4. Risk Tier Definitions & UI Styling Recommendations

| Risk Tier | Probability Range | Badge CSS Hex | Recommended Action |
| :--- | :--- | :--- | :--- |
| **`LOW`** | $[0.00, 0.30)$ | `#3b82f6` (Cyan / Blue) | Normal solar monitoring. |
| **`MODERATE`** | $[0.30, 0.70)$ | `#f59e0b` (Amber / Yellow) | Sub-flare thermal rise; watch for active region emergence. |
| **`HIGH`** | $[0.70, 0.90)$ | `#f97316` (Orange) | Flare onset detected; trigger notification alerts. |
| **`SEVERE`** | $[0.90, 1.00]$ | `#ef4444` (Vibrant Red) | Major flare erupting; engage satellite instrument safeguard procedures. |
