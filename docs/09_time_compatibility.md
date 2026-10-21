# SOLARIS-A1: Time-System Compatibility Analysis (Stage 6)

## Overview

In `SOLARIS-A1` (*Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations*), associating external solar flare event catalogues with SoLEXS Level-1 light curves requires rigorous temporal compatibility analysis.

A mismatch in epoch, time scale, or leap-second handling would introduce systematic timing offsets of seconds to hours, directly corrupting:
1. **Window-level ground-truth labels for Task A:** Falsely labeling active flare windows as quiet, or quiet windows as active.
2. **Forecast horizons for Task B:** Leaking active flare data into pre-flare forecasting windows.

---

## 1. What Must Be Established Before Event Association

To achieve verified temporal compatibility, five criteria must be confirmed by the student researcher:

### 1.1 Reference Epoch Alignment
- **SoLEXS Header Convention:** FITS header keywords indicate `MJDREFI = 40587` and `MJDREFF = 0`. In astronomical convention, Modified Julian Date 40587.0 corresponds to `1970-01-01 00:00:00 UTC` (the standard POSIX/Unix epoch).
- **Candidate Timestamp:** $t = 1,792,281,600.0\text{ s}$ evaluates to `2026-10-18 00:00:00 UTC`, matching `DATE-OBS`.
- **External Catalog Epoch:** External records (e.g. NOAA GOES or HEK) must be translated into elapsed seconds since the exact same `1970-01-01 00:00:00 UTC` zero-point.

### 1.2 Time Scale Definition (UTC vs TAI vs TT vs Mission Elapsed Time)
- **UTC (Coordinated Universal Time):** Incorporates discrete leap seconds to stay synchronized with Earth's rotation ($UT1$).
- **TAI (International Atomic Time) / TT (Terrestrial Time):** Continuous atomic scales without leap seconds. As of 2026, $\text{TAI} - \text{UTC} = 37\text{ s}$.
- **Spacecraft Mission Elapsed Time (MET):** Continuous clock counter onboard Aditya-L1. If `TIME` in SoLEXS FITS is derived from an uncorrected spacecraft clock rather than ground-reconstructed UTC, a clock drift or offset must be accounted for.
- **Decision D-10:** Remains strictly **PROVISIONAL** pending human confirmation at Gate G1.

### 1.3 Leap-Second Treatment
- High-level event catalogues typically state ISO 8601 strings (e.g. `2026-10-18T10:50:00Z`). Converting ISO 8601 strings to elapsed seconds must use a consistent leap-second convention (standard Unix time ignores leap seconds, assuming 86,400 SI seconds per day).

### 1.4 Timezone and String Formatting
- All text timestamps from external sources must be verified as Universal Time (UTC / UT / GMT). Local station times (e.g. US Mountain Time for SWPC operations) must never be used without explicit UTC conversion.

### 1.5 Light-Travel Time Offsets
- **Aditya-L1 Position:** Aditya-L1 orbits the Sun-Earth Lagrange Point 1 (L1), located approximately $1.5 \times 10^6\text{ km}$ sunward of Earth.
- **Light-Travel Time Difference:** Light from the Sun arrives at Aditya-L1 approximately **$5.0\text{ seconds}$ earlier** than at Earth or geostationary GOES satellites:
  $$\Delta t_{\text{light}} = \frac{1.5 \times 10^6\text{ km}}{3.0 \times 10^5\text{ km/s}} \approx 5.0\text{ s}$$
- **Matching Tolerance (Decision D-02):** The temporal tolerance $\Delta t_{\text{match}}$ must account for this physical propagation differential plus detector integration bins.

---

## 2. Compatibility Assessment Rule

In `solar_flare.labels.compatibility`:
- If the SoLEXS time system (Decision D-10) is marked `PROVISIONAL`, `PENDING`, or `OPEN`, the compatibility status for any external source is strictly:
  $$\text{Status} = \text{"TIME\_SYSTEM\_UNCONFIRMED"}$$
- No time conversion or data alignment may be applied until Gate G1 confirms the SoLEXS time system.
