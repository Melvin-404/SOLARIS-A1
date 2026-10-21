# SOLARIS-A1: Data Quality Assessment Methods (Stage 4)

## Overview

Stage 4 of `SOLARIS-A1` (*Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations*) establishes an empirical, observational data quality assessment protocol for Aditya-L1 SoLEXS Level-1 light-curve and Good Time Interval (GTI) data.

All quality metrics and diagnostic routines in this stage adhere strictly to two foundational principles:
1. **Zero Data Mutation:** No clipping of negative values, no imputation of NaNs with zero, no dropping of anomalous samples, and no interpolation of gaps. All raw data remains 100% bit-for-bit immutable.
2. **Strict Scientific Neutrality:** No candidate statistical spike is labelled as a solar flare or physical event. No scientific conclusions are declared. All candidate roles and thresholds are strictly **PROVISIONAL pending Gate G1 and G2 confirmation**.

---

## Architectural Principles and Pipeline Separation

```
data/raw/ (Read-Only)
   │
   ├─► roles.py ─────────► results/quality/column_role_evidence.json & .md
   │
   ├─► checks.py (Pure) ──► Non-finite, Negative, Ordering, Zeros, Spikes
   │
   ├─► cadence.py ────────► Empirical Cadence & Gap Analysis
   │
   ├─► gti_coverage.py ───► GTI Coverage Quantification (Non-filtering)
   │
   └─► report.py ─────────► results/quality/<stem>/ (Figures & Reports)
                            results/quality/summary.csv
                            results/quality/AWAITING_G1.md
```

---

## Quality Checks Methodology

Each check in [`src/solar_flare/quality/checks.py`](../src/solar_flare/quality/checks.py) is a pure, side-effect-free mathematical function.

### 1. Non-Finite Sample Detection (`check_non_finite`)
- **Metric:** Counts NaN, positive infinity ($+\infty$), and negative infinity ($-\infty$) separately.
- **Physical Rationale:** Telemetry packet corruption, detector dead-time overflow, or missing downlink frames manifest as non-finite IEEE 754 float representations. In the examined dataset (`AL1_SOLEXS_20261018_SDD2_L1.lc.gz`), exactly **4,849 NaNs** (5.61%) are observed.
- **Handling Rule:** NaNs must never be replaced with zeros; doing so would falsely indicate that zero X-ray photons were recorded during an unmeasured interval.
- **Status Thresholds:** `PASS` if non-finite count == 0; `WARN` if $> 0$.

### 2. Negative Value Detection (`check_negative_values`)
- **Metric:** Counts all finite values strictly less than zero ($x < 0$).
- **Physical Rationale:** Photon counting instruments (such as Silicon Drift Detectors) cannot register physical negative photon counts. If background subtraction has occurred upstream, negative residual flux can theoretically appear. In the Level-1 dataset examined, zero negative values were found (minimum count is 0.0).
- **Handling Rule:** Negative values must never be clipped to zero. Any negative value is reported as a potential pipeline failure or upstream subtraction artefact.
- **Status Thresholds:** `PASS` if negative count == 0; `FAIL` if $> 0$.

### 3. Timestamp Ordering and Monotonicity (`check_time_ordering`)
- **Metric:** Computes first differences $\Delta t_i = t_{i+1} - t_i$ and counts all backward steps ($\Delta t_i < 0$).
- **Physical Rationale:** Time-series analysis and sliding-window feature extraction assume strictly chronological time evolution. Backward steps indicate clock resynchronization, packet reordering, or counter wrap-around.
- **Status Thresholds:** `PASS` if backward steps == 0; `FAIL` if $> 0$.

### 4. Duplicate Timestamp Detection (`check_duplicate_timestamps`)
- **Metric:** Identifies repeated timestamps ($t_i = t_j$ with $i \neq j$) and records total duplicate occurrences and first examples.
- **Physical Rationale:** Duplicate timestamps corrupt sliding-window strides and autocorrelation features.
- **Status Thresholds:** `PASS` if duplicates == 0; `WARN` if $> 0$.

### 5. Contiguous Zero-Run Analysis (`check_zero_runs`)
- **Metric:** Tracks contiguous sequences of finite, exact zeros ($x_i == 0.0$) meeting or exceeding a minimum length threshold (`min_zero_run_length = 5`).
- **Physical Rationale:** Exact zero counts can represent true low-emission solar quiescent states, but extended consecutive zero runs often signify telemetry hold, shutter closure, or detector electronics freeze. Segregating zero runs from NaNs allows later stages to distinguish quiet-Sun intervals from telemetry voids.
- **Status Thresholds:** `PASS` if zero runs == 0; `WARN` if $> 0$.

### 6. Quality Flag Tabulation (`check_quality_flags`)
- **Metric:** Tabulates raw frequencies of unique values in dedicated flag columns.
- **Methodological Limitation:** Because no hardware flag column is present in the Level-1 `.lc.gz` RATE table, flag parsing evaluates to `NOT_APPLICABLE` (or `UNRESOLVED`). If an external flag array is provided, raw distributions are tabulated without assuming semantic meanings until Gate G1.

### 7. Statistical Candidate Spike Detection (`check_candidate_spikes`)
- **Metric:** Computes robust z-scores using the median and Median Absolute Deviation (MAD):
  $$\text{MAD} = \text{median}\left(|x_i - \text{median}(x)|\right)$$
  $$\text{Scale} = 1.4826 \times \text{MAD}$$
  $$z_{\text{robust}, i} = \frac{x_i - \text{median}(x)}{\text{Scale}}$$
  Candidate spikes are flagged when $z_{\text{robust}, i} > 5.0$.
- **CRITICAL SCIENTIFIC DISTINCTION:** Statistical spikes are explicitly labelled **"candidate spike — not a verified event"**. A high-z outlier can arise from cosmic ray hits, telemetry single-event upsets (SEUs), calibration pulses, or genuine microflares. Model training and event labelling are strictly prohibited from utilizing these candidate spikes as ground-truth flare labels.

---

## Cadence and Gap Analysis

Implemented in [`src/solar_flare/quality/cadence.py`](../src/solar_flare/quality/cadence.py):

1. **Cadence Estimation (`estimate_cadence`):**
   - Positive time differences $\Delta t > 0$ are analyzed to derive:
     - Median cadence ($\Delta t_{\text{median}}$)
     - Empirical mode ($\Delta t_{\text{mode}}$)
     - Minimum and maximum steps ($\Delta t_{\text{min}}, \Delta t_{\text{max}}$)
     - Standard deviation ($\sigma_{\Delta t}$)
   - In `AL1_SOLEXS_20261018_SDD2_L1.lc.gz`, the derived median cadence is exactly **1.0000 s**, matching the nominal `TIMEDEL` header keyword.
2. **Gap Detection (`find_cadence_gaps`):**
   - A cadence gap is declared when $\Delta t_i > \Delta t_{\text{median}} \times \text{tolerance\_factor}$.
   - The tolerance factor defaults to `1.5` (marked `PROVISIONAL` in `config/default.yaml`).
   - For a 1 s cadence, any step $> 1.5\text{ s}$ is recorded with its start timestamp, end timestamp, and missing step count.

---

## GTI Coverage Quantification

Implemented in [`src/solar_flare/quality/gti_coverage.py`](../src/solar_flare/quality/gti_coverage.py):

- **Non-destructive Quantification:** GTI intervals define verified good observation periods (e.g. orbit daytime, Sun in field-of-view, detector high voltage stable). The quantifier measures the covered duration and covered fraction without removing any samples outside GTI.
- **Zero-Row Rule:** If a GTI file has zero rows (such as `AL1_SOLEXS_20261018_SDD1_L1.gti.gz`), the system records `"GTI EMPTY FOR THIS OBSERVATION"`. It never attempts to substitute another file or synthesize artificial intervals.
- **Refusal on Unconfirmed Columns:** If the configured columns (`START`, `STOP`) are missing, loading refuses to execute, preventing silent misalignment.

---

## Gate G1 and G2 Human Approval Protocol

No scientific conclusions, feature extraction, or model training may proceed until the human student researcher reviews and approves:
- **Gate G1:** Confirmation of candidate column roles (`TIME`, `COUNTS`), time system (`MJD 40587` / Unix epoch), and detector pairing.
- **Gate G2:** Confirmation of quality thresholds (`cadence_tolerance_factor = 1.5`, `spike_z_score_threshold = 5.0`, `min_zero_run_length = 5`).
