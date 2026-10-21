# Stage 4 Completion Report: Data Quality Assessment (PROVISIONAL)

> **CRITICAL STAGE STATUS STATEMENT:**
> **Stage 4 completion is PROVISIONAL until G1 is recorded as CONFIRMED.**
> All column roles, time systems, quality thresholds, and GTI associations in this report are observational and provisional. No scientific conclusions are declared. No data in `data/raw/` has been clipped, interpolated, imputed, or modified.

---

## 1. Files Created and Modified

### Created Source and Utility Modules:
- [`src/solar_flare/quality/__init__.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/quality/__init__.py) — Package interface exposing all quality checks, cadence tools, GTI coverage routines, and role evidence compilers.
- [`src/solar_flare/quality/checks.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/quality/checks.py) — Pure functional quality checks (non-finite, negative, ordering, duplicates, zero runs, quality flags, robust MAD candidate spikes).
- [`src/solar_flare/quality/cadence.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/quality/cadence.py) — Empirical cadence derivation and tolerance-factor gap detection.
- [`src/solar_flare/quality/gti_coverage.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/quality/gti_coverage.py) — Non-destructive GTI interval loader and coverage quantifier.
- [`src/solar_flare/quality/roles.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/quality/roles.py) — Column-role evidence compiler.
- [`src/solar_flare/quality/report.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/quality/report.py) — Per-file quality reports and Matplotlib diagnostic figure generation.
- [`scripts/run_quality.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/scripts/run_quality.py) — Command-line runner for Stage 4 quality pipeline.

### Created Configuration and Registry Files:
- [`config/column_roles.yaml`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/config/column_roles.yaml) — PROVISIONAL candidate column roles for light curves and GTI tables.
- [`config/decisions.yaml`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/config/decisions.yaml) — Machine-readable decision register tracking D-01 through D-14.

### Created Documentation:
- [`docs/04_quality_methods.md`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/docs/04_quality_methods.md) — Comprehensive explanation of quality methods, mathematical formulations, and limitations.

### Modified Existing Files:
- [`config/default.yaml`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/config/default.yaml) — Added `quality` threshold configuration section (`cadence_tolerance_factor: 1.5`, `spike_z_score_threshold: 5.0`, `min_zero_run_length: 5`).
- [`docs/01_decision_log.md`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/docs/01_decision_log.md) — Updated decisions D-09, D-10, and D-13 to PROVISIONAL status with evidence links and Stage 4 progress notes.
- [`README.md`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/README.md) — Added Stage 4 Quality Assessment overview, CLI instructions, and Gate G1/G2 next steps.
- [`tests/test_config.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/tests/test_config.py) — Updated stage status assertion to support progression.

### Created Unit Test Suites:
- [`tests/test_quality_checks.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/tests/test_quality_checks.py) — Tests for pure checks using synthetic fixtures.
- [`tests/test_cadence.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/tests/test_cadence.py) — Tests for cadence statistics and gap detection.
- [`tests/test_gti_coverage.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/tests/test_gti_coverage.py) — Tests for GTI loading, coverage fraction, zero-row behavior, and missing column refusal.
- [`tests/test_roles.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/tests/test_roles.py) — Tests for role compilation and evidence generation.

### Created Results Artifacts:
- [`results/quality/summary.csv`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/quality/summary.csv) — Primary cross-file quality summary table.
- [`results/quality/column_role_evidence.json`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/quality/column_role_evidence.json) & [`.md`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/quality/column_role_evidence.md) — Compiled evidence for all candidate roles.
- [`results/quality/AWAITING_G1.md`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/quality/AWAITING_G1.md) — Human Gate G1 action checklist.
- [`results/quality/run_manifest.json`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/quality/run_manifest.json) — Execution metadata log.
- [`results/quality/raw_hashes_before.json`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/quality/raw_hashes_before.json) & [`raw_hashes_after.json`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/quality/raw_hashes_after.json) — Hash integrity records.
- [`results/quality/AL1_SOLEXS_20261018_SDD2_L1.lc/`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/quality/AL1_SOLEXS_20261018_SDD2_L1.lc/):
  - `quality.json`
  - `quality.md`
  - `time_coverage.png` (150 dpi)
  - `cadence_histogram.png` (150 dpi)
  - `count_distribution.png` (150 dpi)
  - `flagged_samples.png` (150 dpi)

---

## 2. Commands Executed and Exit Codes

| Command Line | Exit Code | Purpose |
| :--- | :--- | :--- |
| `.venv\Scripts\python scripts/check_manifest.py data/manifests/manifest.csv` | **0** | Verified Stage 2 manifest prerequisite integrity |
| `.venv\Scripts\python -m pytest -v` | **0** | Development test suite verification across all 50 unit tests |
| `.venv\Scripts\python scripts/run_quality.py --raw-dir data/raw --manifest data/manifests/manifest.csv --out-dir results/quality` | **0** | Executed automated quality assessment pipeline on real data |
| Post-execution SHA-256 Verification Script | **0** | Verified bit-for-bit identical hashes before and after execution |

---

## 3. Test Results Summary

- **Total Tests Collected:** 50
- **Passed:** 50 (100%)
- **Failed:** 0
- **Skipped:** 0
- **Execution Time:** 1.41 s

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\melvi\Desktop\SOLARIS-A1
collected 50 items

tests/test_cadence.py (4 tests) ........................................ PASSED
tests/test_config.py (6 tests) ......................................... PASSED
tests/test_gti_coverage.py (4 tests) ................................... PASSED
tests/test_inspection.py (9 tests) ..................................... PASSED
tests/test_logging.py (2 tests) ........................................ PASSED
tests/test_manifest.py (11 tests) ...................................... PASSED
tests/test_paths.py (4 tests) .......................................... PASSED
tests/test_quality_checks.py (8 tests) ................................. PASSED
tests/test_roles.py (2 tests) .......................................... PASSED
============================= 50 passed in 1.41s ==============================
```

---

## 4. Per-File Summary Table (Counts Only — PROVISIONAL Status)

Extracted from [`results/quality/summary.csv`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/quality/summary.csv):

| File Stem | n_samples | n_nan | n_pos_inf | n_neg_inf | n_negative | n_zero | n_dup_ts | n_back_step | n_cadence_gaps | GTI Status | GTI Covered Frac | n_outside_gti | n_candidate_spikes | Role Status | Overall Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `AL1_SOLEXS_20261018_SDD1_L1.gti` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **GTI EMPTY FOR THIS OBSERVATION** | N/A | N/A | N/A | `PROVISIONAL` | `UNPAIRED_GTI — inspected read-only` |
| `AL1_SOLEXS_20261018_SDD2_L1.lc` | 86,400 | 4,849 | 0 | 0 | 0 | 137 | 0 | 0 | 0 | **VALID** (8 intervals) | 0.9424 (94.24%) | 4,975 | 5,238 | `PROVISIONAL` | **`PROVISIONAL`** |
| `AL1_SOLEXS_20261018_SDD2_L1.pi` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **NOT_APPLICABLE** | N/A | N/A | N/A | `UNRESOLVED` | `OTHER — inspected read-only, not used in quality checks` |

---

## 5. Raw File SHA-256 Hash Verification (Before vs After)

Bit-for-bit immutability guarantee:

| File in `data/raw/` | SHA-256 Before Quality Assessment | SHA-256 After Quality Assessment | Match Status |
| :--- | :--- | :--- | :--- |
| `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` | `9415f2457bfc108ba561e20420fb34f694787f5f24461dcd6cb24a4a00580f9e` | `9415f2457bfc108ba561e20420fb34f694787f5f24461dcd6cb24a4a00580f9e` | **MATCH (100% Identical)** |
| `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` | `0e12dab0cf21f3246a75f901f1af1e10e2e55bcd81ea8936801399355a9b1e2b` | `0e12dab0cf21f3246a75f901f1af1e10e2e55bcd81ea8936801399355a9b1e2b` | **MATCH (100% Identical)** |
| `AL1_SOLEXS_20261018_SDD2_L1.lc.gz` | `1c1a5371663267d39a8e89c8d29640aed69dcad427f0d8139b97e61071746c94` | `1c1a5371663267d39a8e89c8d29640aed69dcad427f0d8139b97e61071746c94` | **MATCH (100% Identical)** |
| `AL1_SOLEXS_20261018_SDD2_L1.pi.gz` | `7914183ae74d2ad46b916b3759a4af4e234ed526d4bf098eeeeef8c369c3eb85` | `7914183ae74d2ad46b916b3759a4af4e234ed526d4bf098eeeeef8c369c3eb85` | **MATCH (100% Identical)** |

---

## 6. Column-Role Status and Evidence Reference

- **Evidence File:** [`results/quality/column_role_evidence.json`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/quality/column_role_evidence.json) and [`column_role_evidence.md`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/quality/column_role_evidence.md)
- **Role Statuses:**
  - `time`: `PROVISIONAL` (Column `TIME` in `RATE`, format `D`, monotonic 1.0 s step matching `DATE-OBS`, `TSTART=1792281600.0`, `MJDREFI=40587`).
  - `count_or_rate`: `PROVISIONAL` (Column `COUNTS` in `RATE`, format `D`, non-negative [0.0, 185.0], 4,849 NaNs).
  - `quality_flag`: `UNRESOLVED` (No dedicated flag column found in `RATE` table; requires human confirmation).
  - `gti_start`: `PROVISIONAL` (Column `START` in `GTI`, format `D`, monotonic timestamps on identical 1.792e9 epoch scale).
  - `gti_stop`: `PROVISIONAL` (Column `STOP` in `GTI`, format `D`, monotonic timestamps on identical 1.792e9 epoch scale).
  - `energy_or_channel`: `PROVISIONAL` (Header keywords `NUMBAND=4`, `FILTER='SDD2'`, spectral channels in `.pi` file).

---

## 7. Unresolved Scientific Questions

Copied from [`results/inventory/open_questions.md`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/inventory/open_questions.md) with Stage 4 updates:

1. **Physical Unit of `COUNTS`:** Column `COUNTS` in `RATE` has no recorded `TUNIT` keyword. Confirm whether values represent total raw integer counts per 1 s bin, count rate in counts/second ($c/s$), or calibrated flux.
2. **Physical Unit of `TIME`:** Column `TIME` has no recorded `TUNIT` keyword in table column metadata (though header provides `TIMEUNIT = 's'`). Confirm time unit is SI seconds.
3. **Time System in GTI Headers:** GTI headers do not record `TIMESYS` or `TIMEREF`. Numerical range matches `TIME` in `RATE` exactly, but official confirmation of reference clock is required.
4. **SDD1 Zero-Interval GTI:** `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` contains exactly 0 rows. Confirm whether detector SDD1 was unpowered, in calibration mode, or excluded during this observation.
5. **Quality Flags Source:** Since no bitmask flag column exists in Level-1 light-curve tables, confirm whether telemetry flags are published in auxiliary HK (housekeeping) files or if Level-1 data points are filtered purely by GTI intervals.
6. **Candidate Spike Interpretation:** 5,238 points exceed robust $z > 5.0$. Confirm the expected physical distribution of quiet-Sun micro-activity vs detector noise.

---

## 8. Known Limitations

1. **Single Observation Day:** Current dataset contains observations for only one UTC calendar day (`2026-10-18`). Quality metrics are indicative of this specific day and instrument configuration (SDD2).
2. **No Hardware Flag Bitmask:** Because no hardware flag column is present in `RATE`, samples during detector anomalies can only be distinguished via NaNs or by falling outside GTI intervals.
3. **Spectral PI Exclusion:** The `.pi.gz` product contains 340-channel spectra per 1-second interval (29,376,000 values) and is classified as `OTHER — inspected read-only, not used in quality checks`.

---

## 9. Prerequisites for Stage 5 and Progression Mode

- **Can Stage 5 Proceed in PROVISIONAL Mode?** **YES.**
  - Stage 5 (Data Cleaning and Non-Destructive Preparation / Segmentation) can be executed in `PROVISIONAL mode` using the provisional column roles (`TIME`, `COUNTS`, `START`, `STOP`) and provisional thresholds.
  - However, **no Stage 5 results, segments, or cleaned datasets may be interpreted scientifically until Gate G1 is formally confirmed by the human researcher.**
- **Prerequisites for Stage 5:**
  1. Virtual environment and dependencies active.
  2. Stage 4 quality summary table (`results/quality/summary.csv`) and per-file quality metrics available.
  3. Raw data hash immutability verified.
