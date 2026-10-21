# Research Limitations and Scientific Constraints (Stage 14)

**Project:** `SOLARIS-A1`  
**Current Phase:** Stage 14 (Integration Testing, Reproducibility, and Acceptance Preparation)  
**Status:** Software Implementation Complete; Scientific Validation Pending Human Acceptance  

---

## 1. Overview of Limitations

Scientific machine learning requires transparent reporting of instrument physics, observational constraints, data processing boundaries, and epistemological limits. The limitations outlined below govern all findings, code, and artifacts generated within the SOLARIS-A1 repository.

---

## 2. Core Limitations and Constraints

### 2.1 Software Tests Validate Code Behaviour, Not Physical Correctness
The 215 automated tests and static safeguard AST scans in this repository establish that the code functions according to its programmatic specifications (absence of lookahead leakage, strict GTI gap segmentation, schema compliance, deterministic artifact production, and test set cryptographic isolation). **Software correctness does not establish physical correctness.** Passing software tests does not prove that candidate events are true flares, that background flux estimations represent solar quiescent emission, or that machine learning predictions reflect genuine solar physics.

### 2.2 Single Observation Date; Generalisation to Other Periods is Unknown
All real data processed in this repository originates from a single observation day: **2026-10-18**. Solar activity varies across solar cycles, active region evolutions, and rotational phases. The statistical distributions, noise characteristics, and model weights derived from this single date cannot be assumed to generalise to other dates, solar cycle regimes, or orbital geometries without independent multi-epoch evaluation.

### 2.3 SoLEXS Alone Cannot Establish Active Region Attribution
SoLEXS (Solar Low Energy X-ray Spectrometer) is a Sun-as-a-star, full-disk integrating spectrometer. It provides high-cadence temporal and spectral flux measurements but lacks spatial imaging resolution. Consequently, SoLEXS observations alone cannot identify which active region (AR) on the solar disk produced a flare, nor can they differentiate multiple co-temporal flares from distinct active regions.

### 2.4 Dependence on Availability, Quality, and Time Compatibility of Independent Event Records
Supervised flare classification requires independent, externally verified event catalogues (such as GOES/SWPC, RHESSI, or PRADAN official event logs). The validity of ground-truth labels is fundamentally limited by the temporal resolution, onset criteria, and physical definitions of the external catalogue. Any time discrepancy or misclassification in the external catalogue propagates directly into trained models.

### 2.5 Time-System Alignment Uncertainty (PROVISIONAL)
The time system of the Level-1 SoLEXS data is currently treated as **PROVISIONAL pending Gate G1 confirmation**. The light curve `TIME` column represents elapsed seconds since MJD 40587.0 (1970-01-01 00:00:00 UTC) with a 1.0 s nominal step, consistent with `DATE-OBS`. However, definitive confirmation of leap-second corrections and satellite clock synchronization against UTC ground time has not yet been formally signed off by the human researcher.

### 2.6 Column-Role and Channel Selection Uncertainty (PROVISIONAL)
Column roles are **PROVISIONAL pending Gate G1 confirmation**. The primary light-curve flux is currently mapped to the `COUNTS` column of the `RATE` table from detector SDD2. While physical inspection confirms positive count rates with reasonable background noise, official documentation confirming the exact energy passband (e.g. 1–22 keV) and whether `COUNTS` represents deadtime-corrected counts remains provisional.

### 2.7 Extreme Class Imbalance and Event Rarity
Solar flares, particularly moderate and major flares (M- and X-class), are rare astrophysical events. The vast majority of observation intervals correspond to quiet-Sun or non-flaring conditions. High accuracy is trivially achieved by predicting the negative class; evaluation must rely on precision-recall curves, false alarm rates, and detection latency rather than naive classification accuracy.

### 2.8 Overlapping Windows and Effective Sample Size
Sliding analysis windows ($W = 60\text{ s}$, $S = 10\text{ s}$) produce heavily overlapping time intervals. Successive windows share 83.3% of their temporal samples, causing severe autocorrelation. The number of rows in the feature table vastly exceeds the number of statistically independent physical degrees of freedom. Standard random cross-validation yields extreme data leakage; grouping by continuous segment or independent event is strictly required.

### 2.9 Limited Observational Coverage, Orbital Gaps, and SDD1 Invalidation
The Aditya-L1 orbit around the Sun-Earth L1 Lagrange point avoids Earth-eclipse night periods but remains subject to detector telemetry gaps, South Atlantic Anomaly passages, calibrations, and station-keeping maneuvers. In the single observation date present (2026-10-18):
- Detector SDD2 contains 4 continuous GTI segments totaling ~3,600 s.
- **Detector SDD1 GTI file contains zero valid intervals (empty table)**. SDD1 data cannot be substituted or cross-validated for this observation date.

### 2.10 Possible Instrumental Artefacts and Non-Flare Transients
Observed flux increments may originate from non-solar phenomena, including cosmic ray strikes, particle precipitation events, micro-meteoroid impacts, detector electronics resets, or high-voltage fluctuations. Without multi-instrument confirmation (e.g. co-temporal GOES-16/18 XRS or SDO/AIA observations), sudden count rate spikes cannot be unequivocally attributed to solar flares.

---

## 3. Register of PENDING and PROVISIONAL Decisions

Per `config/decisions.yaml`, the following scientific decisions remain provisional or pending human researcher sign-off:

| Decision ID | Decision Title | Status | Responsible Owner | Gate |
| :---: | :--- | :---: | :---: | :---: |
| **D-01** | Source of verified flare-event labels | `PENDING` | Human Researcher | Gate G3 |
| **D-02** | Time-matching tolerance between event records and SoLEXS timestamps | `PENDING` | Human Researcher | Gate G3 |
| **D-03** | Definition of flare onset, peak, and end | `PENDING` | Human Researcher | Gate G3 |
| **D-04** | Treatment of ambiguous or partially observed events | `PENDING` | Human Researcher | Gate G3 |
| **D-05** | Window length ($W = 60\text{ s}$) | `PROVISIONAL` | Human / Antigravity | Gate G5 |
| **D-06** | Window stride ($S = 10\text{ s}$) | `PROVISIONAL` | Human / Antigravity | Gate G5 |
| **D-07** | Forecast horizon for Task B ($\Delta t_{\text{horizon}}$) | `PENDING` | Human Researcher | Gate G6 |
| **D-08** | Definition of verified negative intervals and quiet-Sun safety buffer | `PENDING` | Human Researcher | Gate G3 |
| **D-09** | Energy band / light-curve channel selection (`COUNTS` column) | `PROVISIONAL` | Human Researcher | Gate G1 |
| **D-10** | Time system alignment (UTC vs MET elapsed seconds) | `PROVISIONAL` | Human Researcher | Gate G1 |
| **D-11** | Class-imbalance handling strategy | `PENDING` | Human Researcher | Gate G7 |
| **D-12** | Train / Validation / Test split strategy | `PENDING` | Human Researcher | Gate G7 |
| **D-13** | Quality check and cadence thresholds | `PROVISIONAL` | Human Researcher | Gate G2 |
| **D-14** | Gap splitting and minimum segment duration thresholds | `PENDING` | Human Researcher | Gate G4 |
| **D-15** | Minimum number of independent positive events for main experiment | `PENDING` | Human Researcher | Gate G3 |
| **D-17** | GTI interval boundary inclusion convention | `PENDING` | Human Researcher | Gate G4 |
| **D-18** | Causal baseline lookback window duration ($600\text{ s}$) | `PENDING` | Human Researcher | Gate G5 |
| **D-19** | Rolling trend duration parameter $K$ ($15\text{ s}$) | `PENDING` | Human Researcher | Gate G5 |
| **D-20** | Minimum window sample coverage fraction ($0.80$) | `PENDING` | Human Researcher | Gate G5 |

---

## 4. Unvalidated or Deliberately Guarded Components

1. **Supervised Flare Labels on Real Data:** Unvalidated. Labelling policy `08_labelling_policy.md` remains in `DRAFT` status; no supervised labels were generated for real observation data.
2. **Main Model Training (Task A & Task B):** Not validated on multi-day data. The pilot experiment `PROTO_STAGE10_DRAFT_001` serves purely as an end-to-end software pipeline verification.
3. **Multi-Day Generalisation:** Not validated due to single observation date availability.
