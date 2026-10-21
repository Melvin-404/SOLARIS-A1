# SOLARIS-A1: Column-Role Evidence Report (Stage 4)

> **CRITICAL NOTICE (Gate G1):** All candidate column roles, time systems, GTI columns, and channel definitions listed below are strictly **PROVISIONAL** or **UNRESOLVED**. No role is CONFIRMED. Every entry requires human researcher confirmation at Gate G1.

---

## Summary of Candidate Roles Across Products

| File Name | Product Type | Candidate Time | Candidate Count/Rate | Quality Flag | GTI Interval Cols | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` | GTI | - | - | None detected | START, STOP | PROVISIONAL (requires G1) |
| `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` | GTI | - | - | None detected | START, STOP | PROVISIONAL (requires G1) |
| `AL1_SOLEXS_20261018_SDD2_L1.lc.gz` | LIGHTCURVE | TIME | COUNTS | None | - | PROVISIONAL (requires G1) |
| `AL1_SOLEXS_20261018_SDD2_L1.pi.gz` | PI_SPECTRUM | TSTART (spectrum) | COUNTS (340D array) | None detected | N/A | UNRESOLVED |

---

## Detailed Evidence by Product

### File: `AL1_SOLEXS_20261018_SDD1_L1.gti.gz`
- **Product Type:** `GTI`
- **Observed Header Keywords:**
  - `TELESCOP`: `AL1`
  - `INSTRUME`: `SoLEXS`
  - `OBS_ID`: `N00_0000_001056`
  - `TSTART`: ``
  - `TSTOP`: ``
- **Role Evidence:**
  - **Role `gti_start`:**
    - `candidate_column`: `START`
    - `status`: `UNRESOLVED`
    - `note`: `GTI table has ZERO rows for this observation; requires human confirmation (G1)`
    - `n_intervals`: `0`
  - **Role `gti_stop`:**
    - `candidate_column`: `STOP`
    - `status`: `UNRESOLVED`
    - `note`: `GTI table has ZERO rows for this observation; requires human confirmation (G1)`
    - `n_intervals`: `0`

### File: `AL1_SOLEXS_20261018_SDD2_L1.gti.gz`
- **Product Type:** `GTI`
- **Observed Header Keywords:**
  - `TELESCOP`: `AL1`
  - `INSTRUME`: `SoLEXS`
  - `OBS_ID`: `N00_0000_001056`
  - `TSTART`: `2026-10-18T01:20:28+00:00`
  - `TSTOP`: `2026-10-18T23:59:59+00:00`
- **Role Evidence:**
  - **Role `gti_start`:**
    - `candidate_column`: `START`
    - `status`: `PROVISIONAL`
    - `note`: `requires human confirmation (G1)`
    - `format`: `D`
    - `unit_as_stored`: `None recorded`
    - `n_intervals`: `8`
    - `data_range`: `[1792286428.0, 1792341831.0]`
    - `monotonic`: `True`
  - **Role `gti_stop`:**
    - `candidate_column`: `STOP`
    - `status`: `PROVISIONAL`
    - `note`: `requires human confirmation (G1)`
    - `format`: `D`
    - `unit_as_stored`: `None recorded`
    - `n_intervals`: `8`
    - `data_range`: `[1792316629.0, 1792367999.0]`
    - `monotonic`: `True`

### File: `AL1_SOLEXS_20261018_SDD2_L1.lc.gz`
- **Product Type:** `LIGHTCURVE`
- **Observed Header Keywords:**
  - `TELESCOP`: `AL1`
  - `INSTRUME`: `SoLEXS`
  - `OBS_ID`: `N00_0000_001056`
  - `FILTER`: `SDD2`
  - `NUMBAND`: `4`
  - `TIMESYS`: `UTC`
  - `MJDREFI`: `40587`
  - `MJDREFF`: `0`
  - `TIMZERO`: `0`
  - `TIMEDEL`: `1`
  - `TIMEUNIT`: `s`
  - `TIMEREF`: `LOCAL`
  - `TSTART`: `1792281600.0`
  - `TSTOP`: `1792367999.0`
  - `DATE-OBS`: `2026-10-18 00:00:00`
  - `DATE-END`: `2026-10-18 23:59:59`
- **Role Evidence:**
  - **Role `time`:**
    - `candidate_column`: `TIME`
    - `status`: `PROVISIONAL`
    - `note`: `requires human confirmation (G1)`
    - `format`: `D`
    - `unit_as_stored`: `None recorded`
    - `n_rows`: `86400`
    - `data_range`: `[1792281600.0, 1792367999.0]`
    - `monotonic`: `True`
    - `median_step`: `1.0`
    - `header_evidence`: `{'TIMESYS': 'UTC', 'MJDREFI': '40587', 'TIMEDEL': '1', 'DATE-OBS': '2026-10-18 00:00:00'}`
  - **Role `count_or_rate`:**
    - `candidate_column`: `COUNTS`
    - `status`: `PROVISIONAL`
    - `note`: `requires human confirmation (G1)`
    - `format`: `D`
    - `unit_as_stored`: `None recorded`
    - `n_rows`: `86400`
    - `n_nan`: `4849`
    - `n_pos_inf`: `0`
    - `n_neg_inf`: `0`
    - `n_zeros`: `137`
    - `data_range`: `[0.0, 185.0]`
    - `mean`: `13.349817905359837`
    - `median`: `9.0`
    - `header_evidence`: `{'NUMBAND': '4', 'FILTER': 'SDD2'}`
  - **Role `quality_flag`:**
    - `candidate_column`: `None`
    - `status`: `UNRESOLVED`
    - `note`: `No dedicated quality flag column found in RATE table; requires human confirmation (G1)`
  - **Role `energy_or_channel`:**
    - `candidate_indicator`: `Header keywords (NUMBAND, FILTER)`
    - `status`: `PROVISIONAL`
    - `note`: `requires human confirmation (G1)`
    - `NUMBAND`: `4`
    - `FILTER`: `SDD2`

### File: `AL1_SOLEXS_20261018_SDD2_L1.pi.gz`
- **Product Type:** `PI_SPECTRUM`
- **Observed Header Keywords:**
  - `TELESCOP`: `AL1`
  - `INSTRUME`: `SoLEXS`
  - `OBS_ID`: `N00_0000_001056`
  - `FILTER`: `SDD2`
- **Role Evidence:**
  - **Role `spectral_channels`:**
    - `candidate_columns`: `['SPEC_NUM', 'CHANNEL', 'COUNTS']`
    - `status`: `UNRESOLVED`
    - `note`: `PI spectrum product — inspected read-only, not used in light-curve quality checks; requires human confirmation (G1)`
    - `n_rows`: `86400`

---

## Gate G1 Action Checklist for Student Researcher

Before transitioning any role to CONFIRMED, the human student must verify:
1. [ ] Confirm that `TIME` in `RATE` represents elapsed seconds from `1970-01-01 00:00:00 UTC` (MJD 40587).
2. [ ] Confirm that `COUNTS` in `RATE` represents integrated detector counts (or count rate in c/s).
3. [ ] Confirm that no hardware quality-flag bitmask exists in `.lc.gz`, or define where external flag indicators are sourced.
4. [ ] Confirm that `START` and `STOP` in `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` correspond to valid observation intervals on the same time scale.
5. [ ] Confirm why `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` contains zero rows (SDD1 inactive or off during this epoch).
6. [ ] Confirm that `AL1_SOLEXS_20261018_SDD2_L1.pi.gz` is a multi-channel spectral file to be handled in later stages.
