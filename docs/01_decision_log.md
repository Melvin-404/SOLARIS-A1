# Decision Log: SOLARIS-A1

## Overview
This document records all critical architectural, scientific, and methodological decisions for project `SOLARIS-A1` (*Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations*).

Status definitions:
- **OPEN:** Requires scientific review, investigation of data, or human student decision before implementation.
- **PROVISIONAL:** A temporary working default has been adopted for scaffolding, subject to formal review and student approval.
- **APPROVED:** Formally reviewed and approved by the student researcher.

---

## Decision Table

| ID | Decision / Question | Current Status | Owner | Stage Needed | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **D-01** | **Source of verified flare-event labels**<br>Which external solar flare catalogue will serve as ground truth (e.g., NOAA/GOES X-ray flare catalogue, ISRO/PRADAN published event lists, or Heliophysics Event Knowledgebase)? | **OPEN** | Student | Stage 6 | Must be an independently verified, scientifically accepted catalogue. TO BE VERIFIED FROM OFFICIAL DOCUMENTATION and student decision. |
| **D-02** | **Time-matching tolerance between event records and SoLEXS timestamps**<br>What temporal tolerance $\pm \Delta t$ should be applied when associating catalogue event timestamps with SoLEXS light-curve data? | **OPEN** | Student | Stage 6 / 7 | Different instruments may have slight offsets in timestamping, integration boundaries, or detector response onset. |
| **D-03** | **Definition of flare onset, peak, and end**<br>How are flare onset, peak, and end boundaries defined (e.g., standard catalogue times, derivative threshold crossing, or fraction of peak flux above pre-flare background)? | **OPEN** | Student | Stage 6 / 7 | Crucial for defining the exact window boundaries for flare activity in Task A and pre-flare exclusion in Task B. |
| **D-04** | **Treatment of ambiguous or partially observed events**<br>How should the pipeline treat flares that intersect with orbital night, GTI boundaries, or telemetry drops (truncate, discard, or flag as partial)? | **OPEN** | Student | Stage 4 / 7 | Incomplete events could introduce label noise if partial flux rise is truncated by a data gap. |
| **D-05** | **Window length ($W = 60\text{ s}$)**<br>Length of the sliding window for extracting time-series features in Task A. | **PROVISIONAL** | Student / Antigravity | Stage 8 | Provisional default set to 60 seconds based on typical impulsive flare timescales; subject to review after FITS cadence inspection. |
| **D-06** | **Window stride ($S = 10\text{ s}$)**<br>Stride step between consecutive sliding windows in Task A. | **PROVISIONAL** | Student / Antigravity | Stage 8 | Provisional default set to 10 seconds (83.3% overlap) to capture transient dynamics; subject to review regarding data volume and autocorrelation. |
| **D-07** | **Forecast horizon for Task B**<br>What prediction horizon(s) $\Delta t_{\text{horizon}}$ (e.g., 10 min, 30 min, 60 min) should be evaluated for the pre-flare prediction task? | **OPEN** | Student | Stage 14 | Prediction must occur strictly prior to flare onset $[t_{\text{pred}}, t_{\text{pred}} + \Delta t_{\text{horizon}}]$. Needs student scientific justification. |
| **D-08** | **Definition of verified negative intervals**<br>What criteria define a verified negative (non-flaring/quiet) interval (e.g., minimum temporal buffer from any catalogue flare, background flux stability threshold)? | **OPEN** | Student | Stage 7 / 10 | Essential to prevent contamination of negative training samples by microflares or flare decay tails. |
| **D-09** | **Energy band / light-curve channel selection**<br>Which SoLEXS energy band(s) or spectral channels should be utilized for light-curve feature extraction? | **PROVISIONAL** | Student | Stage 4 (Gate G1) | **Candidate:** RATE table column `COUNTS` in `AL1_SOLEXS_20261018_SDD2_L1.lc.gz`. Full-disk soft X-ray counts from SDD2 detector. Candidate evidence compiled in `results/quality/column_role_evidence.json`. Requires human confirmation at Gate G1. |
| **D-10** | **Time system alignment (UTC vs Mission Elapsed Time)**<br>Does SoLEXS light-curve data use UTC timestamps, Julian Date, or Mission Elapsed Time (MET), and is conversion needed to match external catalogues? | **PROVISIONAL** | Student | Stage 4 (Gate G1) | **Candidate:** Elapsed seconds since MJD 40587.0 (1970-01-01 00:00:00 UTC). Monotonic 1.0 s step matching `DATE-OBS`. Candidate evidence in `results/quality/column_role_evidence.json`. Requires human confirmation at Gate G1. |
| **D-11** | **Class-imbalance handling strategy**<br>How should the high rarity of solar flare windows relative to quiet-Sun windows be addressed (e.g., PR-AUC metrics, class weighting, sub-sampling, SMOTE)? | **OPEN** | Student | Stage 10 / 12 | Class imbalance management directly affects student model training; deferred entirely to student scientific choice. |
| **D-12** | **Train / Validation / Test split strategy**<br>What data splitting protocol should be enforced (e.g., strict chronological split, grouped-by-active-day split, or stratified-by-flare-class split)? | **OPEN** | Student | Stage 10 | Must avoid data leakage across adjacent sliding windows; requires strict temporal separation or day-level grouping. Approved by student. |
| **D-13** | **Quality check and cadence thresholds**<br>Threshold parameters for data quality assessment and cadence gap detection. | **PROVISIONAL** | Student | Stage 4 (Gate G2) | **Provisional thresholds:** `cadence_tolerance_factor = 1.5`, `spike_z_score_threshold = 5.0` (robust MAD), `min_zero_run_length = 5`. Recorded in `config/default.yaml` and `config/decisions.yaml`. Requires human confirmation at Gate G2. |
| **D-14** | **Handling of sub-cadence jitter and small telemetry dropouts**<br>What threshold of missing points within a nominal GTI interval triggers interpolation versus window rejection? | **OPEN** | Antigravity / Student | Stage 4 | TO BE VERIFIED FROM OFFICIAL DOCUMENTATION and empirical analysis in Stage 4. |
| **D-15** | **Quiescent background estimation methodology**<br>What algorithm should be used to estimate baseline background solar X-ray flux (e.g., running minimum, rolling lower quantile, or polynomial fit)? | **OPEN** | Student | Stage 5 / 9 | Critical for calculating baseline threshold triggers and excess flare flux metrics. |

---

## Decision Management Protocol
1. Any modification to the status of a decision must be recorded with date and rationale.
2. Decisions marked **Owner: Student** require direct review and confirmation by the human researcher.
3. No stage may transition to completion if any decision required for that stage remains in **OPEN** status.

---

## Stage Progress and Architecture Notes
- **Stage 1 (Configuration System Initialized):** The project configuration infrastructure (`config/default.yaml` and `src/solar_flare/config.py`) has been established. All domain and scientific parameters (window duration, stride, forecast horizon, matching tolerance, energy channels) are explicitly flagged as `PENDING` to ensure that no hardcoded scientific assumptions bypass student approval.
- **Stage 2 (Data Acquisition Protocol Established):** Official manual acquisition instructions ([`docs/data_acquisition.md`](data_acquisition.md)), provenance manifest schema ([`data/manifests/manifest_template.csv`](../data/manifests/manifest_template.csv)), and manifest disk verification tools ([`src/solar_flare/manifest.py`](../src/solar_flare/manifest.py) and [`scripts/check_manifest.py`](../scripts/check_manifest.py)) have been completed.
- **Unresolved Portal Questions (Student Manual Confirmation Required):**
  1. *Exact PRADAN Endpoint:* Record the final verified URL for the Aditya-L1 SoLEXS data search interface.
  2. *Product File Naming Format:* Confirm exact filename patterns for light-curve and GTI FITS files (e.g., whether files are compressed as `.fits.gz` or distributed as uncompressed `.fits`).
  3. *Observation Identifier Convention:* Confirm whether products are indexed by `OBS_ID`, `OBSERVATION_ID`, or date-timestamp strings on the portal table.
  4. *Time Coordinate System:* Verify whether timestamps displayed on the portal correspond to UTC or Mission Elapsed Time (MET) (relates to Decision D-10).
- **Stage 3 (FITS Inspection Completed):** Reusable non-destructive inspection tools (`src/solar_flare/inspection/`), CLI runner (`scripts/inspect_fits.py`), exploration notebook (`notebooks/01_fits_inspection.ipynb`), and documentation ([`docs/03_inspection_methods.md`](03_inspection_methods.md)) have been established. Real Level-1 SoLEXS files were inspected, verifying 100% hash immutability before and after execution. Decisions D-09 and D-10 were enriched with empirical header observations.
- **Stage 4 (Data Quality Assessment — PROVISIONAL pending G1):** Pure non-destructive quality checks (`src/solar_flare/quality/checks.py`), empirical cadence diagnostics (`src/solar_flare/quality/cadence.py`), GTI coverage quantifier (`src/solar_flare/quality/gti_coverage.py`), column-role evidence extractor (`src/solar_flare/quality/roles.py`), and visualization generator (`src/solar_flare/quality/report.py`) implemented. Decisions D-09, D-10, and D-13 advanced to `PROVISIONAL` pending student confirmation at Gate G1 (column roles, time system, GTI names) and Gate G2 (quality thresholds). All raw FITS files preserved with 100% SHA-256 integrity.
