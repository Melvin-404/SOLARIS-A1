# SOLARIS-A1 Streamlit Dashboard Architecture & Governance (Stage 12)

**Document ID:** `DOC-16-DASHBOARD-FOUNDATION`  
**Milestone:** Stage 12 — Streamlit Dashboard Foundation  
**Governance Status:** Standardized Scientific Presentation Framework  

---

## 1. Purpose and Philosophy

The SOLARIS-A1 Streamlit Dashboard provides a local, interactive research visualization and inspection portal for Aditya-L1 SoLEXS Level-1 solar X-ray observations, data quality assessments, exploratory burst candidates, feature engineering, and model evaluation metrics.

### Core Architectural Axioms
1. **Strict Read-Only Operation:** The dashboard never writes, alters, creates, or deletes any file in `data/raw/`, `data/processed/`, or `results/`.
2. **Zero Computation / Training:** The dashboard does **not** train machine learning models, does **not** execute pipeline steps on button clicks, and does **not** tune hyperparameters. All numbers displayed are read strictly from pre-computed, verified disk artifacts.
3. **Transparent Scientific Status:** A polished UI does not establish scientific validity. Every page explicitly flags the status of its underlying data:
   - `PROVISIONAL`: Parameter or threshold awaiting formal human approval at a designated gate.
   - `PILOT`: Single observation day analysis (2026-10-18); does not establish general detector performance under Decision D-15.
   - `CANDIDATE — UNVERIFIED`: Heuristic statistical burst detections that are strictly **not** verified flare labels.
   - `MISSING` / `EMPTY`: Unambiguous display when an artifact has not yet been produced.
   - `ERROR`: Unparseable or malformed files are reported with actionable diagnostic details without crashing the application.
4. **Persistent Governance Disclaimer:** The sidebar permanently displays:
   > *"Candidate bursts are not verified solar flares. Pilot and provisional results are not validated detector performance."*

---

## 2. Multipage Application Structure

The dashboard is structured into 8 modular pages under `dashboard/`:

```text
dashboard/
├── app.py                      # Main entrypoint: task separation framing & artifact readiness
├── loaders.py                  # Standardized, read-only LoadResult data extraction functions
├── components/                 # Reusable UI presentation components
│   ├── __init__.py
│   ├── banner.py               # Status alerts (PROVISIONAL, PILOT, UNVERIFIED, MISSING)
│   ├── figures.py              # Interactive Plotly light-curve & histogram builders
│   └── tables.py               # Standardized dataframes and metric cards
└── pages/
    ├── 1_Overview.py           # Stage progress, inventory summary, open scientific questions
    ├── 2_Dataset.py            # Manifest checksum status, channel pairing, SDD1 empty GTI notice
    ├── 3_Data_Quality.py       # Quality summary table, per-file diagnostics, and 4 quality figures
    ├── 4_Light_Curves.py       # Interactive time series viewer, GTI shading, 0/NaN sample flags
    ├── 5_Events.py             # Candidate burst table vs. Gate G3 approved ground truth
    ├── 6_Features.py           # Window index browser, feature histograms, leakage warning
    └── 7_Model_Results.py      # Validation-only tuning results & single-shot sealed test evaluation
```

---

## 3. Page Details & Data Sources

| Page | Primary Data Sources | Handled Empty/Provisional State |
| :--- | :--- | :--- |
| **App (Home)** | `results/inventory/inventory.csv`, `docs/08_labelling_policy.md`, `config/decisions.yaml` | Displays readiness checklist and flags if policy is DRAFT |
| **1. Overview** | `results/inventory/inventory.csv`, `results/inventory/open_questions.md` | Informs user if inventory or questions document is missing |
| **2. Dataset** | `data/manifests/manifest.csv`, `results/inventory/inventory.csv` | Explicitly warns: `GTI EMPTY FOR THIS OBSERVATION` for SDD1 |
| **3. Quality** | `results/quality/summary.csv`, `results/quality/<stem>/quality.md`, PNG figures | Prominently displays `PROVISIONAL pending Gate G1/G2` banner |
| **4. Light Curves** | `data/raw/<stem>.lc.gz`, `data/raw/<stem>.gti.gz` | Displays downsampling notice when samples exceed 12,000 |
| **5. Events** | `results/eda/candidate_bursts.csv`, `data/manifests/event_records_approved.csv` | Every candidate row is labelled `CANDIDATE — UNVERIFIED` |
| **6. Features** | `data/processed/features/<stem>/window_index.csv`, `features.csv` | Displays prominent 83.3% window overlap leakage warning |
| **7. Model Results**| `results/experiments/<id>/` (trials, reports, metrics, lock) | Displays `VALIDATION ONLY` for tuning; refuses test display if lock unverified |

---

## 4. What the Dashboard Does NOT Do (Prohibited Behaviors)

1. **No Data Modification:** Never writes or overwrites raw FITS files, CSV tables, or JSON records.
2. **No On-Demand Training:** Never imports model estimators to train on the fly.
3. **No Unattested Metrics:** Never displays a classification score, F1, or PR-AUC that was not loaded directly from a valid, verified artifact.
4. **No Circularity:** Never presents Stage 5 candidate burst intervals as flare labels.
5. **No Cloud or External Connections:** Runs 100% locally and offline without external telemetry.

---

## 5. Local Execution Instructions

To run the Streamlit dashboard on Windows:
```powershell
# Activate local virtual environment
.\.venv\Scripts\Activate.ps1

# Launch Streamlit local server
python -m streamlit run dashboard/app.py
```
By default, the server launches locally at `http://localhost:8501`.
