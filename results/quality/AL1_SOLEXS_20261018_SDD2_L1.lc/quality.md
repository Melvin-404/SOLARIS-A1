# Data Quality Report: `AL1_SOLEXS_20261018_SDD2_L1.lc`

> **PROVISIONAL STATUS NOTICE (Gate G1 / G2 Pending):**
> All column roles, time systems, and quality thresholds in this report are strictly **PROVISIONAL**.
> Column roles require confirmation by the student researcher at Gate G1.
> Quality thresholds require confirmation at Gate G2. No data has been modified, filtered, or interpolated.

---

## Summary Overview

- **File Stem:** `AL1_SOLEXS_20261018_SDD2_L1.lc`
- **Role Confirmation Status:** `PROVISIONAL`
- **Stage 4 Assessment Status:** `PROVISIONAL pending G1`
- **Sampling Cadence (Median):** `1.0 s`
- **Cadence Gaps Detected:** `0`
- **GTI Observation Status:** `VALID`
- **GTI Covered Fraction:** `94.24%`
- **Samples Inside GTI:** `81,425`
- **Samples Outside GTI:** `4,975`

---

## Quality Checks Table

| Check Name | Status | Key Metric / Count | Details |
| :--- | :--- | :--- | :--- |
| `check_non_finite` | **WARN** | NaN: 4849, +inf: 0, -inf: 0 | Observed 4849 NaNs, 0 +inf, and 0 -inf samples. |
| `check_negative_values` | **PASS** | Negative: 0 | No negative values detected. |
| `check_duplicate_timestamps` | **PASS** | Duplicates: 0 | All timestamps are unique. |
| `check_time_ordering` | **PASS** | Backward steps: 0 | Timestamps are strictly non-decreasing. |
| `check_zero_runs` | **PASS** | Zero count: 137, Zero runs: 0 | Observed 137 zero counts across 0 runs (run length >= 5). Maximum run length: 0 samples. |
| `check_quality_flags` | **NOT_APPLICABLE** | Total samples: 0 | No quality flag column available or column is null (UNRESOLVED pending G1). |
| `check_candidate_spikes` | **WARN** | Candidate spikes: 5238 | Labelled: candidate spike — not a verified event. Threshold: z > 5.0 |

---

## Diagnostic Figures Generated

1. **Time Coverage & GTI Intervals:** [`time_coverage.png`](time_coverage.png)
2. **Cadence Histogram:** [`cadence_histogram.png`](cadence_histogram.png)
3. **Count Distribution (Linear & Log):** [`count_distribution.png`](count_distribution.png)
4. **Classified & Flagged Samples:** [`flagged_samples.png`](flagged_samples.png)
