# STAGE 11 — SCIENTIFIC EVALUATION COMPLETION REPORT

**Project:** `SOLARIS-A1` (Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations)  
**Execution Timestamp:** `2026-10-21T09:17:00+00:00`  
**Pipeline Stage:** Stage 11 — Scientific Evaluation  
**Status:** `FRAMEWORK COMPLETE — LIVE TEST EVALUATION BLOCKED PENDING GATE G8`  
**Gate Clearance Status:** Awaiting Gate G8 (Pre-Evaluation Human Authorization)  

---

## 1. Executive Summary & Objective Realization

Stage 11 establishes the complete, production-grade, reproducible scientific evaluation framework for SOLARIS-A1.

Key capabilities delivered:
1. **Window-Level Metric Engine (`window_metrics.py`)**: Computes precision, recall, F1 (with explicit, tracked `zero_division` parameter), confusion matrix (TP, FP, TN, FN), and PR-AUC. Mandates explicit reporting of positive class prevalence alongside every metric. Handles unverified `<NA>` labels through auditable exclusion without imputation.
2. **Event-Level Macro Detection Engine (`event_metrics.py`)**: Merges consecutive sliding window predictions within an approved `merge_gap_seconds` buffer (default 60 s) into contiguous candidate flare episodes. Evaluates physical event recall against independent ground-truth catalogues and quantifies onset timing errors (median and IQR).
3. **Operational False-Alarm Analysis (`false_alarms.py`)**: Normalizes false-alarm rates strictly by verified GTI-covered science observation hours, preventing artificial rate dilution from unobserved night or SAA downtime.
4. **Reference Baselines (`baseline.py`)**:
   - **Threshold Baseline**: Heuristic based on causal peak-to-baseline flux ratio fitted strictly on training data (maximizing training F1), rigorously guarded against test/val leakage (`TestLeakageError`).
   - **Climatological Baseline**: Constant probability forecast matching training set prevalence.
   - **Persistence Baseline**: Causal persistence of observed window state at $t_0$.
5. **Probability Calibration Assessment (`calibration.py`)**: Equal-width reliability diagrams, Expected Calibration Error (ECE), Maximum Calibration Error (MCE), and Brier score. Strictly observational—no post-hoc test set recalibration is permitted.
6. **Block Bootstrap Uncertainty (`uncertainty.py`)**: Resamples entire observation segments rather than rows to honor 83.3% sliding window autocorrelation. Enforces a scientific minimum block floor ($n \ge 5$); withholds CI computation with an explicit audit reason if the threshold is not met.
7. **Single-Shot Evaluation Engine (`evaluate_locked_models.py`)**: Enforces cryptographic lock verification, verifies 0 reads occurred during Stage 10 tuning, logs single test access in `access_log.jsonl`, updates status to `EVALUATED_ONCE`, and strictly refuses any repeated evaluation on the same experiment directory.
8. **Dashboard Contract (`reporting.py`)**: Automatically produces `dashboard_contract.json` specifying exact schemas consumed by Stage 12 (interactive exploration) and Stage 13 (dashboard).

---

## 2. Files Created and Modified

### A. New Scientific Modules (`src/solar_flare/evaluation/`)
- `src/solar_flare/evaluation/__init__.py`: Package export interface.
- `src/solar_flare/evaluation/window_metrics.py`: Window classification metrics and prevalence calculation.
- `src/solar_flare/evaluation/event_metrics.py`: Window merging, event overlap matching, and timing error quantification.
- `src/solar_flare/evaluation/false_alarms.py`: GTI-covered false-alarm rates and missed-event tables.
- `src/solar_flare/evaluation/baseline.py`: Threshold, Climatological, and Persistence baseline models.
- `src/solar_flare/evaluation/calibration.py`: Reliability binning, ECE, MCE, and Brier score.
- `src/solar_flare/evaluation/uncertainty.py`: Block bootstrap resampling with segment floor guard.
- `src/solar_flare/evaluation/reporting.py`: Markdown, JSON, CSV reports, and `dashboard_contract.json`.

### B. New CLI Driver
- `scripts/evaluate_locked_models.py`: Main single-shot evaluation script with Gate G8 verification, cryptographic integrity check, and `EVALUATED_ONCE` state lockdown.

### C. New Documentation
- `docs/15_evaluation_methods.md`: Comprehensive methodological documentation covering window vs event metrics, PR-AUC, embargoes, covered-time normalization, calibration, and single-shot evaluation governance.

### D. New Unit Test Suites (`tests/`)
- `tests/test_window_metrics.py`: Exact hand-computed confusion matrix, precision/recall/F1, NA exclusion, non-binary rejection.
- `tests/test_event_metrics.py`: Merge gap behavior, known detections, misses, false alarms, and timing errors.
- `tests/test_false_alarms.py`: GTI-covered hour normalization vs. wall clock.
- `tests/test_baseline.py`: Training-only fitting, validation/test leakage rejection, climatological/persistence behavior.
- `tests/test_calibration.py`: Exact Brier score, ECE convergence on calibrated data.
- `tests/test_uncertainty.py`: Segment floor refusal and valid empirical percentile CIs.
- `tests/test_reporting.py`: Refusal without lock verification, refusal on existing evaluation directory.
- `tests/test_single_shot.py`: Verification that a second invocation on the same experiment directory strictly refuses.

### E. Modified Files
- `README.md`: Updated Current Status to Stage 11, indexed `docs/15_evaluation_methods.md`, and added Stage 11 execution commands.
- `scripts/train_models.py`: Added explicit `import joblib`.

---

## 3. Automated Test Verification

All tests run in `.venv` on Windows 11 with synthetic fixtures:
```powershell
.venv\Scripts\python -m pytest -v
```

**Results:**
- **Stage 11 New Tests:** 18 passed in 2.10s (0 failed).
- **Total Repository Test Suite:** **179 passed in 3.68s (0 failed)**.

Key Test Verifications:
- `test_single_shot_evaluation_enforcement`: Confirmed that after an experiment directory has been evaluated, a second call to `evaluate_locked_models.py` exits with non-zero and refuses execution.
- `test_threshold_baseline_fitting_and_leakage_guard`: Confirmed that fitting a threshold baseline with validation or test indices immediately raises `TestLeakageError`.
- `test_false_alarm_rate_uses_covered_time_not_wall_clock`: Confirmed that uncorrected wall-clock time does not dilute false alarm rates.

---

## 4. Live Workspace Execution & Stop Condition Record

Execution of the single-shot evaluation CLI on the live workspace:
```powershell
.venv\Scripts\python scripts/evaluate_locked_models.py
```
- **Exit Code:** `1` (Clean execution refusal).
- **Blocking Reasons Identified:**
  1. Gate G8 approval is NOT recorded. Human authorization required before test set evaluation.
  2. No trained experiment directory found with status `TRAINED_PENDING_TEST_EVALUATION` (Stage 10 model training awaits Gate G7 protocol freeze).
- **Audit File Generated:** `results/experiments/AWAITING_G8.md`.

---

## 5. Mandatory Scientific Governance & Limitations

### Crucial Project Limitations:
1. **Single Observation Day (2026-10-18):** A single-day dataset cannot support an independent chronological test split. Results on this dataset remain strictly `PILOT` under Decision D-15.
2. **Window Overlap:** Adjacent windows share 83.3% of raw observations. Window-level metrics must not be interpreted as independent trials.
3. **Prevalence Mandate:** Solar flares are rare; window prevalence is low. PR-AUC is reported as the primary metric, with prevalence explicitly tabulated in every report. Accuracy is prohibited as a headline.
4. **Forecasting Skill Prerequisite:** Prediction tasks require outperforming both the climatological baseline (training prevalence) and persistence baseline before any claim of predictive skill can be made.

### Mandatory Scientific Statement:
> **Results are computed values only. Human interpretation required at Gate G9.**  
> Test evaluation on the real sealed test set has NOT been performed and awaits Gate G8 human approval.
