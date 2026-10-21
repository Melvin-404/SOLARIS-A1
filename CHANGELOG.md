# CHANGELOG

All notable changes to the `SOLARIS-A1` project are documented in this file.
Commit dates and timestamps are recorded directly from Git history.

---

## [Stage 14] - 2026-10-21 (Pending Commit)
### Status: AUTOMATED CHECKS COMPLETE (Human Acceptance Required)
- **Automated Integration Suite:**
  - Implemented end-to-end synthetic pipeline test (`tests/integration/test_pipeline_synthetic.py`).
  - Implemented synthetic dual-run reproducibility test (`tests/integration/test_reproducibility_synthetic.py`).
  - Implemented edge-case and failure-mode test harness (`tests/integration/test_failure_modes.py`).
  - Implemented AST static safeguard scanner (`tests/integration/test_static_safeguards.py`).
- **Audit and Verification Scripts:**
  - Added dependency auditor `scripts/check_dependencies.py`.
  - Added real-data isolated reproducibility verifier `scripts/check_real_reproducibility.py`.
  - Added master pipeline audit runner `scripts/run_full_pipeline_check.py`.
- **Documentation and Acceptance Preparation:**
  - Added technical test report (`docs/18_test_report.md`).
  - Added reproducibility checklist (`docs/19_reproducibility_checklist.md`).
  - Added scientific research limitations register (`docs/20_limitations.md`).
  - Prepared human acceptance checklist (`docs/acceptance/ACCEPTANCE_CHECKLIST.md`).
  - Prepared verification bundle with independent commands (`docs/acceptance/VERIFICATION_BUNDLE.md`).
- **Audit Outcome:** 215/215 tests passed; pip check passed; zero data/raw mutations; 10/10 deterministic artifacts match bit-for-bit.

---

## [Stage 13] - 2026-10-21 15:26:11 +0530 (Commit: `0772f71`)
### Status: COMPLETE
- Implemented pure pipeline status evaluation engine (`src/solar_flare/status.py`).
- Implemented cryptographic schema and artifact integrity checker (`src/solar_flare/integrity.py`).
- Integrated status displays and cryptographic health checks into Streamlit dashboard overview.
- Added comprehensive unit tests for status, schema validation, and test-set lock tampering detection (`tests/test_status.py`, `tests/test_integrity.py`).

---

## [Stage 12] - 2026-10-21 15:01:38 +0530 (Commit: `1b89842`)
### Status: COMPLETE
- Implemented multipage Streamlit local research dashboard (`dashboard/app.py`, `dashboard/pages/1..7`).
- Implemented read-only artifact loaders with caching (`dashboard/loaders.py`).
- Added automated AST read-only enforcement tests (`tests/test_readonly_dashboard.py`).
- Dashboard operates strictly in read-only mode with zero data mutation or automatic training.

---

## [Stage 11] - 2026-10-21 14:47:07 +0530 (Commit: `72f8073`)
### Status: PILOT / PROVISIONAL (Human Gate G9 Review Pending)
- Implemented single-shot scientific evaluation engine (`src/solar_flare/evaluation/`).
- Computed window-level confusion matrices, PR-AUC, ROC-AUC, and Brier calibration scores.
- Implemented event-level metrics (event detection rate, false trigger rate, detection latency).
- Evaluated models from pilot experiment `PROTO_STAGE10_DRAFT_001` on sealed test set.
- Produced comprehensive evaluation report (`results/evaluation/evaluation_report.md`).

---

## [Stage 10] - 2026-10-21 14:30:09 +0530 (Commit: `b12b026`)
### Status: PILOT / DRAFT (Executed under Protocol `PROTO_STAGE10_DRAFT_001`)
- Implemented automated model training harness for Logistic Regression, Random Forest, and XGBoost.
- Implemented chronological block splitting with purge gap to prevent temporal leakage.
- Cryptographically sealed and locked test set prior to model selection (`results/training/test_set_lock.json`).
- Selected champion model based exclusively on validation PR-AUC.

---

## [Stage 9] - 2026-10-21 14:17:53 +0530 (Commit: `97e4281`)
### Status: COMPLETE (Export Strictly Blocked Pending Gate G3/G6)
- Implemented dataset export architecture (`src/solar_flare/export/`).
- Enforced hard policy guards: export strictly blocked when labelling policy is in `DRAFT` status.
- Generated audit documentation for blocked export states (`results/exports/BLOCKED_DETECTION.md`, `BLOCKED_PREDICTION.md`).

---

## [Stage 8] - 2026-10-21 14:03:11 +0530 (Commit: `545e951`)
### Status: PROVISIONAL (Development Run Pending Gate G5)
- Implemented GTI-respecting sliding window extractor ($W=60\text{ s}$, $S=10\text{ s}$).
- Built causal feature library (statistical moments, morphological derivatives, causal hardness ratios).
- Implemented causal baseline lookback estimator ($600\text{ s}$) with strict no-lookahead assertions.
- Extracted window features for all valid continuous segments without cross-boundary leakage.

---

## [Stage 7] - 2026-10-21 13:41:06 +0530 (Commit: `152bd7f`)
### Status: PROVISIONAL (Development Run Pending Gate G4)
- Implemented GTI-aware observation filtering and gap segmentation engine (`src/solar_flare/preprocessing/`).
- Enforced zero interpolation and zero gap bridging across invalid intervals.
- Produced segmented observation files and sample-level reconciliation audit table.

---

## [Stage 6] - 2026-10-21 13:21:10 +0530 (Commit: `7e13713`)
### Status: COMPLETE (Policy Drafted; Labelling Blocked Pending Gate G3)
- Conducted ground-truth catalogue research (GOES, RHESSI, PRADAN).
- Drafted scientific labelling policy (`docs/08_labelling_policy.md`) with all decisions marked `PENDING`.
- Implemented hard policy gate requiring explicit `APPROVED` status before generating supervised labels.

---

## [Stage 5] - 2026-10-21 12:54:02 +0530 (Commit: `5d735b3`)
### Status: COMPLETE (Candidates Unverified)
- Implemented exploratory data analysis suite for SoLEXS light curves.
- Evaluated count distributions, background flux variance, and observation duty cycles.
- Detected candidate transient intervals, strictly labelling all candidates as `CANDIDATE - UNVERIFIED`.

---

## [Stage 4] - 2026-10-21 12:42:21 +0530 (Commit: `add9495`)
### Status: PROVISIONAL (Pending Gate G1)
- Implemented Level-1 FITS data quality validator and GTI parser.
- Evaluated observation cadence stability, dropout rates, and non-positive value flags.
- Confirmed SDD1 GTI table is empty for observation date 2026-10-18.
- Established provisional mapping for flux column `COUNTS` and elapsed seconds time system.
