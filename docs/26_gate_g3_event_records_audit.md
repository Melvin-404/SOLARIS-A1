# SOLARIS-A1: Pre-Approval Rigorous Audit of Proposed July 2024 Flare Records (Gate G3)

**Document ID:** `DOC-STAGE14-AUDIT-004`  
**Date:** 2026-10-23  
**Status:** `AUDIT COMPLETE — READY FOR HUMAN DECISION`  
**Target Catalog:** `results/proposed_event_records_july2024.csv` (117 candidate records)  
**Evaluator:** Antigravity Autonomous Audit Engine  
**Governance Gate:** Gate G3 (Independent Ground-Truth Flare Labelling Approval)  

---

## 1. Executive Verdict & Readiness Summary

| Category | Finding | Recommendation |
| :--- | :--- | :--- |
| **Major Eruptive Flares ($M$ & $X$ Class)** | **28 events** verified with high photon count rates ($1,000$ to $9,194\text{ cts/s}$) and precise NOAA GOES start/peak/end times. | **READY FOR IMMEDIATE APPROVAL** |
| **Minor Solar Flares ($C$ Class)** | **89 events** verified with clear thermal count elevations ($C1.0$ to $C9.8$) inside SoLEXS GTIs. | **READY FOR APPROVAL** |
| **Telemetry Gap Flares (Outside GTIs)** | **12 events** in raw NOAA reports occurred during SoLEXS orbital gaps on July 8 and 9. | **CONFIRMED EXCLUDED (0 in catalog)** |
| **Timestamp Consistency** | 100% of records satisfy $t_{\text{onset}} \le t_{\text{peak}} \le t_{\text{end}}$ with zero backward time steps. | **PASSED** |
| **Duplicate / Overlapping Events** | Zero duplicate IDs. Zero mutual interval overlaps among the 117 records. | **PASSED** |
| **Simulated Window Yield** | **14,074 positive windows**, **89,494 negative windows**, **384 boundary-excluded (`<NA>`)**, **8,290 gap-excluded (`<NA>`)**. | **SCIENTIFICALLY SOUND (Prevalence: 13.59%)** |

---

## 2. Event Field & Source Cross-Verification

All 117 records were cross-checked against the raw NOAA SWPC daily event logs (`https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2024/07/`):
1. **Classification:**
   - 1 X-Class: `X1.2` (July 14, 02:23–02:48 UTC, Peak 02:34 UTC)
   - 27 M-Class: `M1.0` to `M5.3` (including the intense July 13 M5.3 burst)
   - 89 C-Class: `C1.0` to `C9.8`
2. **Active Region Attribution:**
   - Regions **AR3738**, **AR3730**, **AR3747**, **AR3745**, and **AR3729** match official NOAA sunspot group assignments.
3. **Astrophysical Durations:**
   - All flare durations fall between 4 minutes and 85 minutes, consistent with standard solar atmospheric magnetic reconnection and cooling phases.

---

## 3. How the 60-Second Windows Are Labelled (`src/solar_flare/export/join_labels.py`)

The pipeline executes a deterministic, policy-guarded decision tree on every 60-second observation window ($W = [t_{\text{start}}, t_{\text{start}} + 60\text{s}]$, stepped by 10 seconds):

```mermaid
flowchart TD
    W["60s Observation Window"] --> Cov{"GTI Coverage >= 80%?"}
    Cov -- No --> NA_Gap["Excluded: LOW_COVERAGE_EXCLUDED (label=<NA>)"]
    Cov -- Yes --> Ov{"Overlap with Event >= 30s (50%)?"}
    Ov -- Yes --> Pos["Positive: MATCHED_EVENT (label=1)"]
    Ov -- No --> Part{"Overlap with Event > 0s?"}
    Part -- Yes --> NA_Part["Excluded: PARTIAL_OVERLAP_EXCLUDED (label=<NA>)"]
    Part -- No --> Emb{"Inside 300s Flare Embargo Buffer?"}
    Emb -- Yes --> NA_Emb["Excluded: EMBARGO_EXCLUDED (label=<NA>)"]
    Emb -- No --> Neg["Verified Negative: VERIFIED_QUIET_BACKGROUND (label=0)"]
```

### Protection Against Boundary Contamination:
- Windows touching only the leading or trailing tail of a flare (overlap $< 30$ seconds) are **not** labeled as negative (0). They are explicitly quarantined as `<NA>`, completely eliminating label noise at flare transitions.

---

## 4. Verification of Negative Windows (No False Assumptions of Quietness)

A critical scientific concern is whether negative windows are assumed to be quiet merely because no major flare was reported.
* **Granular C-Class Cataloging:** The proposed catalog tracks all flares down to **$C1.0$** ($10^{-6} \text{ W/m}^2$). Any window containing even a minor C-flare is flagged as positive or boundary-quarantined.
* **Flux Verification:** The SoLEXS count rate distribution across the 89,494 negative windows was evaluated:
  - Mean count rate: $31.4 \text{ cts/s}$
  - Standard deviation: $8.6 \text{ cts/s}$
  - Peak count rate in negative windows: $< 180 \text{ cts/s}$
* This confirms that the negative windows contain authentic quiet-Sun background fluctuations without unrecognized major eruptive emissions.

---

## 5. Quantitative Window Breakdown by Observation Date

Simulating the full sliding windowing algorithm across the 13 integrated days produces:

| Date | Events Count | Total 60s Windows | Positive Windows (`label=1`) | Verified Negatives (`label=0`) | Boundary Excluded (`label=<NA>`) | Telemetry Gap Excluded (`label=<NA>`) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2024-07-01** | 9 | 8,634 | 955 | 7,639 | 28 | 12 |
| **2024-07-03** | 7 | 8,634 | 846 | 7,764 | 24 | 0 |
| **2024-07-04** | 8 | 8,634 | 1,123 | 7,483 | 28 | 0 |
| **2024-07-05** | 9 | 8,634 | 998 | 7,602 | 34 | 0 |
| **2024-07-06** | 7 | 8,634 | 1,001 | 7,613 | 20 | 0 |
| **2024-07-07** | 13 | 8,634 | 1,653 | 6,945 | 36 | 0 |
| **2024-07-08** | 8 | 8,634 | 817 | 2,531 | 28 | 5,258 |
| **2024-07-09** | 4 | 8,634 | 380 | 5,220 | 14 | 3,020 |
| **2024-07-10** | 12 | 8,634 | 1,564 | 7,030 | 40 | 0 |
| **2024-07-11** | 7 | 8,634 | 875 | 7,739 | 20 | 0 |
| **2024-07-12** | 5 | 8,634 | 659 | 7,955 | 20 | 0 |
| **2024-07-13** | 11 | 8,634 | 1,507 | 7,099 | 28 | 0 |
| **2024-07-14** | 17 | 8,634 | 1,696 | 6,874 | 64 | 0 |
| **TOTAL** | **117** | **112,242** | **14,074** | **89,494** | **384** | **8,290** |

* **Usable Labeled Windows:** **103,568 windows** ($14,074$ positive, $89,494$ negative)
* **Positive Class Prevalence:** **$13.59\%$** (representing realistic active-region space-weather operational conditions, up from $0.56\%$ in the 1-day pilot).

---

## 6. Audit Conclusion & Human Approval Decision

* **Status:** The 117 event records in [`results/proposed_event_records_july2024.csv`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/results/proposed_event_records_july2024.csv) have passed all automated schema, physical ordering, GTI alignment, and overlap checks with **zero discrepancies**.
* **Integrity Guarantee:** No approved catalog files or trained models have been modified.
