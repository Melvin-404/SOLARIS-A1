# Project Roadmap: SOLARIS-A1

## Overview
This roadmap outlines the 17 sequential stages (Stage 0 through Stage 16) for `SOLARIS-A1` (*Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations*).

Each stage defines its objectives, dependencies, deliverables, Antigravity responsibilities, and required **Human-Approval Gates** where the student researcher must review, execute models, or formally sign off before subsequent work proceeds.

---

## Roadmap Summary Table

| Stage | Name | Key Dependencies | Primary Deliverables | Approval Gate (Student) |
| :--- | :--- | :--- | :--- | :--- |
| **0** | **Research Requirements & Architecture** | None | Requirements, Decision Log, Roadmap, Architecture, README | Sign-off on scope, division of responsibilities, and initial decisions |
| **1** | **Environment & Project Structure Setup** | Stage 0 | Directory tree, Python venv config, dependency manifest, `.gitignore` | Verify local installation and script execution on Windows |
| **2** | **Data Acquisition & Ingestion Protocol** | Stage 1 | PRADAN retrieval protocol, data directory layout, ingestion manifest | Confirm raw Level-1 data files and GTI files placed in raw storage |
| **3** | **Raw FITS Inspection & Metadata Verification** | Stage 2 | FITS header inspector, schema report, time format and energy channel docs | Review and approve resolved FITS schema, time convention, and channel IDs |
| **4** | **GTI-Aware Data Validation & QC** | Stage 3 | GTI parsing module, gap detection tools, data quality validator | Approve gap thresholds, data filtering, and invalid interval masks |
| **5** | **Exploratory Data Analysis (EDA)** | Stage 4 | Light-curve profiles, cadence checks, background flux distributions, EDA notebook | Review EDA insights, background stability, and physical distributions |
| **6** | **Ground-Truth Flare Event Catalogue Ingestion** | Stage 5 | External catalogue parser, timestamp alignment module, candidate matcher | Select & approve verified flare catalogue and time-matching tolerance |
| **7** | **Event Labelling Infrastructure & Verification** | Stage 6 | Deterministic labelling engine, negative interval generator, label audit log | Audit and approve ground-truth label assignments and negative sampling buffer |
| **8** | **Time-Series Segmentation & Windowing** | Stage 7 | GTI-respecting sliding-window engine, window indexer, metadata tracker | Approve window length ($W$) and stride ($S$) settings |
| **9** | **Feature Engineering Pipeline** | Stage 8 | Statistical, morphological, and temporal feature extractors, unit tests | Review physical relevance and numerical correctness of feature set |
| **10** | **Dataset Generation & Export** | Stage 9 | Clean exported feature datasets (Parquet/CSV), train/val/test split generator | Approve train/val/test split protocol and temporal isolation |
| **11** | **Threshold Baseline Implementation** | Stage 10 | Standard physical flux and derivative threshold detector benchmarks | Review baseline benchmark performance metrics |
| **12** | **Student Model Training Framework (Task A)** | Stage 11 | Training and evaluation harness scripts for LR, RF, XGBoost | **Student executes:** Model training, hyperparameter tuning, and model selection |
| **13** | **Event-Level Evaluation & Validation (Task A)** | Stage 12 | Event-level metric aggregation module (latency, event recall, false triggers) | Student reviews, interprets, and approves Task A detection findings |
| **14** | **Pre-Flare Activity Analysis Infrastructure (Task B)** | Stage 13 | Pre-onset feature extractor, horizon buffer generator, student training harness | Approve prediction horizons ($\Delta t_{\text{horizon}}$); **Student trains Task B models** |
| **15** | **Interactive Streamlit Dashboard** | Stages 5, 7, 10, 13, 14 | Local interactive dashboard (light-curve viewer, QC, labels, results viewer) | Walkthrough and acceptance of dashboard functionality |
| **16** | **Reproducibility Package & Final Documentation** | Stage 15 | Reproducibility bundle, frozen environment, complete audit report | Final project review and scientific sign-off |

---

## Detailed Stage Breakdown

### Stage 0: Research Requirements and Architecture
- **Objective:** Establish the formal scientific and technical foundation.
- **Dependencies:** None.
- **Antigravity Scope:** Author `docs/00_requirements.md`, `docs/01_decision_log.md`, `docs/02_roadmap.md`, `docs/03_architecture.md`, and top-level `README.md`.
- **Deliverables:** Complete documentation foundation without code or data.
- **Human Approval Gate:** Student reviews and signs off on project aims, operational separation of Task A and Task B, and initial decision statuses.

### Stage 1: Environment and Project Structure Setup
- **Objective:** Construct clean, reproducible local workspace and environment on Windows.
- **Dependencies:** Stage 0 approval.
- **Antigravity Scope:** Generate folder tree (`data/`, `src/`, `notebooks/`, `tests/`, `dashboard/`), configure `requirements.txt` / `pyproject.toml`, `.gitignore`, and basic environment verification scripts.
- **Deliverables:** Working Python virtual environment configuration and project scaffolding.
- **Human Approval Gate:** Student executes verification script locally and confirms clean environment setup.

### Stage 2: Data Acquisition and Ingestion Protocol
- **Objective:** Define explicit procedures for obtaining real Aditya-L1 SoLEXS Level-1 data from ISRO/ISSDC PRADAN.
- **Dependencies:** Stage 1.
- **Antigravity Scope:** Author download checklist, PRADAN navigation guide, data directory conventions, and file integrity check scripts (SHA-256). Prohibit automated downloading.
- **Deliverables:** `docs/data_acquisition_guide.md`, ingestion manifest, and verification script.
- **Human Approval Gate:** Student downloads Level-1 FITS and GTI files and places them into the designated immutable raw directory.

### Stage 3: Raw FITS Inspection and Metadata Verification
- **Objective:** Empirically verify FITS structures without pre-conceived assumptions.
- **Dependencies:** Stage 2 (raw files present).
- **Antigravity Scope:** Build read-only inspection script using `astropy.io.fits` to log HDU names, headers, table columns, units, time formats (UTC vs MET), and energy channels.
- **Deliverables:** Inspection script, FITS schema report (`docs/solexs_fits_schema.md`), populated decisions D-09 and D-10.
- **Human Approval Gate:** Student reviews extracted metadata and confirms channels and time conventions to use.

### Stage 4: GTI-Aware Data Validation and Quality Control
- **Objective:** Ingest Level-1 GTI files and enforce rigorous observation interval masking.
- **Dependencies:** Stage 3.
- **Antigravity Scope:** Implement GTI parser and gap detection module. Produce quality control summaries (cadence stability, dropouts, duty cycle).
- **Deliverables:** `src/data/gti_validator.py`, automated QC test suite, data quality report.
- **Human Approval Gate:** Student approves gap tolerance and invalid data exclusion criteria (D-04, D-14).

### Stage 5: Exploratory Data Analysis (EDA)
- **Objective:** Examine raw and GTI-filtered light-curve characteristics.
- **Dependencies:** Stage 4.
- **Antigravity Scope:** Provide EDA scripts and Jupyter notebook template generating light-curve profiles, count rate distributions, background variance, and noise properties.
- **Deliverables:** `notebooks/01_eda_solexs_lightcurves.ipynb`, summary figures.
- **Human Approval Gate:** Student reviews EDA observations and approves background estimation approach (D-13).

### Stage 6: Ground-Truth Flare Event Catalogue Ingestion & Alignment
- **Objective:** Ingest and align independent, scientifically verified solar flare records.
- **Dependencies:** Stage 5.
- **Antigravity Scope:** Develop parser for external flare catalogues (e.g., GOES flare catalogue or PRADAN event lists). Implement timestamp matching with configurable tolerance $\pm \Delta t$.
- **Deliverables:** `src/labels/catalogue_parser.py`, `src/labels/event_alignment.py`.
- **Human Approval Gate:** Student selects and provides external catalogue (D-01) and approves matching tolerance (D-02) and onset/peak/end definitions (D-03).

### Stage 7: Event Labelling Infrastructure & Verification
- **Objective:** Assign deterministic labels to observation intervals.
- **Dependencies:** Stage 6.
- **Antigravity Scope:** Build labelling pipeline producing binary flare/non-flare flags and multi-class flare-class annotations. Implement negative sampling buffer generator to ensure clean quiet-Sun samples.
- **Deliverables:** `src/labels/labelling_engine.py`, label verification summary, negative sampling audit.
- **Human Approval Gate:** Student audits label distribution and confirms negative interval selection rules (D-08).

### Stage 8: Time-Series Segmentation and Sliding-Window Extraction
- **Objective:** Slice continuous observation intervals into analysis windows.
- **Dependencies:** Stage 7.
- **Antigravity Scope:** Implement sliding-window generator parametrized by window length $W$ and stride $S$. Enforce strict GTI isolation: windows must never cross GTI boundaries or data gaps.
- **Deliverables:** `src/features/segmentation.py`, unit tests validating gap isolation.
- **Human Approval Gate:** Student approves final window length (D-05) and stride (D-06).

### Stage 9: Feature Engineering Pipeline
- **Objective:** Compute time-series domain features for each observation window.
- **Dependencies:** Stage 8.
- **Antigravity Scope:** Develop feature extractors: statistical moments (mean, std, skewness, kurtosis), dynamic metrics (min-max ratio, rise/fall slopes, first/second differences), and spectral hardness ratios across channels.
- **Deliverables:** `src/features/extractors.py`, feature calculation test suite, feature definition documentation.
- **Human Approval Gate:** Student reviews feature documentation and verifies physical interpretability.

### Stage 10: Dataset Generation and Export
- **Objective:** Export clean, leakage-free feature tables with metadata.
- **Dependencies:** Stage 9.
- **Antigravity Scope:** Construct dataset export module saving tabular features in Parquet and CSV formats. Implement student-approved temporal split policy (D-12) to prevent autocorrelation leakage between adjacent windows.
- **Deliverables:** `src/data/export_dataset.py`, exported train/validation/test matrices, data split manifest.
- **Human Approval Gate:** Student approves split strategy (D-12) and class imbalance mitigation strategy (D-11).

### Stage 11: Threshold Baseline Implementation
- **Objective:** Implement non-ML physical and statistical baseline detectors.
- **Dependencies:** Stage 10.
- **Antigravity Scope:** Build classical baseline algorithms (e.g., $N$-sigma above running background flux, derivative threshold trigger) and compute benchmark performance metrics on validation sets.
- **Deliverables:** `src/models/baseline_threshold.py`, baseline performance benchmark table.
- **Human Approval Gate:** Student reviews baseline metrics to establish research benchmark.

### Stage 12: Student Model Training Framework (Task A: Detection)
- **Objective:** Facilitate student-driven training of ML models for solar flare detection.
- **Dependencies:** Stage 11.
- **Antigravity Scope:** Provide structured evaluation harnesses and template scripts for model training, cross-validation, and metrics logging. Provide standard scikit-learn and XGBoost interfaces.
- **Deliverables:** `notebooks/02_student_training_task_a.ipynb`, evaluation utility `src/models/evaluation.py`.
- **Human Approval Gate:** **STUDENT SOLE RESPONSIBILITY:** Student selects hyperparameters, executes training for Logistic Regression, Random Forest, and XGBoost, evaluates validation performance, and chooses champion model. Antigravity does not train models.

### Stage 13: Event-Level Evaluation and Performance Validation (Task A)
- **Objective:** Translate window-level predictions into physical flare-event evaluations.
- **Dependencies:** Stage 12.
- **Antigravity Scope:** Implement event-level aggregator calculating event detection rate, detection latency (delay relative to catalogue onset), and false event trigger frequency.
- **Deliverables:** `src/evaluation/event_metrics.py`, comparative report comparing student ML models to baselines.
- **Human Approval Gate:** Student verifies event-level metrics and validates scientific conclusions for Task A.

### Stage 14: Pre-Flare Activity Analysis Infrastructure (Task B: Forecasting)
- **Objective:** Construct rigorous pre-flare forecasting experiment strictly decoupled from Task A.
- **Dependencies:** Stage 13 (Task A must be completed first).
- **Antigravity Scope:** Implement pre-flare dataset builder defining prediction time $t_{\text{pred}}$, forecast horizon $\Delta t_{\text{horizon}}$, and feature window $[t_{\text{pred}} - W_{\text{pre}}, t_{\text{pred}}]$. Enforce strict exclusion of data at and after flare onset. Provide student training harness for forecasting models.
- **Deliverables:** `src/features/preflare_builder.py`, `notebooks/03_student_training_task_b.ipynb`.
- **Human Approval Gate:** Student defines horizon $\Delta t_{\text{horizon}}$ (D-07), reviews precursor feature distributions, and **trains Task B models**.

### Stage 15: Streamlit Interactive Research Dashboard
- **Objective:** Deliver a responsive local web interface for exploration and results visualization.
- **Dependencies:** Stages 5, 7, 10, 13, 14.
- **Antigravity Scope:** Build multi-page Streamlit application with interactive light-curve viewer, GTI mask overlays, event alignment inspector, feature explorer, and student model evaluation viewer (read-only; no auto-training on startup).
- **Deliverables:** `dashboard/app.py`, `dashboard/pages/`.
- **Human Approval Gate:** Student conducts interactive walkthrough and approves dashboard usability and visualizations.

### Stage 16: Reproducibility Package, Final Documentation, and Project Wrap-Up
- **Objective:** Package the entire research workflow for auditability, publication, or thesis submission.
- **Dependencies:** Stage 15.
- **Antigravity Scope:** Package dependency lockfiles, execution scripts, final data dictionary, consolidated decision log, and automated verification tests.
- **Deliverables:** Complete `docs/`, reproducibility check script `verify_reproducibility.py`, final summary report.
- **Human Approval Gate:** Student conducts final review and issues official project completion approval.
