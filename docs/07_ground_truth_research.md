# SOLARIS-A1: Ground-Truth Solar Flare Source Research (Stage 6)

> **CRITICAL SCIENTIFIC STATUS STATEMENT:**
> **No independent solar flare event source has been confirmed or approved.**
> Sourcing status: **AWAITING HUMAN APPROVAL (Gate G3)**.
> All event sources documented below were researched and accessed by Antigravity during Stage 6.
> No observation data has been downloaded for use in labels. Label generation remains strictly blocked.

---

## 1. Search Strategy and Taxonomy of Sources

To establish an independent, non-circular ground truth for `SOLARIS-A1` solar flare detection (Task A) and pre-flare forecasting (Task B), candidate sources are categorized into three distinct classes:

1. **Category 1 — Primary External Satellite Soft X-ray Monitors (Independent Ground Truth):**
   Continuous full-disk solar soft X-ray irradiance records from geostationary or heliospheric observatories outside the Aditya-L1 payload suite (e.g. NOAA GOES series). These provide standard physical classifications ($A, B, C, M, X$).
2. **Category 2 — Aggregated Solar Event Knowledgebases:**
   Multi-instrument community repositories aggregating automated detection algorithms and human solar observer reports (e.g. NASA Heliophysics Event Knowledgebase).
3. **Category 3 — In-Mission Aditya-L1 SoLEXS Data Products (Evaluated but Rejected for Labels):**
   Internal SoLEXS Level-1/Level-2 light-curve and spectral products hosted on the ISRO PRADAN portal.

---

## 2. Records of Sources Actually Accessed

Every source listed below was directly accessed and investigated during Stage 6.

### Source Record 1: NOAA Space Weather Prediction Center (SWPC) Solar Geophysical Event Reports
- **Source Identifier:** `SRC_NOAA_SWPC`
- **Name as Displayed:** NOAA SWPC Solar Geophysical Event Reports
- **URL Actually Accessed:** `https://services.swpc.noaa.gov/text/solar-geophysical-event-reports.txt`
- **Access Date:** 2026-10-21
- **Version / Release:** Operational daily text event log (compiled by duty forecasters)
- **Instrument:** Global ground-based optical/radio stations and geostationary GOES satellites
- **Energy Band as Stated:** Soft X-ray (GOES 0.1–0.8 nm passband) and optical H-alpha (656.3 nm)
- **Time System as Stated:** Universal Time (UT / UTC)
- **Coverage Start and End:** Daily operational log (current epoch ongoing)
- **Event Definition as Stated:** Begin timestamp, Max flux timestamp, and End timestamp
- **Classification Method as Stated:** Standard GOES peak soft X-ray flux class ($A, B, C, M, X$) and optical flare importance
- **Licence / Terms as Stated:** US Government Public Domain / Open Access
- **Independence from SoLEXS:** **YES.** Fully independent of Aditya-L1 SoLEXS instrument hardware, telemetry, and processing heuristics.
- **Human Verification State:** **NOT VERIFIED BY HUMAN.** Requires review and approval by the student researcher at Gate G3.

---

### Source Record 2: NOAA National Centers for Environmental Information (NCEI) GOES Satellite Data Archive
- **Source Identifier:** `SRC_NOAA_NCEI_GOES`
- **Name as Displayed:** NOAA NCEI GOES Satellite Data Archive
- **URL Actually Accessed:** `https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/`
- **Access Date:** 2026-10-21
- **Version / Release:** Level-2 Science Quality XRS Solar Irradiance and Flare Summaries
- **Instrument:** Geostationary Operational Environmental Satellite (GOES) EXIS / XRS instrument suite
- **Energy Band as Stated:** XRS-A (0.05–0.4 nm) and XRS-B (0.1–0.8 nm)
- **Time System as Stated:** UTC (ISO 8601 strings and elapsed seconds from MJD epoch in netCDF)
- **Coverage Start and End:** 1975 to present (continuous operational coverage across GOES-16, 17, 18, 19)
- **Event Definition as Stated:** Event onset (initial flux rise exceeding background threshold), peak epoch, and end epoch (flux decaying to half-peak or returning to quiet baseline)
- **Classification Method as Stated:** International standard GOES peak flux in $W/\text{m}^2$ ($B \ge 10^{-7}$, $C \ge 10^{-6}$, $M \ge 10^{-5}$, $X \ge 10^{-4}$)
- **Licence / Terms as Stated:** US Government Public Domain / Open Access
- **Independence from SoLEXS:** **YES.** Gold-standard international reference for soft X-ray solar flare classification; zero algorithmic or hardware coupling to Aditya-L1.
- **Human Verification State:** **NOT VERIFIED BY HUMAN.** Requires review and approval by the student researcher at Gate G3.

---

### Source Record 3: NASA LMSAL Heliophysics Event Knowledgebase (HEK)
- **Source Identifier:** `SRC_NASA_HEK`
- **Name as Displayed:** NASA LMSAL Heliophysics Event Knowledgebase
- **URL Actually Accessed:** `https://www.lmsal.com/hek/VOEvent_Spec.html`
- **Access Date:** 2026-10-21
- **Version / Release:** VOEvent 2.0 Feature / Event Specification
- **Instrument:** Multi-instrument aggregation (SDO/AIA, GOES, RHESSI, STEREO)
- **Energy Band as Stated:** Extreme Ultraviolet (EUV) and Soft X-ray
- **Time System as Stated:** UTC (ISO 8601 string format `YYYY-MM-DDTHH:MM:SSZ`)
- **Coverage Start and End:** 2010 to present
- **Event Definition as Stated:** Event type `FL` (Flare) containing `event_starttime`, `event_peaktime`, `event_endtime`
- **Classification Method as Stated:** Automated computer vision feature recognition combined with human observer reports
- **Licence / Terms as Stated:** NASA Open Data Policy
- **Independence from SoLEXS:** **UNKNOWN.** SDO/AIA and GOES automated modules are independent of SoLEXS, but individual automated algorithms vary in threshold heuristics.
- **Human Verification State:** **NOT VERIFIED BY HUMAN.** Requires review and approval by the student researcher at Gate G3.

---

## 3. Searched and Rejected Sources

### Rejected Source 1: ISRO ISSDC Aditya-L1 PRADAN Portal
- **Source Identifier:** `SRC_ISRO_PRADAN`
- **Name as Displayed:** ISRO ISSDC Aditya-L1 PRADAN Portal
- **URL Actually Accessed:** `https://pradan.issdc.gov.in/al1`
- **Access Date:** 2026-10-21
- **Rejection Reason (CIRCULARITY SAFEGUARD):**
  The PRADAN portal is the repository for the primary input data of `SOLARIS-A1` (SoLEXS Level-1 and Level-2 light curves and spectra). Deriving machine learning ground-truth labels from SoLEXS internal burst thresholds or unverified automated detection heuristics to evaluate models that detect SoLEXS flares constitutes **circular reasoning**. An independent external reference (such as NOAA GOES) is mandatory for scientific validity.
- **Status:** **REJECTED AS LABEL SOURCE.** Permitted only as input observation data.

---

## 4. Unverified Sources Statement

The following potential sources were noted in solar physics literature but were **NOT VERIFIED** during Stage 6 because direct documentation URLs were not retrieved:
- *Solar Orbiter STIX Flare Catalog:* NOT VERIFIED.
- *Fermi Gamma-ray Burst Monitor (GBM) Solar Flare Catalog:* NOT VERIFIED.
- *RHESSI Flare List:* NOT VERIFIED.

---

## 5. Summary and Recommendation for Student Researcher (Gate G3)

Antigravity recommends adopting **Source Record 2 (`SRC_NOAA_NCEI_GOES`)** as the primary independent ground-truth event source, with **Source Record 1 (`SRC_NOAA_SWPC`)** as an auxiliary verification reference. The human student researcher holds sole authority to approve or reject this recommendation at Gate G3.
