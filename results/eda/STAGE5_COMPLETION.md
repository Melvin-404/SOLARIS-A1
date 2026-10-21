# Stage 5 Completion Report: Exploratory Data Analysis (CANDIDATES UNVERIFIED)

> **CRITICAL SCIENTIFIC STATUS STATEMENT:**
> **All candidate intervals identified in Stage 5 are strictly CANDIDATE — UNVERIFIED.**
> Nothing produced in this stage represents a verified solar flare, ground truth label, or machine learning target.
> Event comparison status: **NOT PERFORMED — no independent event records supplied**.
> **Stage 6 may begin its source research now. Label generation remains blocked until G3.**

---

## 1. Files Created and Modified

### Created Modules:
- [`src/solar_flare/eda/__init__.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/eda/__init__.py) — Package interface for EDA subsystem.
- [`src/solar_flare/eda/variability.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/eda/variability.py) — Pure functions for time-based rolling summaries, non-parametric dispersion, and count histograms.
- [`src/solar_flare/eda/bursts.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/eda/bursts.py) — Robust running baseline with edge handling and candidate burst detection.
- [`src/solar_flare/eda/event_comparison.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/eda/event_comparison.py) — Event comparison scaffolding (NOT PERFORMED default).
- [`src/solar_flare/eda/plots.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/eda/plots.py) — Diagnostic plotting routines (PNG at 150 dpi and PDF).
- [`scripts/run_eda.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/scripts/run_eda.py) — CLI runner for Stage 5 pipeline.

### Created Documentation and Templates:
- [`docs/05_eda_methods.md`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/docs/05_eda_methods.md) — Comprehensive explanation of baseline algorithms, burst criteria, and statistical methods.
- [`docs/05_eda_findings.md`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/docs/05_eda_findings.md) — Findings report with automated numerical section and narrative sections for the student researcher.
- [`docs/06_event_record_schema.md`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/docs/06_event_record_schema.md) — Standardized schema template for external event catalogs to be sourced in Stage 6.

### Created Exploratory Notebook:
- [`notebooks/02_eda.ipynb`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/notebooks/02_eda.ipynb) — Interactive Jupyter notebook with visible candidate disclaimer banner.
- [`results/eda/notebook_runs/02_eda_executed.ipynb`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/eda/notebook_runs/02_eda_executed.ipynb) — Executed notebook output artifact.

### Modified Files:
- [`config/default.yaml`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/config/default.yaml) — Added `eda` configuration section with PROVISIONAL exploratory thresholds (`baseline_span_seconds: 600.0`, `burst_threshold_sigma: 5.0`, `burst_min_duration_seconds: 10.0`, `gallery_max_panels: 9`, `rolling_window_seconds: 60.0`).
- [`README.md`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/README.md) — Added Stage 5 EDA description, CLI execution commands, and notebook instructions.

### Created Unit Test Suites:
- [`tests/test_variability.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/tests/test_variability.py) — Tests for exact mean, median, MAD, IQR, CV, and histogram segregation.
- [`tests/test_bursts.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/tests/test_bursts.py) — Tests for injected burst detection, flat series zero-candidate behavior, and empty header preservation.
- [`tests/test_event_comparison.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/tests/test_event_comparison.py) — Tests for NOT PERFORMED branches and synthetic overlap matching.
- [`tests/test_no_label_writes.py`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/tests/test_no_label_writes.py) — Static code analysis ensuring EDA modules never write to datasets or label paths.

### Created EDA Artifacts:
- [`results/eda/raw_hashes_before.json`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/eda/raw_hashes_before.json) & [`raw_hashes_after.json`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/eda/raw_hashes_after.json)
- [`results/eda/AL1_SOLEXS_20261018_SDD2_L1.lc/`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/eda/AL1_SOLEXS_20261018_SDD2_L1.lc/):
  - `variability_summary.csv`
  - `candidate_bursts.csv` (all rows: `status = "CANDIDATE — UNVERIFIED"`)
  - `light_curve.png` & `light_curve.pdf`
  - `count_distribution.png`
  - `coverage_timeline.png`
  - `burst_gallery.png`
  - `eda_log.txt`
  - `run_manifest.json`

---

## 2. Commands Executed and Exit Codes

| Command Line | Exit Code | Purpose / Result |
| :--- | :--- | :--- |
| `.venv\Scripts\python -m pytest -v` | **0** | Executed complete unit test suite across 61 tests; 100% pass |
| `.venv\Scripts\python scripts/run_eda.py --out-dir results/eda` | **0** | Executed automated EDA pipeline on real observation data |
| `.venv\Scripts\jupyter nbconvert --to notebook --execute notebooks/02_eda.ipynb --output 02_eda_executed.ipynb --output-dir results/eda/notebook_runs` | **0** | Headless notebook execution completed successfully |
| Post-execution SHA-256 Hash Verification | **0** | Verified bit-for-bit raw data immutability |

---

## 3. Test Results Summary

- **Total Tests Collected:** 61
- **Passed:** 61 (100%)
- **Failed:** 0
- **Skipped:** 0
- **Test Modules:**
  - `tests/test_bursts.py`: 3 passed
  - `tests/test_cadence.py`: 4 passed
  - `tests/test_config.py`: 6 passed
  - `tests/test_event_comparison.py`: 3 passed
  - `tests/test_gti_coverage.py`: 4 passed
  - `tests/test_inspection.py`: 9 passed
  - `tests/test_logging.py`: 2 passed
  - `tests/test_manifest.py`: 11 passed
  - `tests/test_no_label_writes.py`: 2 passed
  - `tests/test_paths.py`: 4 passed
  - `tests/test_quality_checks.py`: 8 passed
  - `tests/test_roles.py`: 2 passed
  - `tests/test_variability.py`: 3 passed

---

## 4. Candidate Counts and Exploratory Metrics

From [`results/eda/AL1_SOLEXS_20261018_SDD2_L1.lc/candidate_bursts.csv`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/results/eda/AL1_SOLEXS_20261018_SDD2_L1.lc/candidate_bursts.csv):

| Candidate ID | Start (s) | End (s) | Duration (s) | Peak Time (s) | Peak Value (counts) | Peak/Baseline Ratio | Samples | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CAND_001` | 1792320583.0 | 1792320601.0 | 18.0 | 1792320598.0 | 48.0 | 2.82x | 19 | **CANDIDATE — UNVERIFIED** |
| `CAND_002` | 1792320610.0 | 1792320628.0 | 18.0 | 1792320627.0 | 58.0 | 3.22x | 19 | **CANDIDATE — UNVERIFIED** |
| `CAND_003` | 1792320655.0 | 1792320670.0 | 15.0 | 1792320667.0 | 45.0 | 2.50x | 16 | **CANDIDATE — UNVERIFIED** |
| `CAND_004` | 1792351036.0 | 1792351045.0 | 9.0 | 1792351042.0 | 80.0 | 1.95x | 10 | **CANDIDATE — UNVERIFIED** |

**Total Candidate Bursts:** 4 (all with status `CANDIDATE — UNVERIFIED`).

---

## 5. Raw File SHA-256 Hash Verification (Before vs After)

| File in `data/raw/` | SHA-256 Before EDA | SHA-256 After EDA | Match Status |
| :--- | :--- | :--- | :--- |
| `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` | `9415f2457bfc108ba561e20420fb34f694787f5f24461dcd6cb24a4a00580f9e` | `9415f2457bfc108ba561e20420fb34f694787f5f24461dcd6cb24a4a00580f9e` | **MATCH (100% Identical)** |
| `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` | `0e12dab0cf21f3246a75f901f1af1e10e2e55bcd81ea8936801399355a9b1e2b` | `0e12dab0cf21f3246a75f901f1af1e10e2e55bcd81ea8936801399355a9b1e2b` | **MATCH (100% Identical)** |
| `AL1_SOLEXS_20261018_SDD2_L1.lc.gz` | `1c1a5371663267d39a8e89c8d29640aed69dcad427f0d8139b97e61071746c94` | `1c1a5371663267d39a8e89c8d29640aed69dcad427f0d8139b97e61071746c94` | **MATCH (100% Identical)** |
| `AL1_SOLEXS_20261018_SDD2_L1.pi.gz` | `7914183ae74d2ad46b916b3759a4af4e234ed526d4bf098eeeeef8c369c3eb85` | `7914183ae74d2ad46b916b3759a4af4e234ed526d4bf098eeeeef8c369c3eb85` | **MATCH (100% Identical)** |

---

## 6. Unresolved Scientific Questions

1. **Origin of Candidate Bursts:** Do candidate bursts `CAND_001` through `CAND_004` correspond to actual physical solar transient emission (e.g., B-class or sub-A microflares), detector thermal drift, or telemetry single-event upsets?
2. **Cluster Behavior:** Candidates `CAND_001`, `CAND_002`, and `CAND_003` occur within ~90 seconds of each other (around $t \approx 1792320600\text{ s}$, which corresponds to approximately `2026-10-18 10:50 UTC`). Is this a multi-peaked impulsive event or detector oscillation?
3. **Appropriateness of Exploratory Thresholds:** Is a 600 s running median with a $5.0\sigma$ threshold optimal across diverse solar activity levels, or should threshold scaling adapt to quiescent background flux?
4. **Physical Meaning of Isolated Zero Counts:** Does the presence of 137 finite zero counts amidst a mean count rate of ~13.35 counts/s signify true low-flux moments or 1-second telemetry bin dropouts?

---

## 7. Known Limitations

1. **Single Day Observation:** Observations reflect only `2026-10-18`. Generalization to active-Sun periods requires multi-day datasets.
2. **Absence of External Verification:** Event comparison status remains `NOT PERFORMED`. No external flare labels are associated with these data.
3. **No Spatial Information:** SoLEXS Level-1 light-curve counts are full-disk integrated; spatial localisation of emission requires comparison with imaging instruments (e.g. SDO/AIA or SUIT).

---

## 8. Stage 6 Readiness Assessment

- **Stage 6 may begin its source research now. Label generation remains blocked until G3.**
- Sourcing, evaluation, and documentation of candidate external ground-truth event catalogues (e.g. NOAA/GOES X-ray flare catalogue, ISSDC PRADAN published flare event lists) can proceed immediately under Stage 6 guidelines.
