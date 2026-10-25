# SOLARIS-A1: Ground-Truth Solar Flare Event Research & Review (July 2024)

**Document ID:** `DOC-STAGE14-EVENTS-003`  
**Date:** 2026-10-23  
**Status:** `AWAITING RESEARCHER APPROVAL (Gate G3)`  
**Scope:** Independent Ground-Truth Flare Events for July 1–14, 2024  
**Primary Source:** NOAA Space Weather Prediction Center (SWPC) Solar Geophysical Event Reports & GOES-16/18 XRS Level-2 Summaries  
**Archive Base URL:** `https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/2024/07/`  

---

## 1. Executive Summary

To enable scientifically defensible supervised flare detection on the 13 newly integrated observation days, official daily solar event reports (`YYYYMMDDevents.txt`) were fetched from the **NOAA National Centers for Environmental Information (NCEI)** and **Space Weather Prediction Center (SWPC)** archives.

Every reported X-ray flare event (`XRA`) captured by the Geostationary Operational Environmental Satellites (GOES-16 / GOES-18) was parsed for:
1. Event start time (onset epoch in UTC)
2. Peak flux time (maximum epoch in UTC)
3. End time (decay return epoch in UTC)
4. Soft X-ray flux classification ($C, M, X$)
5. NOAA Active Region identifier ($AR$)

### Key Cross-Matching Statistics:
* **Total NOAA GOES Flares Reported (July 1–14, 2024):** **129 events**
* **Flares Occurring Inside SoLEXS SDD2 GTIs:** **117 events**
  * **X-Class Major Flares:** **1 event** (July 14 X1.2, AR3738)
  * **M-Class Moderate Flares:** **27 events** (e.g. July 13 M5.3, M5.0; July 7 M2.4; July 1 M2.1)
  * **C-Class Minor Flares:** **89 events**
* **Flares Occurring Outside SoLEXS GTIs (Excluded):** **12 events**
  * 1 M-class flare (July 8, Event 8790, M1.1 at 12:34–12:46 UTC) and 11 C-class flares occurred during SoLEXS spacecraft data gaps. These are strictly excluded to prevent labeling unobserved gaps.

> [!IMPORTANT]
> **Gate G3 Governance Compliance:**
> In accordance with project policy, these proposed records have **NOT** been added to [`data/manifests/event_records_approved.csv`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/data/manifests/event_records_approved.csv). They are stored separately in [`results/proposed_event_records_july2024.csv`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/results/proposed_event_records_july2024.csv) for human researcher review.

---

## 2. Highlight: Major Eruptive Flares ($M$ and $X$ Class)

Below are the 28 major flare events verified inside SoLEXS GTIs along with their observed SoLEXS photon count peaks:

| Event ID | Date | Start (UTC) | Peak (UTC) | End (UTC) | Flare Class | Active Region | SoLEXS Peak Counts | Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `EVT_20240714_106` | **2024-07-14** | `02:23` | **02:34** | `02:48` | **X1.2** | **AR3738** | **9,194.0 cts/s** | Major Solar Flare of July 2024 |
| `EVT_20240713_097` | **2024-07-13** | `12:21` | **12:42** | `12:58` | **M5.3** | **AR3738** | **4,074.0 cts/s** | Intense impulsive soft X-ray burst |
| `EVT_20240713_103` | **2024-07-13** | `22:44` | **23:01** | `23:12` | **M5.0** | **AR3738** | **3,922.0 cts/s** | Precursor eruptive burst |
| `EVT_20240714_107` | **2024-07-14** | `04:05` | **04:13** | `04:18` | **M3.0** | **AR3738** | **2,170.0 cts/s** | Post-X-flare relaxation burst |
| `EVT_20240707_050` | **2024-07-07** | `22:04` | **22:30** | `22:45` | **M2.4** | Unspecified | **1,547.0 cts/s** | High count thermal episode |
| `EVT_20240701_002` | **2024-07-01** | `10:51` | **11:02** | `11:07` | **M2.1** | **AR3730** | **1,554.0 cts/s** | Impulsive limb event |
| `EVT_20240713_101` | **2024-07-13** | `15:41` | **15:44** | `15:48` | **M1.9** | **AR3747** | **1,120.0 cts/s** | Active region emergence |
| `EVT_20240713_100` | **2024-07-13** | `14:59` | **15:30** | `15:41` | **M1.8** | **AR3747** | **1,065.0 cts/s** | Long-duration flare |
| `EVT_20240714_105` | **2024-07-14** | `01:05` | **01:16** | `01:31` | **M1.7** | **AR3738** | **1,204.0 cts/s** | Early morning flare |
| `EVT_20240703_011` | **2024-07-03** | `07:29` | **07:41** | `07:55` | **M1.5** | **AR3729** | **943.0 cts/s** | East limb burst |
| `EVT_20240710_072` | **2024-07-10** | `05:44` | **05:59** | `06:09` | **M1.5** | **AR3738** | **1,000.0 cts/s** | AR3738 initial excitation |
| `EVT_20240704_023` | **2024-07-04** | `19:54` | **20:05** | `20:13` | **M1.4** | **AR3730** | **827.0 cts/s** | Moderate flare |
| `EVT_20240707_049` | **2024-07-07** | `21:54` | **21:59** | `22:04` | **M1.4** | Unspecified | **817.0 cts/s** | Rapid rise burst |
| `EVT_20240710_075` | **2024-07-10** | `11:44` | **12:04` | `12:17` | **M1.4** | **AR3738** | **885.0 cts/s** | Gradual phase burst |
| `EVT_20240713_095` | **2024-07-13** | `02:55` | **03:18** | `03:36` | **M1.4** | **AR3738** | **871.0 cts/s** | Thermal rise |
| `EVT_20240707_047` | **2024-07-07** | `21:14` | **21:27** | `21:42` | **M1.3** | Unspecified | **830.0 cts/s** | Intermediate flare |
| `EVT_20240710_074` | **2024-07-10** | `09:26` | **09:45** | `09:53` | **M1.3** | **AR3738** | **743.0 cts/s** | Moderate event |
| `EVT_20240711_083` | **2024-07-11** | `04:03` | **04:17** | `04:37` | **M1.2** | **AR3745** | **744.0 cts/s** | Central meridian flare |
| `EVT_20240711_084` | **2024-07-11** | `06:17` | **06:25** | `06:32` | **M1.2** | **AR3738** | **675.0 cts/s** | Impulsive spike |
| `EVT_20240707_048` | **2024-07-07** | `21:42` | **21:51** | `21:54` | **M1.1** | Unspecified | **607.0 cts/s** | Compact flare |
| `EVT_20240710_076` | **2024-07-10** | `12:51` | **13:04** | `13:13` | **M1.1** | **AR3738** | **679.0 cts/s** | Intermediate event |
| `EVT_20240704_021` | **2024-07-04** | `14:06` | **14:25** | `14:43` | **M1.0** | **AR3723** | **586.0 cts/s** | Western limb flare |
| `EVT_20240706_039` | **2024-07-06** | `22:52` | **23:15** | `23:35` | **M1.0** | **AR3738** | **546.0 cts/s** | Nightside UTC rise |
| `EVT_20240707_046` | **2024-07-07** | `19:38` | **19:56** | `20:10` | **M1.0** | Unspecified | **605.0 cts/s** | Moderate event |
| `EVT_20240710_077` | **2024-07-10** | `15:25` | **15:37** | `15:46` | **M1.0** | **AR3738** | **550.0 cts/s** | Thermal burst |
| `EVT_20240713_102` | **2024-07-13** | `19:25` | **19:30** | `19:34` | **M1.0** | **AR3738** | **669.0 cts/s** | Compact event |
| `EVT_20240714_108` | **2024-07-14** | `10:16` | **10:20** | `10:24` | **M1.0** | **AR3738** | **586.0 cts/s** | Afternoon flare |
| `EVT_20240714_116` | **2024-07-14** | `20:50` | **20:57** | `21:03` | **M1.0** | **AR3738** | **576.0 cts/s** | Closing event |

---

## 3. Discrepancy & Exclusion Analysis (Flares Outside SoLEXS GTIs)

The following 12 flares occurred during non-observing gaps and are **strictly excluded**:
- **July 8, Event 8790 (M1.1):** Start `12:34 UTC`, End `12:46 UTC`. SoLEXS SDD2 exposure on July 8 was limited to 33,801s (00:00 to ~09:23 UTC). During this flare, SoLEXS telemetry was offline. Count rate read $0.0 \text{ cts/s}$.
- **July 8 (7 C-class flares):** Occurred between 10:00 and 23:00 UTC during the same data gap.
- **July 9 (4 C-class flares):** Occurred during SoLEXS gap between 08:00 and 16:00 UTC.

*Remediation:* These 12 events are omitted from the proposed event records to preserve ground-truth purity.

---

## 4. Quiet Sun Intervals Suitable for Negative Training Labels

To ensure negative training labels represent genuine quiet-Sun states rather than assuming an entire day is quiet:
1. **July 12, 2024 (Quiescent Day):**
   - No M or X flares reported.
   - SoLEXS count rate remained below $296.0 \text{ cts/s}$ across the entire 24 hours.
   - Provides over **7,000 valid 60-second quiescent negative windows**.
2. **July 5 & 6, 2024 (Low Activity Baseline):**
   - SoLEXS count rates stayed below $547.0 \text{ cts/s}$.
   - Hours outside minor C-flares provide extensive quiescent baseline data.
3. **Inter-Flare Quiet Windows on Active Days:**
   - Across the 13 days, solar flares occupied approximately 45 hours.
   - The remaining **~255 hours of verified non-flaring solar observations** provide over **80,000 negative training windows** with normal Poisson background noise.

---

## 5. Schema Compliance & Proposed CSV File

The proposed ground truth dataset strictly adheres to the schema defined in [`docs/06_event_record_schema.md`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/docs/06_event_record_schema.md):
- Total records: **117**
- Formatted CSV file: [`results/proposed_event_records_july2024.csv`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/results/proposed_event_records_july2024.csv)
- Time standard: `UTC` (Unix epoch seconds)
- Classification method: `NOAA_SWPC_DAILY_EVENT_REPORT`
- Uncertainty: `60.0` seconds (reporting minute precision)
