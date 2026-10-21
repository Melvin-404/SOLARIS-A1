# SOLARIS-A1: Ground-Truth Event Record Schema (Template)

> **STATUS: TEMPLATE ONLY (Stage 5 / Stage 6)**
> No event records are created in Stage 5. This schema defines the expected columns, formats, and time standards for independent solar flare ground-truth catalogues to be evaluated during Stage 6.

---

## 1. Schema Definition for Event Catalogues

When independent event catalogues (e.g. NOAA/GOES X-ray flare catalogue, ISRO/PRADAN official event lists) are acquired in Stage 6, they must be formatted into this normalized CSV schema:

| Column Name | Data Type | Requirement | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `event_id` | String | Mandatory | Unique identifier for the flare event record | `NOAA_20261018_001` |
| `event_start` | Float64 | Mandatory | Flare start / onset epoch in elapsed seconds since `1970-01-01 00:00:00 UTC` | `1792286400.0` |
| `event_peak` | Float64 | Optional | Flare maximum flux epoch in elapsed seconds since `1970-01-01 00:00:00 UTC` | `1792287000.0` |
| `event_end` | Float64 | Mandatory | Flare end epoch in elapsed seconds since `1970-01-01 00:00:00 UTC` | `1792287900.0` |
| `flare_class` | String | Mandatory | Standard GOES soft X-ray classification (A, B, C, M, X with magnitude) | `M1.2` |
| `source_catalogue` | String | Mandatory | Originating archive / observatory | `NOAA_SWPC` / `ISRO_PRADAN` |
| `active_region` | String | Optional | NOAA Active Region number (if assigned) | `AR13850` |
| `verification_status` | String | Mandatory | Verification state: `CONFIRMED_OBSERVATIONAL`, `PROVISIONAL` | `CONFIRMED_OBSERVATIONAL` |
| `notes` | String | Optional | Qualitative notes regarding data quality or cross-instrument flags | `Impulsive phase clear` |

---

## 2. Temporal Reference Standard

In alignment with **Decision D-10 (Time System Alignment)**:
- All timestamps in the event catalogue must be synchronized to the exact same reference frame as SoLEXS Level-1 light-curve data:
  $$\text{Timestamp} = \text{Seconds since } 1970-01-01\text{ 00:00:00 UTC (MJD 40587.0)}$$
- If external records provide ISO 8601 UTC strings (e.g., `2026-10-18T01:20:00Z`), they must be converted using standard UTC POSIX/Unix seconds with leap-second awareness recorded.

---

## 3. Human Approval Gate (Gate G3)

No event catalogue may be ingested into the ML labeling pipeline until:
1. The student researcher reviews candidate catalogues in Stage 6.
2. The student researcher confirms the catalogue source, coverage, and classification accuracy.
3. Gate G3 approval is formally logged in `config/decisions.yaml` (Decision D-01) and `docs/01_decision_log.md`.
