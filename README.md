# SOLARIS-A1

## Project Title
**Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations**

**Permanent Project Identifier:** `SOLARIS-A1`

---

## Current Status
**Status:** `Stage 13 — Dashboard and Pipeline Integration (Lineage, Status & Integrity Verification Complete)`

Stage 13 connects the SOLARIS-A1 Streamlit presentation layer to real pipeline artifacts with rigorous schema validation, cryptographic SHA-256 lineage tracking, stale-artifact detection, and a pure functional status engine (`src/solar_flare/status.py`). The dashboard strictly inspects artifacts in read-only mode, displays pipeline status color-coded across all stages, surfaces configuration drift side-by-side, and is verified by automated AST architecture boundaries prohibiting model training or data mutation. See [`docs/17_integration.md`](docs/17_integration.md).

---

## Data Acquisition & Inspection

### 1. Data Acquisition
Download official Level-1 SoLEXS light-curve and GTI FITS files from the ISRO ISSDC PRADAN portal following [`docs/data_acquisition.md`](docs/data_acquisition.md). Record entries in [`data/manifests/manifest.csv`](data/manifests/manifest.csv) and verify disk consistency:
```powershell
python scripts/check_manifest.py data/manifests/manifest.csv
```

### 2. Inspect FITS Files
Extract FITS HDU structures, column metadata, time-system keywords, and numerical statistics without modifying raw files:
```powershell
python scripts/inspect_fits.py
```
This command generates:
- `results/inventory/inventory.csv` & `inventory.json`
- `results/inventory/inspection_report.md`
- `results/inventory/open_questions.md`

For interactive, visual inspection of light curves and headers in Jupyter, open [`notebooks/01_fits_inspection.ipynb`](notebooks/01_fits_inspection.ipynb).

---

## Windows Setup

To configure and verify the local Python environment on Windows, execute the following commands in PowerShell from the project root:

```powershell
# 1. Create the virtual environment
python -m venv .venv

# 2. Configure process-scoped script execution policy (if blocked by Windows security)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 3. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install runtime and development dependencies
python -m pip install -r requirements-dev.txt

# 6. Verify environment, packages, and configuration
python scripts/verify_environment.py

# 7. Run unit test suite
python -m pytest -v
```

> **PowerShell Execution Policy Note:** If Windows reports that running scripts is disabled (`PSSecurityException`), do not disable security globally. Instead, apply the process-level bypass shown above (`-Scope Process`), which grants execution permissions solely to the current terminal session without weakening system-wide security. See [`docs/setup_windows.md`](docs/setup_windows.md) for full troubleshooting.

---

## Project Structure
```text
SOLARIS-A1/
├── README.md                      # Project overview, status, and setup instructions
├── requirements.txt               # Pinned core runtime dependencies
├── requirements-dev.txt           # Development and testing dependencies
├── .gitignore                     # Git ignore rules (protects data, venv, logs)
├── pyproject.toml                 # Pytest pythonpath configuration and project metadata
├── config/
│   └── default.yaml               # Application configuration with pending scientific params
├── data/
│   ├── raw/                       # STRICTLY READ-ONLY: Real Level-1 SoLEXS FITS files
│   │   └── gti/                   # GTI storage subfolder (if categorized separately)
│   ├── processed/                 # Exported tabular feature matrices and labels
│   └── manifests/                 # Provenance logs and checksum manifests
│       ├── manifest.csv           # Active dataset manifest
│       └── manifest_template.csv  # Manifest schema template
├── docs/
│   ├── 00_requirements.md         # Requirements, scope, and responsibility split
│   ├── 01_decision_log.md         # Architectural and scientific decision register
│   ├── 02_roadmap.md              # 17-stage implementation roadmap
│   ├── 03_architecture.md         # System architecture and layer boundaries
│   ├── 03_inspection_methods.md   # FITS inspection methodology & interpretation guide
│   ├── setup_windows.md           # Windows setup and troubleshooting notes
│   └── data_acquisition.md        # Official PRADAN data access and pairing protocol
├── logs/                          # Application logs (rotating file logs)
├── notebooks/                     # Jupyter notebooks for EDA and student training
│   └── 01_fits_inspection.ipynb   # Interactive FITS inspection notebook
├── results/                       # Generated outputs and figures (gitignored)
│   └── inventory/                 # Generated inventory tables and inspection reports
├── scripts/
│   ├── verify_environment.py      # Automated environment and config diagnostic tool
│   ├── check_manifest.py          # Offline manifest and disk hash verification tool
│   └── inspect_fits.py            # FITS metadata inventory and inspection tool
├── src/
│   └── solar_flare/
│       ├── __init__.py            # Package metadata
│       ├── config.py              # YAML config loader with path resolution & validation
│       ├── logging_setup.py       # Idempotent console & rotating file logging
│       ├── manifest.py            # Manifest parsing, chunked SHA-256, and disk audit
│       ├── paths.py               # Repository-anchored path resolution utilities
│       └── inspection/            # FITS inspection subsystem
│           ├── __init__.py
│           ├── fits_inspect.py    # Non-destructive HDU, column, and statistics extraction
│           ├── time_systems.py    # Astronomical time keyword extraction and interpretation
│           └── inventory.py       # Tabular inventory builder with UNRESOLVED role flags
└── tests/
    ├── __init__.py                # Test package
    ├── test_config.py             # Config loading and error handling tests
    ├── test_inspection.py         # FITS inspection and immutability tests (synthetic fixtures)
    ├── test_logging.py            # Logging setup and idempotency tests
    ├── test_manifest.py           # Manifest loading, hashing, and pairing tests
    └── test_paths.py              # Path resolution unit tests
```

---

## Project Overview
`SOLARIS-A1` is an academic research project investigating machine learning methods for solar flare detection and pre-flare activity analysis using real Level-1 solar X-ray light-curve FITS files and corresponding Good Time Interval (GTI) FITS files from the Solar Low Energy X-ray Spectrometer (SoLEXS) onboard India's Aditya-L1 mission (archived at the official ISRO/ISSDC PRADAN portal).

The project is structured into two distinct scientific tasks:
- **Task A (Solar Flare Detection):** Determine whether solar flare activity occurs within a defined observation window using independently verified ground-truth event labels.
- **Task B (Pre-Flare Prediction / Forecasting):** A separate forecasting experiment evaluating whether light-curve characteristics prior to a prediction epoch are informative of a future flare occurring within a defined horizon, strictly avoiding temporal leakage from active flare onset.

---

## Division of Responsibilities
- **Antigravity (Automated IDE Assistant):** Implements project structure, environment configuration, data ingestion, GTI-aware preprocessing, exploratory analysis, labelling infrastructure, segmentation, windowing, feature engineering, dataset export, baseline detectors, evaluation harnesses, tests, documentation, and the Streamlit dashboard.
- **Student Researcher (Human):** Holds sole authority for approval of scientific assumptions, labelling policies, and ground-truth catalogues; implements and executes training for Logistic Regression, Random Forest, and XGBoost; conducts hyperparameter tuning and model selection; executes validation and final test runs; and performs scientific interpretation of results. **Antigravity does not train research models or invent performance figures.**

---

## Documentation Index
Detailed project documentation is available in the [`docs/`](docs/) directory:

- [**00. Requirements Specification**](docs/00_requirements.md) — Research questions, 16 functional requirements, non-functional requirements, constraints, and division of responsibility.
- [**01. Decision Log**](docs/01_decision_log.md) — Log of architectural and scientific decisions (D-01 through D-14) tracking open, provisional, and approved statuses.
- [**02. Roadmap**](docs/02_roadmap.md) — The 17-stage project implementation lifecycle (Stages 0–16), including dependencies, deliverables, and student approval gates.
- [**03. System Architecture**](docs/03_architecture.md) — Layered software architecture, unidirectional data flow, write permissions, and subsystem designs.
- [**03b. FITS Inspection Methods**](docs/03_inspection_methods.md) — Inspection algorithms, role detection heuristics, and inventory interpretation guidelines.
- [**04. Quality Assessment Methods**](docs/04_quality_methods.md) — Pure functional quality checks, cadence diagnostics, GTI coverage quantification, and Gate G1/G2 protocols.
- [**05. EDA Methods**](docs/05_eda_methods.md) — Robust running baseline, candidate burst intervals, and variability metrics.
- [**05b. EDA Findings**](docs/05_eda_findings.md) — Automated statistical summaries and qualitative observation prompts.
- [**06. Event Record Schema**](docs/06_event_record_schema.md) — Ground-truth solar flare event record specification (template).
- [**07. Ground-Truth Research**](docs/07_ground_truth_research.md) — Sourcing taxonomy, accessed independent flare catalogues, rejected sources, and unverified statements.
- [**08. Labelling Policy**](docs/08_labelling_policy.md) — Scientific labelling protocol draft with all Gate G3 decisions (D-01 to D-04, D-08, D-10, D-15) held PENDING.
- [**09. Time Compatibility**](docs/09_time_compatibility.md) — Evaluation of reference epochs, time scales (UTC vs MET), leap seconds, and L1 propagation delay.
- [**10. Preprocessing Methods**](docs/10_preprocessing_methods.md) — Non-destructive filtering, GTI boundary conventions, continuous segmentation, and auditable reconciliation.
- [**11. Feature Dictionary**](docs/11_feature_dictionary.md) — Exact mathematical definitions, units, reasons, and critical warning on row-level splitting for all 18 causal features.
- [**12. Windowing Methods**](docs/12_windowing_methods.md) — Sliding window geometry, reference time $t_0$, coverage fractions, and effective sample size considerations.
- [**13. Dataset Export**](docs/13_dataset_export.md) — Export structure, label semantics, <NA> exclusion meaning, and complete task separation.
- [**14. Training Protocol**](docs/14_training_protocol.md) — Non-random splitting, embargo buffers, test set sealing, and validation-only selection rules.
- [**15. Evaluation Methods**](docs/15_evaluation_methods.md) — Window-level vs. event-level duality, PR-AUC, covered-time false alarms, baselines, and single-shot evaluation governance.
- [**16. Dashboard Foundation**](docs/16_dashboard.md) — Local multipage Streamlit dashboard architecture, artifact loaders, status categories, and display-only guarantees.
- [**Setup & Troubleshooting (Windows)**](docs/setup_windows.md) — Step-by-step PowerShell environment setup, execution policies, and Windows troubleshooting.
- [**Official Data Acquisition Protocol**](docs/data_acquisition.md) — ISRO ISSDC PRADAN portal retrieval instructions, pairing rules, and checksum logging.

---

## Quality Assessment (Stage 4)
Stage 4 establishes non-destructive data quality characterisation of Aditya-L1 SoLEXS Level-1 light-curve and GTI observations:
- **Zero Mutation:** Real data is never clipped, imputed, interpolated, or filtered.
- **Segregated Sample Tracking:** NaN samples (4,849 observed in SDD2), zero counts, negative counts (0 detected), backward steps (0 detected), duplicate timestamps (0 detected), and candidate statistical spikes ($z_{\text{robust}} > 5.0$) are reported in dedicated, isolated metrics.
- **Candidate Spikes:** Flagged strictly as *"candidate spike — not a verified event"*.
- **Cadence & GTI:** Empirical median cadence (1.0000 s) and GTI coverage quantified without discarding points.
- **PROVISIONAL Status:** All results remain strictly `PROVISIONAL pending G1` human researcher confirmation.

Run quality assessment CLI:
```powershell
python scripts/run_quality.py --raw-dir data/raw --manifest data/manifests/manifest.csv --out-dir results/quality
```

---

## Exploratory Data Analysis (Stage 5)
Stage 5 implements reproducible exploratory data analysis of light-curve variability, count distributions, coverage timelines, running baselines, and candidate transient bursts:
- **Unverified Candidate Status:** All detected candidate intervals are strictly tagged `CANDIDATE — UNVERIFIED`.
- **Zero Labeling Guarantee:** Nothing produced in Stage 5 is a flare label, ground truth, or training target.
- **Event Comparison Check:** Returns strictly `NOT PERFORMED — no independent event records supplied` until external event catalogues are confirmed at Gate G3.

Run EDA CLI:
```powershell
python scripts/run_eda.py --out-dir results/eda
```

Execute exploratory notebook:
```powershell
jupyter nbconvert --to notebook --execute notebooks/02_eda.ipynb --output 02_eda_executed.ipynb --output-dir results/eda/notebook_runs
```

---

## Ground-Truth Research and Labelling Protocol (Stage 6)
Stage 6 establishes independent ground-truth catalogue research, temporal compatibility evaluation, and the scientific policy guard for Gate G3:
- **Independent Sourcing:** Evaluated external catalogues from NOAA SWPC, NOAA NCEI GOES, NASA HEK, and ISRO PRADAN (PRADAN rejected for labelling to prevent circularity). Registered in `data/manifests/event_sources.csv`.
- **No Unverified Claims:** All external sources evaluated as `TIME_SYSTEM_UNCONFIRMED` until SoLEXS time system (D-10) is confirmed. No arbitrary time conversions are performed.
- **Policy Guard (Gate G3):** `assert_labelling_approved()` strictly refuses execution unless `docs/08_labelling_policy.md` contains an approved status line and decisions D-01, D-02, D-03, D-04, D-08, D-10, D-15 are marked `APPROVED` with non-null values in `config/decisions.yaml`.
- **Zero Labels Generated:** Label generation is safely blocked; no training datasets or label tables exist.

Verify Gate G3 Guard Refusal:
```powershell
python scripts/check_labelling_guard.py
```

Run Temporal Compatibility Assessment:
```powershell
python scripts/run_compatibility.py
```

---

## Preprocessing & GTI-Aware Segmentation (Stage 7)
Stage 7 implements non-destructive sample filtering, GTI boundary filtering, and continuous observation segmentation:
- **Zero Mutation:** Raw files under `data/raw/` verified 100% hash identical before and after execution.
- **Zero Interpolation:** Data is never interpolated, reconstructed, or gap-filled.
- **Mathematical Sample Conservation:** Every single sample is accounted for ($N_{\text{retained}} + \sum N_{\text{excluded}} = N_{\text{original}}$). Discrepancy triggers `ReconciliationError`.
- **Reconciliation on 2026-10-18:** 86,400 raw samples $\to$ 81,379 retained in 4 valid continuous segments (94.19%), 4,849 non-finite excluded, 134 outside GTI excluded, 38 short segment samples excluded.
- **Format:** Exported to CSV format (pyarrow absent from dependencies).

Run Preprocessing Development CLI (PROVISIONAL mode):
```powershell
python scripts/run_preprocessing.py --stem all
```

Verify Final Run Refusal (Requires Gate G4 approval):
```powershell
python scripts/run_preprocessing.py --final
```

---

## Sliding Windows & Feature Engineering (Stage 8)
Stage 8 generates configurable sliding windows strictly within continuous segments, computes 18 causal summary and morphological features, and enforces sample-level causal isolation:
- **Intra-Segment Windows:** Windows strictly never cross segment or gap boundaries. Window length $W = 60\text{ s}$, stride $S = 10\text{ s}$ (D-05, D-06 provisional).
- **Zero Future Peeking:** Every feature $f_j(w_i)$ is computed using strictly $t \le w_{\text{end}} = t_0$.
- **Causal Local Baseline:** Evaluated over $[w_{\text{start}} - 600\text{ s}, w_{\text{start}})$ within the same segment. Never uses global or future samples.
- **Auditable Leakage Guard:** Evaluates actual timestamps used (`max_time_used <= window_end`). Offending slices raise `LeakageError` immediately.
- **Non-destructive & Zero Imputation:** Non-finite samples inside windows are excluded and accounted for; NaN is never imputed or filled.
- **Leakage Warning:** Overlapping windows ($S < W$) share raw samples. Random row-level splitting causes catastrophic data leakage. Cross-validation MUST be grouped by contiguous segment or time block (Stage 10).
- **Provisional Run on 2026-10-18:** Generated 8,116 windows across 4 segments (0 low coverage); 100% passed leakage guard.

Run Feature Extraction CLI (PROVISIONAL development run):
```powershell
python scripts/build_features.py --stem all
```

Verify Final Run Refusal (Requires Gate G5 approval):
```powershell
python scripts/build_features.py --final
```

---

## Label Integration & Dataset Export (Stage 9)
Stage 9 integrates validated sliding feature windows with independently verified ground-truth labels and exports segregated datasets:
- **Strict Task Separation:** Task A (Detection) and Task B (Forecasting) targets never share directories or tables.
- **Segregated Tabular Structure:** Exports `X_features.csv` (strictly features; no IDs, labels, or timestamps), `y_labels.csv` (`window_id`, `label`, `label_reason`), `metadata.csv` (full provenance), `exclusions.csv` (all `<NA>` rows with auditable reasons), `config_snapshot.yaml`, and `data_dictionary.md`.
- **Zero Imputation of Unknowns:** Unknown, partial, or embargoed intervals receive `<NA>` and are never coerced to `0`.
- **Policy Guard Enforcement:**
  - Detection export requires Gate G3 approval (`docs/08_labelling_policy.md`, confirmed event records).
  - Prediction export requires Gate G6 approval (`docs/22_forecasting_policy.md`, horizon and embargo parameters).
- **Current Live Status:** Live export on the real workspace strictly refuses and outputs BLOCKED reports (`results/exports/BLOCKED_DETECTION.md` and `results/exports/BLOCKED_PREDICTION.md`) because Gate G3 and Gate G6 await human researcher decisions.

Run Dataset Export CLI:
```powershell
# Detection Export (Task A)
python scripts/export_dataset.py --task detection

# Forecasting Export (Task B)
python scripts/export_dataset.py --task prediction
```

---

## Automated Model Training & Tuning (Stage 10)
Stage 10 implements non-random dataset splitting, test set cryptographic sealing, training-only preprocessing, and validation-only hyperparameter tuning:
- **Strict Non-Random Partitioning:** `chronological_split` enforces temporal embargo buffers (default 300 s) at partition boundaries; `event_grouped_split` groups by continuous segment/event ID. Random shuffling is strictly prohibited.
- **Cryptographic Test Lock:** Test samples are sealed in `results/experiments/<exp_id>/sealed/test_set.csv` with a SHA-256 hash before any tuning begins. Access is logged in `access_log.jsonl`; selection code contains 0 test reads.
- **Training-Only Preprocessing:** Scalers (`StandardScaler`, `RobustScaler`) are fitted strictly on training indices; validation/test overlap raises `TestLeakageError`. Imputation is `NONE` (raises on `NaN`).
- **Validation-Only Tuning:** Evaluates Logistic Regression, Random Forest, and XGBoost on validation data using PR-AUC. The test set is evaluated exclusively in Stage 11 under Gate G8.
- **Current Live Status:** Refuses execution and outputs `results/experiments/AWAITING_G7.md` because Gate G7 (training protocol freeze) awaits human approval.

Run Training CLI:
```powershell
python scripts/train_models.py --protocol config/training_protocol.yaml
```

---

## Scientific Evaluation (Stage 11)
Stage 11 implements the single-shot scientific evaluation engine for locked models on the sealed test set:
- **Single-Shot Evaluation Rule:** Evaluation on the test set is executed strictly once. Any attempt to re-evaluate an already evaluated experiment directory (`EVALUATED_ONCE`) is strictly refused.
- **Window vs. Event Metrics:** Evaluates both micro window-level classifications (PR-AUC, F1, precision, recall with mandatory prevalence reporting) and macro event-level detections (consecutive window merging, overlap matching against reference events, onset timing error median & IQR).
- **Covered Observation Normalization:** Operational false-alarm rates are computed strictly per GTI-covered science observation hour, never uncorrected wall-clock time.
- **Physics & Statistical Baselines:** Evaluates Threshold Baseline (causal peak-to-baseline ratio fitted strictly on training data), Climatological Baseline (constant training prevalence), and Persistence Baseline.
- **Calibration Assessment:** Computes reliability diagrams (equal-width probability bins), Expected Calibration Error (ECE), Maximum Calibration Error (MCE), and Brier score without post-hoc test recalibration.
- **Block Bootstrap Uncertainty:** Resamples continuous observation segments rather than rows to honor temporal autocorrelation. Withheld if independent segments are fewer than 5.
- **Dashboard Contract:** Generates `evaluation/dashboard_contract.json` specifying exact schema requirements for Stage 12 and Stage 13.
- **Gate G8 Guard:** Single-shot evaluation strictly refuses execution and writes `results/experiments/AWAITING_G8.md` unless Gate G8 human approval is explicitly recorded.

Run Evaluation CLI:
```powershell
python scripts/evaluate_locked_models.py --experiment-id <experiment_id>
```

---

## Streamlit Dashboard (Stage 12)
Stage 12 implements a local, interactive, multipage Streamlit dashboard (`dashboard/`):
- **Multipage Navigation:**
  - `app.py`: Overview of Task A (detection) vs. Task B (forecasting), Gate G3 labelling policy status, and pipeline artifact checklist.
  - `1_Overview.py`: Project stage tracking, FITS file inventory summary, and open research questions.
  - `2_Dataset.py`: Detailed product browser, manifest checksum integrity, detector pairing, and `GTI EMPTY FOR THIS OBSERVATION` warning for SDD1.
  - `3_Data_Quality.py`: Stage 4 quality summary table, per-file audit reports, and 4 diagnostic figures.
  - `4_Light_Curves.py`: Interactive time series explorer with time-range slider, GTI shaded rectangles, segregated 0/NaN sample markers, and display-only downsampling notice.
  - `5_Events.py`: Candidate burst table with persistent `CANDIDATE — UNVERIFIED` badges and light-curve zoom overlay.
  - `6_Features.py`: Sliding window index browser, feature histograms, and critical 83.3% window overlap leakage warning.
  - `7_Model_Results.py`: Protocol-governed validation selection results (`VALIDATION ONLY`) and single-shot sealed test evaluation reports.
- **Strict Read-Only Guarantee:** The dashboard never writes to `data/` or `results/`, never trains models, and never runs pipeline stages on button clicks.
- **Persistent Governance Disclaimer:** The sidebar permanently displays:
  > *"Candidate bursts are not verified solar flares. Pilot and provisional results are not validated detector performance."*

Launch Dashboard Locally on Windows:
```powershell
# In PowerShell (.venv activated)
python -m streamlit run dashboard/app.py
```
Open `http://localhost:8501` in your browser.

---

## Dashboard and Pipeline Integration (Stage 13)
Stage 13 connects the dashboard to real pipeline artifacts with end-to-end schema validation, cryptographic lineage checks, stale-artifact detection, and a pure functional status engine:
- **Pure Pipeline Status Engine (`src/solar_flare/status.py`):**
  Evaluates stages 3 through 11 without side effects or disk writes. Assigns one unambiguous status:
  - `COMPLETE`: Required artifacts exist, schemas valid, hashes consistent.
  - `PROVISIONAL`: Artifacts exist but depend on provisional decisions/thresholds.
  - `PARTIAL`: Some required artifacts missing.
  - `MISSING`: No artifacts found for stage.
  - `BLOCKED`: Explicit blocking notice (`AWAITING_G*.md` or `BLOCKED_*.md`) present.
  - `STALE`: Configuration parameter or upstream hash differs from recorded artifact values.
  - `ERROR`: Artifact fails schema validation or cryptographic hash check.
- **Cryptographic Lineage & Schemas (`src/solar_flare/integrity.py`):**
  Tracks SHA-256 hashes connecting raw Level-1 observations -> Stage 7 preprocessing audit -> Stage 8 feature build log -> Stage 10 sealed test set lock -> Stage 11 evaluation.
- **Stale Detection:** Parameter drift (e.g. window length in `default.yaml` vs. `build_log.json`) flags `STALE` and presents recorded vs. current values side-by-side without silent regeneration.
- **Zero-Write Isolation:** AST architecture scans enforce that dashboard pages cannot import training functions, invoke `.fit()`, spawn subprocesses, or open files for writing.

### Topological Pipeline Regeneration Sequence
```powershell
# 1. Inspect FITS files (Stage 3)
python scripts/inspect_fits.py

# 2. Quality Assessment (Stage 4)
python scripts/run_quality.py --raw-dir data/raw --manifest data/manifests/manifest.csv --out-dir results/quality

# 3. Exploratory Data Analysis (Stage 5)
python scripts/run_eda.py --out-dir results/eda

# 4. Check Labelling Policy Guard (Stage 6)
python scripts/check_labelling_guard.py

# 5. Preprocessing & Continuous Segmentation (Stage 7)
python scripts/run_preprocessing.py --stem all

# 6. Sliding Windows & Feature Engineering (Stage 8)
python scripts/build_features.py --stem all

# 7. Dataset Export (Stage 9 — Requires Gate G3/G6 approval)
python scripts/export_dataset.py --task detection

# 8. Model Training & Test Set Sealing (Stage 10 — Requires Gate G7 frozen protocol)
python scripts/train_models.py --protocol config/training_protocol.yaml

# 9. Single-Shot Test Set Evaluation (Stage 11 — Requires Gate G8 approval)
python scripts/evaluate_locked_models.py --experiment-id <experiment_id>

# 10. Run Integration Audit & Launch Dashboard (Stage 12/13)
python scripts/run_stage13_integration.py
python -m streamlit run dashboard/app.py
```

---

## Next Steps (Stage 14 Deployment & Gate G10 Review)
- Human researcher review of pipeline status categories and regeneration sequence in [`docs/17_integration.md`](docs/17_integration.md) (Gate G10).
- Unblock Gate G3 (labelling policy approval) when external GOES/SWPC catalogs are integrated.
- Proceed to Stage 14 (Automated Packaging, Deployment Preparation & Final Verification).

