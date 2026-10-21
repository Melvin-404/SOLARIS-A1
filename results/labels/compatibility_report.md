# SOLARIS-A1: Ground-Truth Time Compatibility Report (Stage 6)

> **CRITICAL SCIENTIFIC STATUS:**
> **TIME SYSTEM UNCONFIRMED (Decision D-10 Pending Gate G1 Approval)**.
> In accordance with non-destructive scientific governance, no time conversions are performed.
> All candidate event sources are currently evaluated as **`TIME_SYSTEM_UNCONFIRMED`**.

---

## SoLEXS Observation Window Under Analysis
- **Observation Start:** `1792281600.0` s (Nominal: `2026-10-18 00:00:00 UTC`)
- **Observation End:** `1792367999.0` s (Nominal: `2026-10-18 23:59:59 UTC`)
- **Time System Status:** `PROVISIONAL pending G1 confirmation` (D-10)

---

## Evaluated Sources and Compatibility Status

| Source ID | Source Name | Instrument | Stated Time System | Compatibility Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SRC_NOAA_SWPC` | NOAA SWPC Solar Geophysical Event Reports | Global ground stations and GOES satellites | `Universal Time (UT / UTC)` | **`TIME_SYSTEM_UNCONFIRMED`** | Requires human verification at Gate G3; live daily operational log. |
| `SRC_NOAA_NCEI_GOES` | NOAA NCEI GOES Satellite Data Archive | GOES EXIS / XRS | `UTC (ISO 8601 / elapsed seconds from MJD epoch)` | **`TIME_SYSTEM_UNCONFIRMED`** | Requires human verification at Gate G3; definitive international soft X-ray baseline. |
| `SRC_NASA_HEK` | NASA LMSAL Heliophysics Event Knowledgebase | Multi-instrument (SDO AIA GOES RHESSI) | `UTC (ISO 8601 string format)` | **`TIME_SYSTEM_UNCONFIRMED`** | Requires human verification at Gate G3; aggregates automated and observer reports. |
| `SRC_ISRO_PRADAN` | ISRO ISSDC Aditya-L1 PRADAN Portal | Aditya-L1 SoLEXS | `UTC (TIMESYS=UTC MJDREFI=40587)` | **`TIME_SYSTEM_UNCONFIRMED`** | REJECTED FOR LABELS: Internal to SoLEXS; cannot use SoLEXS data to label SoLEXS models (circular). |

---

## Required Human Actions for Gate G3 Approval
1. Confirm Decision D-10 in `config/decisions.yaml` (Unix epoch seconds from MJD 40587).
2. Approve independent event source (`SRC_NOAA_NCEI_GOES` recommended) in `data/manifests/event_sources.csv`.
3. Approve matching tolerance $\Delta t_{\text{match}}$ (Decision D-02) taking into account L1 Sun-Earth travel time (~5.0 s).
