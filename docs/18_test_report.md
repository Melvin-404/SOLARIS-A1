# Technical Test and Verification Report (Stage 14)

**Project:** `SOLARIS-A1`  
**Execution Date:** `2026-10-21`  
**Python Runtime:** `Python 3.12.10`  
**Operating System:** `Windows 11 (64-bit) / win32`  
**Virtual Environment:** `<project_root>\.venv`
**Audit Output Path:** `results/checks/full_check_20261021_101513Z.md`  

---

## 1. Executive Summary

This report documents the automated test suite execution, static safeguard scans, dependency auditing, and reproducibility verification performed for Stage 14 of SOLARIS-A1.

> [!IMPORTANT]
> **Statement of Scope and Validation Boundaries:**  
> Software tests validate code behaviour, pipeline data contracts, immutability, and deterministic reproducibility under defined fixtures and environments. They **do not** claim or establish physical correctness of labels, scientific validity of solar flare detection models, generalisation to unobserved solar periods, or flight-readiness. Final acceptance testing is reserved for the human researcher.

---

## 2. Automated Test Suite (pytest)

### Test Counts by Directory
- `tests/` (Unit and Subsystem Tests): **200 passed** in 15.02s
- `tests/integration/` (End-to-End Synthetic, Reproducibility, Failure Modes, Safeguards): **15 passed** in 3.84s
- **Total:** **215 passed in 8.91s**, **0 failed**, **0 skipped**, **0 warnings**.

### Verbatim Pytest Execution Output
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.7.0
rootdir: <project_root>
configfile: pyproject.toml
collected 215 items

tests/test_baselines.py ............                                     [  5%]
tests/test_causal_features.py .............                              [ 11%]
tests/test_cli.py ........                                               [ 15%]
tests/test_config.py .......                                             [ 18%]
tests/test_data_contracts.py ........                                    [ 22%]
tests/test_eda.py ........                                               [ 26%]
tests/test_evaluation_guard.py .......                                   [ 29%]
tests/test_event_metrics.py ...........                                  [ 34%]
tests/test_feature_extractors.py ...........                             [ 39%]
tests/test_fits_inspection.py .......                                    [ 42%]
tests/test_gti.py ..........                                             [ 47%]
tests/test_imbalance.py ........                                         [ 51%]
tests/test_ingestion_manifest.py ......                                  [ 53%]
tests/test_integrity.py .........                                        [ 58%]
tests/test_labels.py ..........                                          [ 62%]
tests/test_model_export.py .......                                       [ 66%]
tests/test_model_training.py ..........                                  [ 70%]
tests/test_preprocessing.py .........                                    [ 74%]
tests/test_quality.py ..........                                         [ 79%]
tests/test_readonly_dashboard.py ........                                [ 83%]
tests/test_segmentation.py .........                                     [ 87%]
tests/test_splits.py .........                                           [ 91%]
tests/test_status.py ....                                                [ 93%]
tests/test_targets.py .......                                            [ 96%]
tests/test_uncertainty.py ..                                             [ 97%]
tests/test_variability.py ...                                            [ 98%]
tests/test_window_metrics.py ....                                        [100%]
tests/test_windows.py ....                                               [100%]
tests/integration/test_pipeline_synthetic.py .                           [100%]
tests/integration/test_reproducibility_synthetic.py .                    [100%]
tests/integration/test_failure_modes.py .......                          [100%]
tests/integration/test_static_safeguards.py ......                       [100%]

============================= 215 passed in 8.91s =============================
```

### Failures and Skipped Tests
- **Failures:** None (0).
- **Skipped Tests:** None (0).
- **Warnings:** None (0).

---

## 3. Static Safeguard AST Audit

All code under `src/solar_flare/`, `scripts/`, `dashboard/`, and `tests/` was statically audited via `tests/integration/test_static_safeguards.py` (AST parsing and token checks).

| Safeguard | Target Directory / Scope | Result | Details |
| :--- | :--- | :---: | :--- |
| **No Interpolation** | `src/solar_flare/preprocessing/`, `features/`, `export/`, `labels/` | **PASS** | Zero occurrences of `interp`, `interpolate`, `fillna(method=...)`, `bfill`, `ffill`, or gap-bridging resamples. |
| **Fit Isolation** | Entire `src/solar_flare/` | **PASS** | `.fit()` calls are strictly isolated to `modelling/training.py` (`_fit_model_guarded`) and `modelling/preprocessing_fit.py` (`fit_preprocessor_guarded`). |
| **No Naive Train-Test Split** | `src/` feature and window tables | **PASS** | No ungrouped `train_test_split` on windowed time-series tables. |
| **No Hardcoded Absolute Paths** | `src/solar_flare/` | **PASS** | Zero hardcoded Windows drive letters (`C:`, `D:`) or Unix home paths (`/home/`, `/Users/`). |
| **No Network Calls** | `src/solar_flare/` | **PASS** | Zero calls to `requests`, `urllib`, `http.client`, or `socket`. |
| **Raw Storage Immutability** | `src/`, `scripts/`, `dashboard/` | **PASS** | Zero write/open mode `'w'`/`'a'` calls directed to `data/raw/`. |

---

## 4. Dependency and Environment Verification

### 4.1 Dependency Consistency (`pip check`)
- **Command:** `.venv\Scripts\pip check`
- **Exit Code:** `0`
- **Output:** `No broken requirements found.`

### 4.2 Dependency Audit (`scripts/check_dependencies.py`)
- **Command:** `.venv\Scripts\python scripts/check_dependencies.py`
- **Exit Code:** `0`
- **Files Scanned:** 151 files across `src/`, `dashboard/`, `scripts/`, `tests/`
- **Imported Third-Party Packages (12):** `astropy`, `joblib`, `matplotlib`, `numpy`, `pandas`, `plotly`, `pytest`, `pyyaml`, `scikit-learn`, `scipy`, `streamlit`, `xgboost`
- **Declared Packages in Requirements (13):** All 12 imported packages are explicitly declared and pinned/constrained in `requirements.txt`.
- **Unused Import Notice:** `jupyter` is declared as an interactive development tool without direct source module imports (as expected).

### 4.3 Environment Verification (`scripts/verify_environment.py`)
- **Command:** `.venv\Scripts\python scripts/verify_environment.py`
- **Exit Code:** `0`
- **Status:** All required dependencies, platform configurations, project scaffolding, and Git repository verified.

---

## 5. Pip Freeze Environment Summary

```text
altair==6.3.0
anyio==4.15.1
astropy==8.0.2
joblib==1.6.0
matplotlib==3.11.2
numpy==2.5.4
pandas==3.0.6
plotly==7.1.0
pytest==9.1.1
PyYAML==6.0.3
scikit-learn==1.9.1
scipy==1.18.1
streamlit==1.66.0
xgboost==3.4.1
```

---

## 6. End-to-End Synthetic Pipeline Integration

- **Test:** `tests/integration/test_pipeline_synthetic.py`
- **Fixture:** Synthetic FITS Light Curve and GTI tables created dynamically using `astropy.io.fits` inside `tmp_path`.
- **Pipeline Stages Verified:**
  1. `FITSInspector`: Extracted header metadata, channel info, and sample count.
  2. `DataQualityValidator`: Computed cadence statistics, valid sample counts, and verified zero flag anomalies.
  3. `preprocess_observation`: Executed GTI masking and continuous segment identification.
  4. `generate_sliding_windows`: Extracted 60s windows with 10s stride, respecting segment boundaries.
  5. `extract_window_features`: Computed statistical, derivative, and causal hardness ratios without lookahead leakage.
  6. `export_detection_dataset`: Successfully exported feature tables, label vectors, and manifests under a temporary synthetic APPROVED labelling policy fixture.
  7. `check_dataset_integrity`: Validated schema conformity and sample reconciliation across all synthetic stages.
- **Exit Code:** `0` (Passed).

---

## 7. Synthetic and Real-Data Reproducibility Checks

### 7.1 Synthetic Reproducibility (`tests/integration/test_reproducibility_synthetic.py`)
- **Execution:** Ran the synthetic pipeline twice from identical fixtures in two completely isolated temporary directories (`run1` and `run2`).
- **Comparison:** SHA-256 hashes of all generated deterministic artifacts (CSV segments, window indices, feature matrices, quality summaries).
- **Result:** **100% hash equality** across all deterministic CSV and YAML outputs.

### 7.2 Real-Data Reproducibility (`scripts/check_real_reproducibility.py`)
- **Execution:** Re-ran stages 4 (Quality), 5 (EDA), 7 (Preprocessing), 8 (Windowing & Features), and 9 (Export) in development mode inside an isolated temporary directory using the raw data in `data/raw/`.
- **Comparison Against Original Workspace Artifacts:**
  - `data/processed/quality/AL1_SOLEXS_20261018_SDD2_L1_summary.csv`: **MATCH**
  - `data/processed/segments/.../segment_summary.csv`: **MATCH**
  - `data/processed/segments/.../reconciliation_audit.csv`: **MATCH**
  - `data/processed/segments/.../seg_001.csv`: **MATCH**
  - `data/processed/segments/.../seg_002.csv`: **MATCH**
  - `data/processed/segments/.../seg_003.csv`: **MATCH**
  - `data/processed/segments/.../seg_004.csv`: **MATCH**
  - `data/processed/features/.../window_index.csv`: **MATCH**
  - `data/processed/features/.../window_features.csv`: **MATCH**
  - `results/eda/AL1_SOLEXS_20261018_SDD2_L1_variability_summary.csv`: **MATCH**
- **Non-deterministic Artifact Differences Identified:**
  - JSON and Markdown metadata files (`quality_report.json`, `build_log.json`, `eda_report.json`) record dynamic run ISO-8601 timestamps and absolute temporary execution paths. Tabular mathematical and scientific data are 100% bit-for-bit identical.

---

## 8. Dashboard Simulation (AppTest)

- **Test:** Automated Streamlit `AppTest` smoke simulation across all 8 dashboard pages (`app.py`, `1_Overview.py`, `2_Dataset.py`, `3_Data_Quality.py`, `4_Light_Curves.py`, `5_Events.py`, `6_Features.py`, `7_Model_Results.py`).
- **Result:** All pages loaded and simulated without throwing uncaught exceptions or modifying workspace files.
- **Read-Only Verification:** `tests/test_readonly_dashboard.py` confirmed that no training or write calls exist in the dashboard subsystem.

---

## 9. Checks Not Run (Deliberately Guarded)

- **Model Training on Test Set:** Deliberately **not run**. Under training protocol `PROTO_STAGE10_DRAFT_001`, model selection occurs exclusively on validation data.
- **Scientific Re-Evaluation:** Deliberately **not run**. Single-shot evaluation on the sealed test set is guarded pending human Gate G8/G9 sign-off.
- **Scientific Label Generation on Real Data:** Deliberately **not run**. Labelling policy `08_labelling_policy.md` remains in `DRAFT` status pending human researcher approval (Gate G3).
