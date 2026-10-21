# STAGE 8 COMPLETION REPORT — SLIDING WINDOWS AND CAUSAL FEATURE ENGINEERING

**Project:** `SOLARIS-A1` — Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations  
**Stage:** 8 — Sliding Windows and Feature Engineering  
**Mode:** PROVISIONAL (Development Run)  
**Execution Timestamp:** 2026-10-21T08:29:23 UTC / 2026-10-21T13:59:23 IST  
**Status:** COMPLETE (PROVISIONAL Development Run)  

---

## 1. Executive Summary

Stage 8 implements configurable, strictly intra-segment sliding windows, a documented library of 18 causal summary and morphological features, a strictly pre-window causal baseline helper, and a temporal leakage guard. 

For the observation date `2026-10-18` (SDD2 Level-1 light curve), sliding window extraction and causal feature engineering were executed across all 4 continuous segments produced by Stage 7. A total of **8,116 sliding windows** were generated with provisional window length $W = 60.0\text{ s}$ and stride $S = 10.0\text{ s}$ ($W/S = 6\times$ overlap). 

Key architectural achievements:
1. **Zero Segment Boundary / Gap Crossing:** Sliding windows are generated strictly within each continuous segment; no window spans a gap or segment boundary.
2. **Strictly Causal Feature Calculation:** Every feature $f_j(w_i)$ utilizes solely observations with timestamp $t \le w_{\text{end}} = t_0$.
3. **Strictly Pre-Window Causal Baseline:** Baselines are evaluated solely over $[w_{\text{start}} - 600\text{ s}, w_{\text{start}})$ within the identical segment. Never uses global, whole-file, or future data.
4. **Sample-Level Provenance Leakage Guard:** The temporal guard examines empirical sample timestamps ($t_{\max} \le w_{\text{end}}$); all 8,116 generated windows passed with zero future peeking.
5. **Zero Data Imputation / Zero Gap Filling:** Non-finite samples are excluded from pure statistical reductions and explicitly counted; no interpolation or imputation (`fillna`, `ffill`, etc.) was performed.
6. **Immutable Raw and Segment Data:** All raw data files and Stage 7 segment files were verified 100% hash-identical before and after execution.
7. **Refusal Guard for Final Mode:** `scripts/build_features.py --final` verified to exit 1 and refuse execution due to Gate G5 pending decisions (D-05, D-06, D-18, D-19, D-20).

---

## 2. Files Created and Modified

### Source Code (`src/solar_flare/features/`)
- [`src/solar_flare/features/__init__.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/features/__init__.py) — Module exports.
- [`src/solar_flare/features/windows.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/features/windows.py) — Configurable intra-segment sliding window generator (`generate_windows`), `WindowRecord` dataclass, and Gate G5 parameter guard.
- [`src/solar_flare/features/features.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/features/features.py) — Pure mathematical feature functions: `mean`, `median`, `std`, `robust_variability` ($1.4826 \times \text{MAD}$), `min`, `max`, `percentiles` (5th, 25th, 75th, 95th), `iqr`, `mean_abs_first_difference`, `max_abs_first_difference`, `temporal_slope`, `rolling_trend`, `peak_to_baseline_ratio`, `coverage_fraction`, `n_observed_samples`.
- [`src/solar_flare/features/baseline.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/features/baseline.py) — Strictly causal pre-window median baseline (`causal_baseline`).
- [`src/solar_flare/features/leakage_guard.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/features/leakage_guard.py) — Temporal provenance leakage guard (`check_no_future_samples`, `check_inputs_causal`) raising `LeakageError`.
- [`src/solar_flare/features/registry.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/features/registry.py) — `FeatureRegistry` cataloging scientific formulas, units, reason codes, and metadata.

### CLI Runner
- [`scripts/build_features.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/scripts/build_features.py) — Automated feature builder CLI supporting `--stem`, `--final`, and `--config`.

### Documentation
- [`docs/11_feature_dictionary.md`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/docs/11_feature_dictionary.md) — Comprehensive dictionary documenting all 18 features with exact equations, units, reason codes, and prominent warning against row-level dataset splitting.
- [`docs/12_windowing_methods.md`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/docs/12_windowing_methods.md) — Methodological specification on window geometry, reference time $t_0$, coverage fractions, overlap dynamics, and effective sample size.
- [`docs/01_decision_log.md`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/docs/01_decision_log.md) — Added decisions D-18, D-19, D-20 (PENDING) and updated architecture notes.
- [`README.md`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/README.md) — Updated project status, docs index, and added Stage 8 CLI section.

### Configuration
- [`config/default.yaml`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/config/default.yaml) — Added `features:` section with configurable parameters.
- [`config/decisions.yaml`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/config/decisions.yaml) — Registered decisions D-18, D-19, D-20 with status `PENDING`.
- [`.gitignore`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/.gitignore) — Whitelisted `!results/features/` and `!results/features/**`.

### Automated Unit Tests
- [`tests/test_windows.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/tests/test_windows.py) — Exact window count, boundary adherence, low coverage handling, and short segment handling.
- [`tests/test_features.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/tests/test_features.py) — Unit tests for constant series, linear series, MAD, IQR, percentiles, slope sample floor, baseline edge cases, and non-finite sample counting.
- [`tests/test_baseline.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/tests/test_baseline.py) — Isolation of pre-window samples and minimum sample count floor.
- [`tests/test_leakage_guard.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/tests/test_leakage_guard.py) — Injected future sample detection (`LeakageError`) and clean window verification.
- [`tests/test_pending_guard.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/tests/test_pending_guard.py) — Added Gate G5 refusal and approval tests.
- [`tests/test_no_interpolation.py`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/tests/test_no_interpolation.py) — Static code scan verifying zero interpolation/imputation calls in `features/`.

### Generated Results & Artifacts
- [`results/features/segment_hashes_before.json`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/results/features/segment_hashes_before.json) — Source segment SHA-256 pre-execution hashes.
- [`results/features/summary.csv`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/results/features/summary.csv) — Per-stem window and leakage summary.
- [`results/features/AL1_SOLEXS_20261018_SDD2_L1/build_log.json`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/results/features/AL1_SOLEXS_20261018_SDD2_L1/build_log.json) — Audit log containing run configuration, parameter statuses, metrics, and output hashes.
- `data/processed/features/AL1_SOLEXS_20261018_SDD2_L1/window_index.csv` — Full window index (8,116 rows).
- `data/processed/features/AL1_SOLEXS_20261018_SDD2_L1/window_features.csv` — Full 18-feature tabular dataset (8,116 rows).

---

## 2. Commands Executed and Exit Codes

| # | Command | Working Directory | Exit Code | Purpose |
|---|---------|-------------------|:---------:|---------|
| 1 | `.venv\Scripts\python -m pytest -v` | Repository Root | `0` | Automated regression test suite (120 tests passed) |
| 2 | `.venv\Scripts\python scripts/build_features.py --final` | Repository Root | `1` | Refusal check for Gate G5 pending parameters |
| 3 | `.venv\Scripts\python scripts/build_features.py --stem all` | Repository Root | `0` | Development feature generation across all segments |
| 4 | `.venv\Scripts\python scripts/check_manifest.py` | Repository Root | `0` | Immutability audit of raw FITS files |
| 5 | Segment Hash Audit (Python) | Repository Root | `0` | Immutability audit of Stage 7 segment files |
| 6 | Hand-Check Verification (Python) | Repository Root | `0` | Segment-by-segment window formula audit |

---

## 3. Test Suite Summary

- **Total Tests Run:** 120
- **Passed:** 120
- **Failed:** 0
- **Execution Time:** 2.38 s
- **Key Subsystem Breakdown:**
  - `test_windows.py`: 4 tests (count verification, boundary containment, low-coverage flag, short-segment handling).
  - `test_features.py`: 7 tests (pure statistical math, constant/linear series, MAD, IQR, percentiles, sample thresholds, zero-division protection, non-finite tracking).
  - `test_baseline.py`: 2 tests (strictly pre-window boundary enforcement, sample floor).
  - `test_leakage_guard.py`: 3 tests (injected future sample detection, clean window validation, dataset causality check).
  - `test_pending_guard.py`: 4 tests (Gate G4 & Gate G5 refusal and approval pathways).
  - `test_no_interpolation.py`: 1 test (static scan over `src/solar_flare/preprocessing/` and `src/solar_flare/features/` confirming zero imputation/interpolation).

---

## 4. Per-File and Per-Segment Window Counts

Configuration for Provisional Development Run:
- Window length ($W$): $60.0\text{ s}$
- Window stride ($S$): $10.0\text{ s}$
- Nominal cadence: $1.0\text{ s}$ ($N_{\text{expected}} = 60$)
- Minimum coverage fraction: $0.80$ ($N_{\text{obs}} \ge 48$)

| Segment ID | Start Time (s) | End Time (s) | Duration (s) | Window Count | Low Coverage Windows | Coverage % |
|------------|:--------------:|:------------:|:------------:|:------------:|:--------------------:|:----------:|
| `AL1_SOLEXS_20261018_SDD2_L1_seg_001` | 1,792,286,428.0 | 1,792,316,628.0 | 30,200.0 | 3,015 | 0 | 100.0% |
| `AL1_SOLEXS_20261018_SDD2_L1_seg_002` | 1,792,323,288.0 | 1,792,330,088.0 | 6,800.0 | 675 | 0 | 100.0% |
| `AL1_SOLEXS_20261018_SDD2_L1_seg_003` | 1,792,336,747.0 | 1,792,354,955.0 | 18,208.0 | 1,815 | 0 | 100.0% |
| `AL1_SOLEXS_20261018_SDD2_L1_seg_004` | 1,792,346,633.0 | 1,792,372,800.0 | 26,167.0 | 2,611 | 0 | 100.0% |
| **Total Across All Segments** | — | — | **81,375.0** | **8,116** | **0** | **100.0%** |

---

## 5. Hand-Check Verification Comparison

The theoretical number of sliding windows of duration $W$ and stride $S$ within a continuous segment of duration $D = t_{\text{end}} - t_{\text{start}}$ is given by:
$$N = \left\lfloor \frac{D - W}{S} \right\rfloor + 1$$

| Segment Identifier | Duration $D$ (s) | Formula Calculation | Extracted Windows | Status |
|--------------------|:----------------:|:-------------------:|:-----------------:|:------:|
| `seg_001` | 30,200.0 | $\lfloor (30,200 - 60)/10 \rfloor + 1 = 3,014 + 1 = \mathbf{3,015}$ | **3,015** | MATCH (Exact) |
| `seg_002` | 6,800.0 | $\lfloor (6,800 - 60)/10 \rfloor + 1 = 674 + 1 = \mathbf{675}$ | **675** | MATCH (Exact) |
| `seg_003` | 18,208.0 | $\lfloor (18,208 - 60)/10 \rfloor + 1 = 1,814 + 1 = \mathbf{1,815}$ | **1,815** | MATCH (Exact) |
| `seg_004` | 26,167.0 | $\lfloor (26,167 - 60)/10 \rfloor + 1 = 2,610 + 1 = \mathbf{2,611}$ | **2,611** | MATCH (Exact) |

Every segment extracted the exact mathematical window count predicted by the continuous windowing theorem.

---

## 6. Temporal Leakage Guard Audit

- **Guard Method:** [`check_no_future_samples`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/features/leakage_guard.py) logs empirical `max_time_used` for each window and asserts:
  $$\forall i \in \{1, \dots, N\}: \quad \text{max\_time\_used}_i \le w_{\text{end}, i}$$
- **Result:** **PASSED (100%)**
- **Offending Windows:** 0
- **Causality Status:** Real provenance verified; zero future observations accessed across all 8,116 windows.

---

## 7. Parameter Statuses and Approval Register

| Parameter | Decision ID | Status | Current Development Value | Authority Required |
|-----------|:-----------:|:------:|:-------------------------:|:------------------:|
| Window Length ($W$) | D-05 | `PROVISIONAL` | $60.0\text{ s}$ | Gate G5 (Human) |
| Window Stride ($S$) | D-06 | `PROVISIONAL` | $10.0\text{ s}$ | Gate G5 (Human) |
| Pre-Window Baseline Lookback | D-18 | `PENDING` | $600.0\text{ s}$ | Gate G5 (Human) |
| Rolling Trend Duration ($K$) | D-19 | `PENDING` | $15.0\text{ s}$ | Gate G5 (Human) |
| Minimum Coverage Fraction | D-20 | `PENDING` | $0.80$ ($80\%$) | Gate G5 (Human) |
| Non-Zero Baseline Threshold ($\epsilon$) | D-21 | `PROVISIONAL` | $10^{-6}$ | Gate G5 (Human) |
| Percentile Cutoffs | D-22 | `PROVISIONAL` | $[5, 25, 75, 95]$ | Gate G5 (Human) |

---

## 8. Immutability & Checksum Audit

### Raw Data Immutability (Stage 2 Manifest)
All 4 raw files in `data/raw/` were verified against `data/manifests/manifest.csv`:
- `AL1_SOLEXS_20261018_SDD2_L1.lc.gz`: `045e4aa09c8594d4cfbbd1ceea1d33cbcc77eec83713d7a8d5e8fb85566ee268` (UNCHANGED)
- `AL1_SOLEXS_20261018_SDD2_L1.gti`: `f4911f421ca6082269a844cc96d3fdf6c6bc527f6e09e13b836dc248d2bc00ee` (UNCHANGED)
- `AL1_SOLEXS_20261018_SDD1_L1.lc.gz`: `b193278912e6c518847bc0551c6c5ff85eb36d70bc235eead13f99aa9f743df2` (UNCHANGED)
- `AL1_SOLEXS_20261018_SDD1_L1.gti`: `4a4968bc93a9d701dfc142c6762aa8db77353fc7d4f93ee7cbe0e0e1eb815e98` (UNCHANGED)

### Preprocessed Segment Immutability (`results/features/segment_hashes_before.json`)
All 4 segment CSV files under `data/processed/segments/AL1_SOLEXS_20261018_SDD2_L1/` were verified 100% hash-identical:
- `seg_001.csv`: `3fd99bd34ea4abea7853c8660479d6e6d11cfe782496ffb5ea82cee5a4da1ec1` (UNCHANGED)
- `seg_002.csv`: `5590f27c8a0566d649edb2a75763875f257d113b26a8ca948fcbe39a23658506` (UNCHANGED)
- `seg_003.csv`: `507089fc484a5fd3ed33e7b2f392b5a9e2e770e67403f79b9e7683344f41fed7` (UNCHANGED)
- `seg_004.csv`: `a89bacae5b7afd8224b26f3524756f2d7cad0e5915a1f63a703089ec2570ab3d` (UNCHANGED)

---

## 9. Known Scientific Limitations

1. **Heavy Window Overlap:** With $W = 60\text{ s}$ and $S = 10\text{ s}$, adjacent windows overlap by $50\text{ s}$ ($83.3\%$). Any random row-level splitting into train and test sets will cause catastrophic data leakage, artificially inflating validation accuracy. Splitting must strictly group by continuous segment or time block (Stage 10).
2. **Effective Sample Size:** While 8,116 window instances exist, the number of statistically independent 60-second observation intervals across the day is at most $81,375 / 60 \approx 1,356$.
3. **Single Observation Date:** The current dataset comprises a single observation date (`2026-10-18`). Generalization to different solar activity levels and instrument background states cannot be demonstrated until multi-day observations are ingested.
4. **Initial Window Baselines:** Windows within the first $30\text{ s}$ of each segment have fewer than 30 prior samples and properly receive `baseline_reason = BASELINE_INSUFFICIENT` with `NaN` baseline and ratio, preserving strict causality.

---

## 10. Milestone Clearance: Stage 9 Gate

> **Gate Clearance Determination:**  
> **"Stage 9 detection export requires G3 and G5. Feature generation is complete in PROVISIONAL mode."**

Stage 8 is fully verified, mathematically tested, and reproducible. The codebase is fully prepared for Stage 9 detection dataset export once human approval is formally recorded for Gate G3 (Labelling Policy) and Gate G5 (Window & Feature Parameters).
