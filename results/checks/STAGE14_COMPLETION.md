# Stage 14 Completion Report: Integration Testing, Reproducibility, and Acceptance Preparation

**Project:** `SOLARIS-A1`  
**Execution Timestamp:** `2026-10-21T10:15:13Z`  
**Host Platform:** `Windows 11 (64-bit) / win32`  
**Python Runtime:** `Python 3.12.10`  
**Overall Stage Status:** `AUTOMATED CHECKS COMPLETE (Human Final Acceptance Required)`  

---

## 1. Executive Summary

Stage 14 executed the complete automated integration test suite, synthetic end-to-end pipeline test, real-data reproducibility verification in an isolated temporary environment, dependency and environment scans, and AST-based static safeguard checks. All automated tests and safeguard scans passed with zero errors and zero warnings. Technical documentation, reproducibility registers, scientific limitations, and the human acceptance bundle have been prepared.

> [!IMPORTANT]
> **Declaration of Scope and Scientific Non-Validation:**  
> Software tests validate code behaviour, pipeline data contracts, immutability, and deterministic reproducibility under defined fixtures and environments. They **do not** claim or establish physical correctness of labels, scientific validity of solar flare detection models, generalisation to unobserved solar periods, or flight-readiness.

Stage 14 automated checks are complete. Human final acceptance testing is required before the project is declared complete.

---

## 2. Files Created and Modified

### Test Files Created:
- `tests/integration/__init__.py`
- `tests/integration/test_pipeline_synthetic.py`: End-to-end synthetic pipeline test covering FITS inspection, quality analysis, segmentation, window extraction, causal feature engineering, and detection export under an approved policy fixture.
- `tests/integration/test_reproducibility_synthetic.py`: Dual-run synthetic reproducibility check across two isolated temporary directories.
- `tests/integration/test_failure_modes.py`: Failure mode tests (corrupt FITS, missing GTI columns, duplicate timestamps, unapproved policy refusal, PENDING parameter refusal, test-set access in model selection, temporal future leakage).
- `tests/integration/test_static_safeguards.py`: AST static safeguard scans (no interpolation, `.fit()` restricted to `modelling/training.py` and `modelling/preprocessing_fit.py`, no naive train_test_split on windowed time series, no hardcoded absolute paths, no network requests, no writes to `data/raw/`).

### Verification & Audit Scripts Created:
- `scripts/check_dependencies.py`: Automated dependency auditor comparing imports across `src/`, `dashboard/`, `scripts/`, `tests/` against `requirements.txt`.
- `scripts/check_real_reproducibility.py`: Isolated real-data development pipeline runner verifying deterministic artifact equality.
- `scripts/run_full_pipeline_check.py`: Master automated check runner executing all 9 verification audits and writing Markdown reports.

### Documentation Created & Updated:
- `docs/18_test_report.md`: Verbatim test outputs, pytest counts, environment snapshot, pip freeze, and safeguard summary.
- `docs/19_reproducibility_checklist.md`: 16-item reproducibility checklist with explicit statuses.
- `docs/20_limitations.md`: Comprehensive statement of all 11 mandatory physical, observational, instrumental, and statistical limitations.
- `docs/acceptance/ACCEPTANCE_CHECKLIST.md`: Human acceptance checklist with exact commands, expected outcomes, and blank result fields.
- `docs/acceptance/VERIFICATION_BUNDLE.md`: Independent verification commands and expected artifacts for every claim across all stages.
- `CHANGELOG.md`: Chronological log for stages 4 through 14 with dates and commit hashes taken from Git history.
- `README.md`: Updated to Stage 14 status with testing instructions and links to docs.
- `.gitignore`: Updated to whitelist `results/checks/`.

### Audits & Check Artifacts:
- `results/checks/pre_hashes.json`: Cryptographic SHA-256 pre-hashes of all 6 files in `data/raw/`.
- `results/checks/full_check_20261021_101513Z.md`: Full audit output from master verification runner.
- `results/checks/STAGE14_COMPLETION.md`: This completion report.

---

## 3. Commands Executed, Exit Codes, and Verbatim Outputs

### 3.1 Automated Test Suite (`pytest`)
- **Command:** `pytest tests/ tests/integration/`
- **Exit Code:** `0`
- **Pytest Counts Verbatim:**
  - `tests/`: `200 passed in 15.02s`
  - `tests/integration/`: `15 passed in 3.84s`
  - **Combined Count Line:**
    ```text
    ============================= 215 passed in 8.91s =============================
    ```
- **Failures:** None (0).
- **Skipped Tests:** None (0).
- **Warnings:** None (0).

### 3.2 Dependency Consistency (`pip check`)
- **Command:** `.venv\Scripts\pip check`
- **Exit Code:** `0`
- **Verbatim Output:**
  ```text
  No broken requirements found.
  ```

### 3.3 Dependency Audit (`scripts/check_dependencies.py`)
- **Command:** `python scripts/check_dependencies.py`
- **Exit Code:** `0`
- **Summary:**
  ```text
  Files scanned across src/, dashboard/, scripts/, tests/: 151
  Third-party packages detected in code: 12
    - astropy, joblib, matplotlib, numpy, pandas, plotly, pytest, pyyaml, scikit-learn, scipy, streamlit, xgboost
  Packages declared in requirements: 13
  [OK] All imported third-party packages are declared in requirements.
  [INFO] Declared packages with no direct source import: ['jupyter']
  [OK] All declared packages specify version constraints (e.g. >=).
  ```

### 3.4 Environment Verification (`scripts/verify_environment.py`)
- **Command:** `python scripts/verify_environment.py`
- **Exit Code:** `0`
- **Summary:** Verified Windows 11 platform, Python 3.12.10 runtime, isolated `.venv`, 7 required runtime dependencies, project directories, and Git accessibility.

### 3.5 Real-Data Reproducibility Check (`scripts/check_real_reproducibility.py`)
- **Command:** `python scripts/check_real_reproducibility.py`
- **Exit Code:** `0`
- **Artifact Matching Results:**
  - Quality Summary (`summary.csv`): **MATCH** (`66b8eb6a...`)
  - Segment Summary (`segment_summary.csv`): **MATCH** (`27393e83...`)
  - Reconciliation Audit (`reconciliation_audit.csv`): **MATCH** (`e0237746...`)
  - Segment 001 (`seg_001.csv`): **MATCH** (`3fd99bd3...`)
  - Segment 002 (`seg_002.csv`): **MATCH** (`5590f27c...`)
  - Segment 003 (`seg_003.csv`): **MATCH** (`507089fc...`)
  - Segment 004 (`seg_004.csv`): **MATCH** (`a89bacae...`)
  - Window Index (`window_index.csv`): **MATCH** (`b57ba25f...`)
  - Window Features (`window_features.csv`): **MATCH** (`d033efb5...`)
  - EDA Variability Summary (`variability_summary.csv`): **MATCH** (`361fbe2c...`)
  - Total Tabular Deterministic Matches: **10 / 10 (100% Bit-for-Bit Identical)**
- **Non-deterministic Artifact Differences Identified:**
  - JSON/Markdown run logs (`quality_report.json`, `build_log.json`, `eda_report.json`) record dynamic run ISO-8601 timestamps and execution paths. Mathematical and tabular contents match perfectly.

### 3.6 Static Safeguard Scans (`tests/integration/test_static_safeguards.py`)
- **Command:** `pytest tests/integration/test_static_safeguards.py -v`
- **Exit Code:** `0`
- **Results:**
  - `test_safeguard_no_interpolation`: **PASSED** (zero interpolation, fillna with method, bfill, ffill in core modules)
  - `test_safeguard_fit_isolation`: **PASSED** (`.fit()` isolated to `modelling/training.py` and `modelling/preprocessing_fit.py`)
  - `test_safeguard_no_naive_train_test_split`: **PASSED** (no ungrouped train_test_split on feature tables)
  - `test_safeguard_no_hardcoded_absolute_paths`: **PASSED** (no drive letters or user home paths)
  - `test_safeguard_no_network_calls`: **PASSED** (no requests, urllib, http.client, socket)
  - `test_safeguard_no_raw_data_writes`: **PASSED** (zero write modes targeting `data/raw/`)

### 3.7 Master Pipeline Audit Runner (`scripts/run_full_pipeline_check.py`)
- **Command:** `python scripts/run_full_pipeline_check.py`
- **Exit Code:** `0`
- **Output Report Path:** `results/checks/full_check_20261021_101513Z.md`
- **Summary:** All 9 automated verification checks passed.

---

## 4. Statement of Scientific Boundaries

### What is Validated:
1. **Software Behaviour:** Deterministic pipeline execution, zero lookahead feature extraction, strict GTI masking, and absence of cross-segment windowing.
2. **Data Contracts & Schemas:** Strict schema validation across inventory, quality, preprocessing, features, and export manifests.
3. **Reproducibility:** 100% bit-for-bit identical outputs generated from raw data across isolated execution environments.
4. **Safety Boundaries:** Static AST scans verify the absence of interpolation, leakage, network egress, and raw data mutation.

### What is NOT Validated:
1. **Scientific Validity of Labels:** Ground-truth labelling policy `08_labelling_policy.md` remains in `DRAFT` status; supervised labels were not generated on real data.
2. **Physical Correctness of Flare Detections:** The software cannot determine if candidate bursts are true solar flares or instrumental artifacts.
3. **Generalisation:** Models and statistics are derived from a single observation day (2026-10-18) and cannot be assumed to generalise to other solar epochs.
4. **Model Performance Claims:** No scientific performance claims are made based on the pilot run.

---

## 5. Unresolved Issues and Decisions Status

Per `config/decisions.yaml`, the following decisions remain `PENDING` or `PROVISIONAL`:
- `D-01` (Source of verified flare labels): `PENDING` (Gate G3)
- `D-02` (Time matching tolerance): `PENDING` (Gate G3)
- `D-03` (Onset/peak/end definition): `PENDING` (Gate G3)
- `D-04` (Partial flare treatment): `PENDING` (Gate G3)
- `D-05` (Window length $W=60\text{ s}$): `PROVISIONAL` (Gate G5)
- `D-06` (Window stride $S=10\text{ s}$): `PROVISIONAL` (Gate G5)
- `D-07` (Forecast horizon $\Delta t_{\text{horizon}}$): `PENDING` (Gate G6)
- `D-08` (Quiet-Sun negative interval definition): `PENDING` (Gate G3)
- `D-09` (Channel selection `COUNTS`): `PROVISIONAL` (Gate G1)
- `D-10` (Time system alignment): `PROVISIONAL` (Gate G1)
- `D-11` (Class imbalance handling): `PENDING` (Gate G7)
- `D-12` (Train/val/test split strategy): `PENDING` (Gate G7)
- `D-13` (Cadence and quality thresholds): `PROVISIONAL` (Gate G2)
- `D-14` (Gap splitting and segment duration thresholds): `PENDING` (Gate G4)
- `D-15` (Minimum positive events for main experiment): `PENDING` (Gate G3)
- `D-17` (GTI boundary convention): `PENDING` (Gate G4)
- `D-18` (Causal baseline lookback duration): `PENDING` (Gate G5)
- `D-19` (Rolling trend parameter $K$): `PENDING` (Gate G5)
- `D-20` (Coverage fraction threshold): `PENDING` (Gate G5)

---

## 6. Final Acceptance Gate Notice

Stage 14 automated checks are complete. Human final acceptance testing is required before the project is declared complete.

The human researcher will execute the independent verification suite and record findings in [`docs/acceptance/ACCEPTANCE_CHECKLIST.md`](../../docs/acceptance/ACCEPTANCE_CHECKLIST.md) using the reference mapping in [`docs/acceptance/VERIFICATION_BUNDLE.md`](../../docs/acceptance/VERIFICATION_BUNDLE.md).
