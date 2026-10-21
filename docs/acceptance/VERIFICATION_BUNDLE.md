# Independent Verification Bundle

**Project:** `SOLARIS-A1`  
**Purpose:** Independent Verification of Completion Report Claims (Stages 4–14)  
**Target Audience:** Human Researcher / External Scientific Auditor  

This document maps every primary scientific and architectural claim made across the stage completion reports (`results/**/STAGE*_COMPLETION.md`) to the specific artifact file path and the exact terminal command that a human reviewer can execute independently to verify that claim.

---

## 1. Stage-by-Stage Verification Map

### Stage 4: Raw Quality Assessment & GTI Verification
- **Claim:** SDD2 has 8 GTI intervals with 1.0 s nominal cadence; SDD1 GTI table has zero rows and must not be used.
- **Artifacts:**
  - `results/quality/STAGE4_COMPLETION.md`
  - `data/processed/quality/AL1_SOLEXS_20261018_SDD2_L1_summary.csv`
  - `results/quality/column_role_evidence.json`
- **Independent Verification Command:**
  ```powershell
  python -c "import pandas as pd; df = pd.read_csv('data/processed/quality/AL1_SOLEXS_20261018_SDD2_L1_summary.csv'); print(df[['metric', 'value']])"
  ```
- **Expected Result:** `gti_intervals` is 8; `nominal_cadence` is 1.0s; `null_count` is 0.

---

### Stage 5: Exploratory Data Analysis & Candidate Bursts
- **Claim:** Variability metrics computed; candidate bursts detected and strictly flagged `CANDIDATE - UNVERIFIED`.
- **Artifacts:**
  - `results/eda/STAGE5_COMPLETION.md`
  - `results/eda/AL1_SOLEXS_20261018_SDD2_L1_candidate_bursts.csv`
  - `results/eda/AL1_SOLEXS_20261018_SDD2_L1_variability_summary.csv`
- **Independent Verification Command:**
  ```powershell
  python -c "import pandas as pd; df = pd.read_csv('results/eda/AL1_SOLEXS_20261018_SDD2_L1_candidate_bursts.csv'); print(df['candidate_label'].unique())"
  ```
- **Expected Result:** Output contains only `['CANDIDATE - UNVERIFIED']`. Zero claims of verified flares.

---

### Stage 6: Ground-Truth Labelling Protocol & Policy Gate
- **Claim:** Labelling policy is in `DRAFT` status; supervised labelling is hard-blocked pending Gate G3 human approval.
- **Artifacts:**
  - `results/labels/STAGE6_COMPLETION.md`
  - `docs/08_labelling_policy.md`
  - `config/decisions.yaml`
- **Independent Verification Command:**
  ```powershell
  pytest tests/test_labels.py -k "policy or draft" -v
  ```
- **Expected Result:** Tests pass confirming that the labelling engine raises `PolicyNotApprovedError` under `DRAFT` policy.

---

### Stage 7: Preprocessing, Gap Segmentation & Reconciliation
- **Claim:** Zero interpolation; gap segmentation splits intervals exceeding `max_gap_seconds` (2.0s); sample reconciliation audit accounts for 100% of raw rows.
- **Artifacts:**
  - `results/preprocessing/STAGE7_COMPLETION.md`
  - `data/processed/segments/AL1_SOLEXS_20261018_SDD2_L1/reconciliation_audit.csv`
  - `data/processed/segments/AL1_SOLEXS_20261018_SDD2_L1/segment_summary.csv`
- **Independent Verification Command:**
  ```powershell
  python -c "import pandas as pd; df = pd.read_csv('data/processed/segments/AL1_SOLEXS_20261018_SDD2_L1/reconciliation_audit.csv'); print(df)"
  ```
- **Expected Result:** `unaccounted_samples` is 0; raw samples equal sum of valid segment samples and excluded samples.

---

### Stage 8: Sliding Windows & Causal Feature Extraction
- **Claim:** Causal features ($W=60\text{ s}$, $S=10\text{ s}$) never look ahead of window reference time; zero cross-segment windows.
- **Artifacts:**
  - `results/features/STAGE8_COMPLETION.md`
  - `data/processed/features/AL1_SOLEXS_20261018_SDD2_L1/window_index.csv`
  - `data/processed/features/AL1_SOLEXS_20261018_SDD2_L1/window_features.csv`
- **Independent Verification Command:**
  ```powershell
  pytest tests/test_causal_features.py tests/test_windows.py -v
  ```
- **Expected Result:** All tests pass confirming temporal causality and absence of cross-boundary windows.

---

### Stage 9: Dataset Export & Gate Enforcement
- **Claim:** Dataset export module prevents unapproved exports and records blocked status manifests.
- **Artifacts:**
  - `results/exports/STAGE9_COMPLETION.md`
  - `results/exports/BLOCKED_DETECTION.md`
  - `results/exports/BLOCKED_PREDICTION.md`
- **Independent Verification Command:**
  ```powershell
  python src/solar_flare/export/export_dataset.py --task detection
  ```
- **Expected Result:** Refuses export with exit code 1 / blocked status, referencing unapproved Gate G3 policy.

---

### Stage 10: Model Training & Test Set Sealing
- **Claim:** Models trained under protocol `PROTO_STAGE10_DRAFT_001` on validation data only; test set cryptographically sealed and locked prior to model selection.
- **Artifacts:**
  - `results/training/STAGE10_COMPLETION.md`
  - `results/training/test_set_lock.json`
  - `docs/14_training_protocol.md`
- **Independent Verification Command:**
  ```powershell
  python -c "import json; lock = json.load(open('results/training/test_set_lock.json')); print('Locked Hash:', lock['test_set_sha256'][:16]); print('Status:', lock['lock_status'])"
  ```
- **Expected Result:** `Locked Hash: d20058b8862f9bb6`, `Status: LOCKED`.

---

### Stage 11: Scientific Single-Shot Test Evaluation
- **Claim:** Sealed test set evaluated exactly once under frozen protocol; window-level and event-level metrics computed; prevalence reported alongside all scores.
- **Artifacts:**
  - `results/evaluation/STAGE11_COMPLETION.md`
  - `results/evaluation/evaluation_report.md`
  - `results/evaluation/metrics_summary.json`
- **Independent Verification Command:**
  ```powershell
  pytest tests/test_evaluation_guard.py tests/test_event_metrics.py tests/test_window_metrics.py -v
  ```
- **Expected Result:** All evaluation integrity and metric computation tests pass.

---

### Stage 12: Streamlit Dashboard Foundation
- **Claim:** Local Streamlit application operates in read-only mode, without auto-training or file mutation.
- **Artifacts:**
  - `results/dashboard/STAGE12_COMPLETION.md`
  - `dashboard/app.py`
  - `tests/test_readonly_dashboard.py`
- **Independent Verification Command:**
  ```powershell
  pytest tests/test_readonly_dashboard.py -v
  ```
- **Expected Result:** All AST tests pass confirming zero training calls, zero subprocesses, and zero file write modes.

---

### Stage 13: Pipeline Status & Cryptographic Lineage Integrity
- **Claim:** Status module evaluates every stage purely without side effects; cryptographic checker validates hashes and catches simulated test set tampering.
- **Artifacts:**
  - `results/integration/STAGE13_COMPLETION.md`
  - `src/solar_flare/status.py`
  - `src/solar_flare/integrity.py`
- **Independent Verification Command:**
  ```powershell
  pytest tests/test_status.py tests/test_integrity.py -v
  ```
- **Expected Result:** All status evaluation and tamper-detection unit tests pass.

---

### Stage 14: Master Integration, Reproducibility & Safeguards
- **Claim:** 215 automated tests pass; full pipeline check runner exits 0; real-data development pipeline is 100% deterministic; static AST safeguards verify no leakage or interpolation.
- **Artifacts:**
  - `results/checks/full_check_*.md`
  - `docs/18_test_report.md`
  - `docs/19_reproducibility_checklist.md`
  - `docs/20_limitations.md`
- **Independent Verification Command:**
  ```powershell
  python scripts/run_full_pipeline_check.py
  ```
- **Expected Result:** Master verification runner executes all 9 checks and exits with code `0`.
