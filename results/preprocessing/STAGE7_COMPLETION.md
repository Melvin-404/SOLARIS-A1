# Stage 7 Completion Report: Preprocessing and GTI-Aware Segmentation

**Project:** `SOLARIS-A1` (Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations)  
**Stage:** Stage 7 — Preprocessing and GTI-Aware Segmentation  
**Date:** 2026-10-21  
**Status:** PROVISIONAL DEVELOPMENT RUN COMPLETE — FINAL RUN BLOCKED PENDING G4 APPROVAL  
**Scientific Gate:** Gate G4 (Decisions D-14, D-17 Pending Human Approval)  

---

## 1. Executive Summary & Mandatory Declarations

Stage 7 implements non-destructive sample filtering, GTI boundary filtering, and continuous observation segmentation at approved gap thresholds. Every sample exclusion is mathematically tracked in an auditable reconciliation table asserting:
$$N_{\text{original}} = N_{\text{retained}} + \sum N_{\text{excluded}}$$

### Mandatory Declarations
- **Zero Raw File Mutation:** Raw observation files under `data/raw/` were verified 100% hash-identical before and after execution.
- **Zero Interpolation:** Data is never interpolated, reconstructed, or gap-filled. Missing points strictly define segment boundaries.
- **Detector Isolation:** SDD1 and SDD2 GTIs are strictly isolated. SDD1 GTI has 0 rows and correctly yielded 0 segments.
- **Stage 8 Progression Statement:** Stage 8 may proceed in PROVISIONAL mode for development. Final feature datasets require D-14 approval.

---

## 2. Files Created and Modified

### A. Documentation Created
1. `docs/10_preprocessing_methods.md` — Detailed step-by-step filtering specification, parameters, reconciliation formulas, and limitations.

### B. Configuration and Decisions Modified
1. `config/decisions.yaml` — Updated D-14 with parameter definitions and added D-17 (GTI boundary convention) with status `PENDING`.
2. `config/default.yaml` — Added `preprocessing:` section containing provisional defaults and pending status tags.
3. `docs/01_decision_log.md` — Appended D-14 update, D-17 entry, and Stage 7 architecture notes.
4. `.gitignore` — Added `!results/preprocessing/` and `!results/preprocessing/**`.

### C. Source Code Created (`src/solar_flare/preprocessing/`)
1. `src/solar_flare/preprocessing/__init__.py` — Package exports.
2. `src/solar_flare/preprocessing/filters.py` — Filtering functions (`exclude_non_finite`, `exclude_negative`, `exclude_flagged`, `resolve_duplicate_timestamps`, `sort_by_time`). Each returns `(filtered_df, exclusion_log_df)`.
3. `src/solar_flare/preprocessing/gti_apply.py` — Good Time Interval application with boundary options (`START_INCLUSIVE_STOP_EXCLUSIVE`, `START_EXCLUSIVE_STOP_INCLUSIVE`, `BOTH_INCLUSIVE`) and zero-row GTI handling.
4. `src/solar_flare/preprocessing/segmentation.py` — Continuous segmentation (`segment_continuous`) with `ParameterPendingError` guard and minimum segment length filtering.
5. `src/solar_flare/preprocessing/audit.py` — `ProcessingAudit` accumulator, reconciliation assertion (`retained + excluded == original`), and multi-format exporters (`.csv`, `.json`, `.md`).

### D. Command-Line Tools & Scripts Created
1. `scripts/run_preprocessing.py` — Complete CLI runner supporting `--stem`, `--final` gate refusal guard, and provisional development mode.

### E. Automated Test Suites Created
1. `tests/test_filters.py` — 7 tests covering NaN/inf exclusion, negative exclusion, flag exclusion, duplicate timestamp policies (`ERROR`, `KEEP_FIRST`, `KEEP_LAST`), and chronological sorting.
2. `tests/test_gti_apply.py` — 5 tests verifying boundary conditions, empty GTI handling, and invalid boundary error triggers.
3. `tests/test_segmentation.py` — 3 tests verifying gap threshold splits (`dt > max_gap`), short segment exclusion, and pending parameter refusal.
4. `tests/test_audit.py` — 4 tests verifying exact reconciliation, discrepancy error trigger, hash mismatch trigger, and multi-format audit export.
5. `tests/test_pending_guard.py` — 2 tests verifying final mode refusal when decisions are pending and success when approved.
6. `tests/test_no_interpolation.py` — 1 static code scan verifying zero occurrences of prohibited interpolation/imputation methods (`interp`, `interpolate`, `fillna`, `ffill`, `bfill`, `resample`).

### F. Results and Reports Created
1. `results/preprocessing/raw_hashes_before.json` — Cryptographic snapshot of all raw files before processing.
2. `results/preprocessing/raw_hashes_after.json` — Cryptographic snapshot of all raw files after processing (100% match).
3. `results/preprocessing/AWAITING_G4.md` — Formal refusal notice documenting pending decisions for Gate G4.
4. `results/preprocessing/summary.csv` — Pipeline execution summary.
5. `results/preprocessing/run_manifest.json` — Detailed execution manifest.
6. `results/preprocessing/audit_AL1_SOLEXS_20261018_SDD2_L1.csv` — Row-level exclusion audit (5,021 excluded records).
7. `results/preprocessing/audit_AL1_SOLEXS_20261018_SDD2_L1.json` — Machine-readable audit data.
8. `results/preprocessing/audit_AL1_SOLEXS_20261018_SDD2_L1.md` — Human-readable retention and segmentation audit.
9. `results/preprocessing/STAGE7_COMPLETION.md` — This stage completion report.

---

## 3. Commands Executed and Exit Codes

| Command | Exit Code | Purpose / Result |
| :--- | :--- | :--- |
| `python scripts/run_preprocessing.py --final` | `1` (Expected) | **Final Mode Guard Verification:** Refused execution and generated `results/preprocessing/AWAITING_G4.md` because G1, G2, D-14, and D-17 remain PENDING. |
| `python scripts/run_preprocessing.py --stem all` | `0` (Success) | **Development Run:** Processed light curve in PROVISIONAL mode, generated 4 continuous segments, and recorded all audits. |
| `python -m pytest -v` | `0` (Success) | **Automated Test Suite:** All 102 unit tests passed cleanly in 2.95s. |

---

## 4. Test Suite Counts

- Total tests: **102 passed**, 0 failed, 0 warnings.
  - Preprocessing filters (`test_filters.py`): 7 passed
  - GTI boundary application (`test_gti_apply.py`): 5 passed
  - Continuous segmentation (`test_segmentation.py`): 3 passed
  - Audit reconciliation (`test_audit.py`): 4 passed
  - Pending approval guard (`test_pending_guard.py`): 2 passed
  - Zero interpolation static scan (`test_no_interpolation.py`): 1 passed
  - Prior stages (0–6): 80 passed

---

## 5. Per-File Sample Retention & Reconciliation Table

**Observation Stem:** `AL1_SOLEXS_20261018_SDD2_L1`  
**Raw Source File:** `data/raw/AL1_SOLEXS_20261018_SDD2_L1.lc.gz`

| Category | Sample Count | Percentage of Original | Notes |
| :--- | :--- | :--- | :--- |
| **Original Total Samples** | **86,400** | **100.0000%** | Full 24-hour observation (1.0 s nominal cadence) |
| **Retained Samples** | **81,379** | **94.1887%** | Contained in 4 valid continuous segments |
| **Total Excluded Samples** | **5,021** | **5.8113%** | Sum of all filtered samples |
| ↳ Excluded: `NON_FINITE` | 4,849 | 5.6123% | NaN reads during night-to-day transitions |
| ↳ Excluded: `OUTSIDE_GTI` | 134 | 0.1551% | Samples falling outside paired GTI intervals |
| ↳ Excluded: `SEGMENT_TOO_SHORT` | 38 | 0.0440% | Samples in segments with duration $< 60.0\text{ s}$ |
| ↳ Excluded: `NEGATIVE_VALUE` | 0 | 0.0000% | No negative counts observed |
| ↳ Excluded: `DUPLICATE_TIMESTAMP`| 0 | 0.0000% | Timestamps are strictly unique |
| ↳ Excluded: `QUALITY_FLAG` | 0 | 0.0000% | No flag column defined in Level-1 RATE table |

**Mathematical Reconciliation Verification:**
$$\text{Retained } (81,379) + \text{Excluded } (5,021) = 86,400 \equiv \text{Original } (86,400)$$
$$\text{Reconciliation Discrepancy} = 0 \text{ samples} \quad [\mathbf{PASS}]$$

---

## 6. Continuous Segmentation Catalog (PROVISIONAL)

Output path: `data/processed/segments/AL1_SOLEXS_20261018_SDD2_L1/`  
Format: **CSV** (pyarrow is absent from requirements; each file contains `TIME`, `COUNTS`, `gti_flag`, `segment_id`, `status: PROVISIONAL`).

| Segment ID | Start (s) | End (s) | Duration (s) | Duration (min) | Samples | Median Cadence (s) | Gap Before (s) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `AL1_SOLEXS_20261018_SDD2_L1_seg_001` | `1792286428.0` | `1792316628.0` | 30,200.0 | 503.3 min | 30,201 | 1.0000 | 0.0 | `PROVISIONAL` |
| `AL1_SOLEXS_20261018_SDD2_L1_seg_002` | `1792316631.0` | `1792323431.0` | 6,800.0 | 113.3 min | 6,801 | 1.0000 | 3.0 | `PROVISIONAL` |
| `AL1_SOLEXS_20261018_SDD2_L1_seg_003` | `1792323469.0` | `1792341677.0` | 18,208.0 | 303.5 min | 18,209 | 1.0000 | 38.0 | `PROVISIONAL` |
| `AL1_SOLEXS_20261018_SDD2_L1_seg_004` | `1792341831.0` | `1792367998.0` | 26,167.0 | 436.1 min | 26,168 | 1.0000 | 74.0 | `PROVISIONAL` |

---

## 7. Raw File Cryptographic Hash Verification

| Filename | SHA-256 (Before Processing) | SHA-256 (After Processing) | Immutability Status |
| :--- | :--- | :--- | :--- |
| `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` | `9415f2457bfc108ba561e20420fb34f694787f5f24461dcd6cb24a4a00580f9e` | `9415f2457bfc108ba561e20420fb34f694787f5f24461dcd6cb24a4a00580f9e` | **PASS (100% IDENTICAL)** |
| `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` | `0e12dab0cf21f3246a75f901f1af1e10e2e55bcd81ea8936801399355a9b1e2b` | `0e12dab0cf21f3246a75f901f1af1e10e2e55bcd81ea8936801399355a9b1e2b` | **PASS (100% IDENTICAL)** |
| `AL1_SOLEXS_20261018_SDD2_L1.lc.gz` | `1c1a5371663267d39a8e89c8d29640aed69dcad427f0d8139b97e61071746c94` | `1c1a5371663267d39a8e89c8d29640aed69dcad427f0d8139b97e61071746c94` | **PASS (100% IDENTICAL)** |
| `AL1_SOLEXS_20261018_SDD2_L1.pi.gz` | `7914183ae74d2ad46b916b3759a4af4e234ed526d4bf098eeeeef8c369c3eb85` | `7914183ae74d2ad46b916b3759a4af4e234ed526d4bf098eeeeef8c369c3eb85` | **PASS (100% IDENTICAL)** |
| `README.md` | `cbbf486887b536309840b400543a8388077a3550c8f3873c778f5cddea2f9dd0` | `cbbf486887b536309840b400543a8388077a3550c8f3873c778f5cddea2f9dd0` | **PASS (100% IDENTICAL)** |

---

## 8. Format Used for Segments and Rationale

- **Format:** `CSV` (Comma-Separated Values).
- **Rationale:** `pyarrow` is absent from `requirements.txt`. In compliance with project constraints, no external library was added. CSV is universal, text-inspectable, and lossless for IEEE floating-point timestamps and integer counts.

---

## 9. Unresolved Decisions & Gate G4 Requirements

The following decisions remain **PENDING** in `config/decisions.yaml` and require human researcher approval:
1. **Decision D-14:** `max_gap_seconds` (provisional: `2.0 s`) and `min_segment_seconds` (provisional: `60.0 s`).
2. **Decision D-17:** `gti_boundary_convention` (provisional: `START_INCLUSIVE_STOP_EXCLUSIVE`).
3. **Duplicate Timestamp Policy:** Confirmation of default `ERROR` policy.
4. **Quality Flags:** Confirmation of excluded flag list when Level-2 flags become available.

---

## 10. Known Scientific Limitations

- **Single Observation Epoch:** Current pipeline has only been executed on `2026-10-18`.
- **Night-to-Day Occultation Dropouts:** 4,849 samples were dropped due to NaNs at orbit transitions.
- **SDD1 Non-Availability:** SDD1 GTI has 0 rows for this date and cannot produce valid segments.

---

## 11. Stage 8 Clearance

> **Stage 8 may proceed in PROVISIONAL mode for development.**  
> **Final feature datasets require D-14 approval.**
