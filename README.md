# SOLARIS-A1: Machine Learning Solar Flare Detection Platform

- **Full Title:** Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations
- **Permanent Project Identifier:** `SOLARIS-A1`
- **License:** MIT (Code) / Research Benchmark Data Sharing Guidelines (Data & Models)
- **Spacecraft & Instrument:** ISRO Aditya-L1 · Solar Low Energy X-ray Spectrometer (SoLEXS, 1.0–22.0 keV)
- **Ground Truth Authority:** NOAA SWPC / NCEI GOES-16 Level-2 Solar Event Reports

---

## 1. Executive Summary & Research Mission

**SOLARIS-A1** is a heliophysics machine learning research platform developed to analyze full-disk soft X-ray light curves (1.0–22.0 keV) from the **Solar Low Energy X-ray Spectrometer (SoLEXS)** onboard India's flagship solar observatory, **Aditya-L1**, positioned at the Sun-Earth Lagrangian point L1.

The project evaluates two distinct scientific objectives:
1. **Task A — 60-Second In-Window Solar Flare Detection (Operational Capability):**
   Determines whether soft X-ray count rate sequences across a 60-second sliding observation window ($W = 60\text{ s}$, stride $S = 10\text{ s}$) exhibit impulsive flaring activity ($\ge \text{C1.0}$) confirmed by independent NOAA GOES event records.
2. **Task B — Pre-Flare Activity Analysis & Forecasting (Archived Negative Result):**
   Evaluates whether single-channel full-disk soft X-ray time series contain physical precursor signatures capable of predicting solar flare onsets across 5-, 10-, or 30-minute advance horizons prior to impulsive reconnection.

> [!IMPORTANT]
> **Scientific Integrity & Scope Notice:**
> - **Task A (Detection)** is verified, high-performance, and operational: achieves **98.15% event-level sensitivity** across 45 held-out test days with an operational false alarm rate of **6.42 FP/hr**.
> - **Task B (Forecasting)** is a rigorous **Negative Result**: disk-integrated soft X-rays emit predominantly *after* magnetic reconnection during thermal plasma cooling; pre-flare forecasting fails to achieve operational reliability ($F_1 \le 0.20$, high false alarm volumes). In accordance with scientific research governance, Task B forecasting has been quarantined from the public dashboard interface and preserved strictly in the offline research archive (`docs/27_task_b_forecasting_negative_result.md`).
> - **Research Benchmark Only:** All models are evaluated under scientific benchmark protocols and are **NOT certified for operational space-weather alerting or mission-critical spacecraft protection**.

---

## 2. Model Registry & Runtime Profiles

SOLARIS-A1 maintains three distinct generations of trained model artifacts:

| Model Profile ID | Experiment ID | Dataset Cohort | Training Range | Evaluation Performance (Test Set) | Operational Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`pilot_20261018`** *(Default)* | `exp_PROTO_STAGE10_PILOT_001_20261023_141429` | October 2026 Pilot | 2026-10-18 (Orbit 1) | Precision: **1.000**, Recall: **0.750**, F1: **0.8571**, FA: **0.00/hr** | **Active Default (UI & API)** |
| **`expanded_july2024`** | `exp_PROTO_STAGE10_EXPANDED_002_20261023_162431` | July 2024 Benchmark | 2024-07-01 to 2024-07-12 | Precision: **0.350**, Recall: **0.901**, F1: **0.5041**, FA: **118.85/hr** | Active Region Benchmark |
| **`expanded_2024_2026`** | `exp_PROTO_STAGE16_EXPANDED_2024_2026` | Multi-Year Expanded | 2024-02-12 to 2026-06-28 | Precision: **0.599**, Recall: **0.478**, F1: **0.5315**, FA: **6.42/hr**, **98.15% Event Recall** | Scaled Research Model |

### Understanding the Model Generations
- **Why is the Pilot Baseline the Default?** The October 2026 pilot represents the frozen, audited baseline (Decision D-15). It executes rapidly and provides clean baseline demonstration on Level-1 telemetry.
- **Why Did July 2024 Suffer Elevated False Alarms?** The held-out test set for July 2024 covers strictly July 13–14, 2024, which was overwhelmingly dominated by super-active region **AR3738**. Pre-flare coronal heating caused tree-based models to trigger 118.85 false alarms/hour.
- **How Did the Expanded 2024–2026 Model Solve This?** Trained across 231 observation days spanning quiet-Sun and peak solar cycle phases, the expanded model achieved an **~85% reduction in operational false alarms** (down to 6.42 FA/hr) while capturing **159 out of 162 independent NOAA flare events (98.15%)** on 45 held-out test days.

---

## 3. Quick Start & Execution Guide

### 3.1 Environment Setup (Windows PowerShell / macOS / Linux)

```powershell
# 1. Clone repository
git clone https://github.com/<org>/SOLARIS-A1.git
cd SOLARIS-A1

# 2. Create Python 3.10+ virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows PowerShell:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# 4. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. Install package in editable development mode
pip install -e .
```

### 3.2 Run Automated Test Suites
```powershell
# Execute 253 comprehensive unit and integration tests
pytest -q
```

### 3.3 Launch Interactive Scientific Dashboard
```powershell
# Launch Streamlit observatory dashboard on port 8501
streamlit run dashboard/app.py --server.port 8501
```
Open **[http://localhost:8501](http://localhost:8501)** to access:
- **Observatory Home:** Satellite telemetry overview, Sun video, observation light curves, and verified event context.
- **Interactive Inference Lab (`/Live_Inference`):** Select historical SoLEXS observation windows to evaluate model detections against authoritative NOAA ground truth.
- **Model Results (`/Model_Results`):** Protocol-governed single-shot test set evaluation metrics, confusion matrices, and false-alarm trade-offs.
- **Dataset & Quality Browsers:** FITS HDU inspection, GTI duty cycle validation, and causal feature distributions.

### 3.4 Launch FastAPI REST Prediction Server
```powershell
# Start production-grade Uvicorn ASGI server on port 8000
uvicorn solar_flare.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Open **[http://localhost:8000/docs](http://localhost:8000/docs)** for interactive OpenAPI Swagger documentation:
- `GET /health` — Operational status and model readiness.
- `GET /models` — Available frozen experiment profiles in the model registry.
- `GET /model/info` — Deep model specifications, feature lists, and test metrics.
- `POST /predict` — Single 60-second window prediction (from features or raw counts).
- `POST /predict/batch` — High-throughput batch inference.
- `POST /predict/timeseries` — Sliding window inference over continuous light curves.

---

## 4. System Architecture & Zero-Leakage Pipeline

```
[Raw Aditya-L1 SoLEXS FITS]
           │
           ▼
[GTI Boundary Enforcement] ──► Exclude telemetry dropouts & anomalous flags
           │
           ▼
[Continuous Segmentation]  ──► Non-destructive, zero-interpolation segments
           │
           ▼
[Sliding Window Engine]    ──► W = 60s, S = 10s strictly within segments
           │
           ▼
[Causal Feature Registry]  ──► 19 physical summary, trend, and variability features
           │
           ▼
[Chronological Splitting]  ──► Strict temporal partitions + 300s embargo buffers
           │
           ▼
[Training-Only Preproc]    ──► Median imputation + RobustScaler fitted ON TRAIN ONLY
           │
           ▼
[Model Inference Engine]   ──► XGBoost / RF / Logistic Regression probabilistic scoring
           │
           ▼
[Dual Delivery Layer]      ──► Streamlit Observatory Dashboard & FastAPI REST Service
```

### Key Engineering Safeguards
1. **Zero Raw Mutation:** Raw telemetry files under `data/raw/` are strictly read-only and verified via SHA-256 chunked hashing. Real data is never interpolated or gap-filled.
2. **Zero Temporal Leakage:** Sliding windows never cross Good Time Interval (GTI) boundaries. Sliding window stride ($S=10\text{ s}$) produces overlapping samples; therefore, all train/validation/test splits are strictly **chronological** with 300-second embargo buffers.
3. **Training-Only Preprocessing:** Imputers and scalers are fitted exclusively on training data and frozen before transforming validation or test partitions.
4. **Cryptographic Test Set Sealing:** Held-out test sets are hashed and locked prior to model tuning. Model selection is performed strictly on validation partitions.

---

## 5. Data Provenance & Acquisition Guidance

### 5.1 Aditya-L1 SoLEXS Instrument
The **Solar Low Energy X-ray Spectrometer (SoLEXS)** is an instrument onboard the ISRO Aditya-L1 spacecraft designed to monitor soft X-ray emission from the solar corona across the 1.0–22.0 keV spectral band using Silicon Drift Detectors (SDD1 and SDD2).

### 5.2 Official Data Retrieval Protocol
Due to redistribution policies, raw Level-1 telemetry files are not bundled directly inside the Git repository. To download official datasets:
1. Register and log in to the **ISRO ISSDC PRADAN portal** ([https://pradan.issdc.gov.in](https://pradan.issdc.gov.in)).
2. Navigate to **Aditya-L1 $\to$ SoLEXS $\to$ Level-1 Science Data**.
3. Download matched Light Curve (`.lc.gz`) and Good Time Interval (`.gti.gz`) files.
4. Place raw files into `data/raw/` and verify pairing using:
   ```powershell
   python scripts/check_manifest.py data/manifests/manifest.csv
   ```
Detailed instructions are provided in [`docs/data_acquisition.md`](docs/data_acquisition.md).

### 5.3 Ground-Truth Flare Event Records
Independent ground-truth flare events are cross-matched against official **NOAA Space Weather Prediction Center (SWPC)** and **NOAA NCEI GOES-16 Level-2 XRS** solar event summaries. Ground-truth records are curated in:
- Pilot Events: [`data/manifests/event_records_approved_pilot.csv`](data/manifests/event_records_approved_pilot.csv)
- July 2024 Benchmark: [`data/manifests/event_records_approved.csv`](data/manifests/event_records_approved.csv)
- Expanded 2024–2026 Catalog: [`data/manifests/event_records_approved_expanded_2024_2026.csv`](data/manifests/event_records_approved_expanded_2024_2026.csv)

---

## 6. Project Directory Layout

```text
SOLARIS-A1/
├── README.md                      # Primary project overview, setup, and scientific guide
├── pyproject.toml                 # Package build metadata & pytest configuration
├── requirements.txt               # Pinned core runtime dependencies
├── requirements-dev.txt           # Testing and development dependencies
├── .gitignore                     # Git rules (excludes virtualenvs, scratch, large matrices)
├── config/                        # Experiment configurations and governance logs
│   ├── default.yaml               # Default system parameters
│   ├── column_roles.yaml          # FITS column role specifications
│   ├── decisions.yaml             # Scientific and architectural decision register
│   ├── training_protocol.yaml     # Pilot experiment training protocol
│   └── training_protocol_july2024.yaml # July 2024 benchmark protocol
├── dashboard/                     # Streamlit scientific dashboard
│   ├── app.py                     # Main dashboard entrypoint (Observatory Home)
│   ├── loaders.py                 # Pure functional artifact loaders
│   ├── components/                # Space-weather theme, banner, and plotting components
│   └── pages/                     # Dedicated analytical pages (1_Overview to 9_Spectral)
├── data/
│   ├── raw/                       # Raw Level-1 SoLEXS FITS files (external / read-only)
│   ├── manifests/                 # Official manifests and approved event catalogs
│   └── processed/                 # Exported feature matrices (generated offline)
├── docs/                          # Comprehensive technical and scientific documentation
│   ├── 00_requirements.md         # Requirements, scope, and responsibility split
│   ├── 01_decision_log.md         # Full architectural decision log (D-01 to D-15)
│   ├── 02_roadmap.md              # 17-stage implementation roadmap
│   ├── 03_architecture.md         # Layered architecture and pipeline contracts
│   ├── 11_feature_dictionary.md   # Mathematical definitions of 19 causal features
│   ├── 14_training_protocol.md    # Partitioning, leakage guards, and sealing rules
│   ├── 20_limitations.md          # Physical, instrumental, and observational limitations
│   ├── 27_task_b_forecasting_negative_result.md # Task B negative result evaluation
│   ├── model_card.md              # Official ML model card for champion XGBoost detector
│   └── setup_windows.md           # Step-by-step PowerShell setup instructions
├── results/                       # Verification reports, quality audits, and models
│   ├── FINAL_PRE_GITHUB_AUDIT.md  # Comprehensive pre-publication scientific audit
│   ├── experiments/               # Frozen experiment runs, sealed splits, and model weights
│   ├── forecasting/               # Archived Task B forecasting experiments
│   └── inventory/                 # FITS HDU inspection reports and statistics
├── scripts/                       # Command-line tools for processing and training
│   ├── inspect_fits.py            # Non-destructive FITS inspection utility
│   ├── run_quality.py             # Pure functional data quality assessment
│   ├── build_features.py          # 60s sliding window feature extractor
│   ├── train_expanded_models.py   # Multi-year expanded model training engine
│   └── run_task_b_forecasting.py  # Task B precursor and forecasting benchmark runner
├── src/
│   └── solar_flare/               # Core Python package
│       ├── api/                   # FastAPI service routers, schemas, and endpoints
│       ├── inference/             # InferencePipeline and Model Registry
│       ├── features/              # Causal feature registry and baseline calculators
│       ├── quality/               # Non-destructive quality audit engines
│       ├── segmentation/          # GTI-aware continuous observation segmenter
│       └── paths.py               # Repository-anchored portable path resolver
└── tests/                         # Automated unit, integration, and guard test suites
```

---

## 7. Citation & Attribution

If you utilize SOLARIS-A1, its pre-trained models, or its benchmark methodologies in your research, please cite:

```bibtex
@software{solaris_a1_2026,
  author       = {Melvin and SOLARIS-A1 Heliophysics & ML Research Group},
  title        = {{SOLARIS-A1: Machine Learning Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations}},
  year         = {2026},
  publisher    = {GitHub},
  howpublished = {\url{https://github.com/<org>/SOLARIS-A1}}
}
```

### Data Acknowledgments
- **ISRO ISSDC:** Indian Space Research Organisation for providing Aditya-L1 SoLEXS Level-1 data via the PRADAN portal.
- **NOAA SWPC & NCEI:** National Oceanic and Atmospheric Administration for independent GOES-16 XRS solar event reports.
