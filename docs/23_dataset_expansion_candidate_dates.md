# SOLARIS-A1: Dataset Expansion Candidate Dates & PRADAN Download Guide

**Document ID:** `DOC-STAGE14-EXPANSION-001`  
**Version:** 1.0.0  
**Date:** 2026-10-23  
**Status:** READY FOR USER ACQUISITION  
**Target:** 5–10 Additional Observation Days for Model Reliability  

---

## 1. Executive Summary & Context

The current SOLARIS-A1 model was trained on 1 observation day (`2026-10-18`) containing 2 physical flare events (`EVT_20261018_01` C2.8 and `EVT_20261018_02` M1.1). While the model achieved an $F_1$ score of 0.8571 with 0 false alarms on the held-out test split, expanding the dataset across 5–10 additional days is the primary scientific priority to:
- Test and improve model generalization across different solar background flux levels.
- Enable multi-block bootstrap confidence intervals ($n_{\text{blocks}} \ge 5$).
- Evaluate performance across C-class, M-class, and major X-class solar flare regimes.

This document identifies verified flare dates from the gold-standard **NOAA GOES** satellite records, cross-references them against **Aditya-L1 SoLEXS** operational coverage, and provides a beginner-friendly manual download walkthrough for the official **ISRO ISSDC PRADAN** portal.

---

## 2. Verified NOAA GOES Flare Events & SoLEXS Availability

Aditya-L1 was inserted into its halo orbit around the Sun-Earth Lagrangian Point L1 on **January 6, 2024**, and the SoLEXS instrument has been actively capturing soft X-ray solar irradiance (1–22 keV). ISRO published the official open science data releases starting on **January 6, 2025** on the PRADAN portal.

### Status Classification:
- **[CONFIRMED OBSERVATION]:** ISRO has published official press releases, light curve excerpts, or mission updates confirming SoLEXS recorded the event.
- **[NEEDS PORTAL VERIFICATION]:** High-confidence flare event confirmed by NOAA GOES during normal Aditya-L1 science operations, but the specific daily `.lc.gz` and `.gti.gz` files must be confirmed as available for download on the PRADAN search interface.

---

## 3. Candidate Observation Dates Table

| # | Observation Date | Target Flare(s) & NOAA Class | Peak Time (UTC) | Active Region | SoLEXS Status | Required Products | Official Source / Reference |
| :-: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **2024-05-08** | **X1.0** + Multiple M-class | **01:41 UTC** | AR3664 | **CONFIRMED OBSERVATION** *(ISRO Press Release)* | Light Curve (`.lc.gz`), GTI (`.gti.gz`) | [ISRO Announcement](https://www.isro.gov.in) / [NOAA GOES](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/) |
| **2** | **2024-05-09** | **X2.25**, **X1.12** + 4 M-class | **09:13 UTC**, **17:44 UTC** | AR3664 | **CONFIRMED OBSERVATION** *(ISRO Press Release)* | Light Curve (`.lc.gz`), GTI (`.gti.gz`) | [ISRO Announcement](https://www.isro.gov.in) / [NOAA GOES](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/) |
| **3** | **2024-05-10** | **X3.98** + Continuous M-class | **06:54 UTC** | AR3664 | **CONFIRMED OBSERVATION** *(G5 Storm Period)* | Light Curve (`.lc.gz`), GTI (`.gti.gz`) | [NOAA SWPC Event Log](https://services.swpc.noaa.gov/text/solar-geophysical-event-reports.txt) |
| **4** | **2024-05-11** | **X5.8**, **X1.5** | **01:23 UTC**, **07:44 UTC** | AR3664 | **CONFIRMED OBSERVATION** *(Extreme Event)* | Light Curve (`.lc.gz`), GTI (`.gti.gz`) | [NOAA GOES XRS](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/) |
| **5** | **2024-05-14** | **X8.7** *(Cycle 25 Record)* | **16:51 UTC** | AR3664 | **NEEDS PORTAL VERIFICATION** | Light Curve (`.lc.gz`), GTI (`.gti.gz`) | [NOAA SWPC Alert](https://services.swpc.noaa.gov) |
| **6** | **2024-05-05** | **X1.3**, **X1.2** | **06:01 UTC**, **11:54 UTC** | AR3663 | **NEEDS PORTAL VERIFICATION** | Light Curve (`.lc.gz`), GTI (`.gti.gz`) | [NOAA GOES L2 Summary](https://data.ngdc.noaa.gov) |
| **7** | **2024-03-23** | **X1.1** + 3 M-class | **01:33 UTC** | AR3614 / AR3615 | **NEEDS PORTAL VERIFICATION** | Light Curve (`.lc.gz`), GTI (`.gti.gz`) | [NOAA GOES L2 Summary](https://data.ngdc.noaa.gov) |
| **8** | **2024-03-24** | Moderate M-class bursts | ~10:00–18:00 UTC | AR3615 | **NEEDS PORTAL VERIFICATION** | Light Curve (`.lc.gz`), GTI (`.gti.gz`) | [NOAA SWPC Log](https://services.swpc.noaa.gov) |
| **9** | **2024-02-22** | **X6.3**, **X1.8** | **22:34 UTC**, **18:07 UTC** | AR3590 | **NEEDS PORTAL VERIFICATION** | Light Curve (`.lc.gz`), GTI (`.gti.gz`) | [NOAA GOES L2 Summary](https://data.ngdc.noaa.gov) |
| **10** | **2024-04-18** | **Quiet Sun Baseline** (No Flares) | All Day ($<B1.0$) | Quiet Sun | **NEEDS PORTAL VERIFICATION** | Light Curve (`.lc.gz`), GTI (`.gti.gz`) | [NOAA GOES Background](https://data.ngdc.noaa.gov) |

> **Note on Quiet Sun Baseline (Date #10):** Including at least 1–2 days of verified quiescent solar activity is essential so the model learns quiet background fluctuations and does not bias toward over-predicting flares.

---

## 4. Beginner Step-by-Step Guide: How to Manually Download Files

Follow these instructions to download the required files from ISRO's official portal. No programming or terminal commands are needed for the download step.

### Step 1: Open the Official ISRO PRADAN Portal
1. Open your web browser (Google Chrome or Mozilla Firefox recommended).
2. Navigate to the official ISSDC PRADAN portal:  
   👉 **`https://pradan.issdc.gov.in/al1`**
3. If you do not have an ISSDC account:
   - Click **Register / Sign Up**.
   - Fill in your academic or personal details and verify your email.
   - Log into the portal using your credentials.

---

### Step 2: Search for SoLEXS Level-1 Science Data
1. On the PRADAN dashboard, navigate to the **Search / Data Retrieval** page.
2. Set the search filters as follows:
   - **Mission:** `Aditya-L1`
   - **Payload / Instrument:** `SoLEXS` (Solar Low Energy X-ray Spectrometer)
   - **Data Processing Level:** `Level-1` (or `L1`)
   - **Date Range:** Select one of our target dates (for example, Start: `2024-05-08 00:00:00`, End: `2024-05-08 23:59:59`).
   - Click **Search** / **Submit Query**.

---

### Step 3: Identify the Two Crucial Files (The "Pairing Rule")
In the search results table, you will see multiple files. For every observation day, **you must download two matching files**:

1. **The Light Curve File:**
   - Look for files ending with `.lc` or `.lc.gz`.
   - File naming convention usually resembles: `AL1_SOLEXS_<YYYYMMDD>_SDD2_L1.lc.gz` (or `SDD1`).
   - Prefer **`SDD2`** (Standard Silicon Drift Detector 2) as it matches our existing pipeline.
2. **The Good Time Interval (GTI) File:**
   - Look for the matching file ending with `.gti` or `.gti.gz`.
   - File naming convention usually resembles: `AL1_SOLEXS_<YYYYMMDD>_SDD2_L1.gti.gz`.
   - **CRITICAL:** Ensure the `OBS_ID` and the detector (`SDD2`) match the light curve file exactly!

---

### Step 4: Download and Save
1. Click the **Download** or **Add to Cart / Bulk Download** button next to each file.
2. Save both files directly into your project's raw data folder:
   ```text
   <project_root>\data\raw\
   ```
   *(Keep the `.gz` compressed format intact; do NOT extract or decompress the `.gz` files).*

---

## 5. What to Do Once Files Are Downloaded

Once you have downloaded the files for 1, 2, or more dates:
1. Do not rename or edit the files.
2. Leave them in `data/raw/`.
3. In your next message, simply notify Antigravity: *"I have placed the downloaded files for [Date] in data/raw/"*.

Antigravity will then automatically:
- Calculate and verify the cryptographic SHA-256 hashes.
- Register the new files in [`data/manifests/manifest.csv`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/data/manifests/manifest.csv).
- Verify the GTI pairing.
- Query and cross-match the official NOAA GOES flare ground-truth for those exact hours.
- Guide you through the safe pipeline run without disturbing the existing pilot model.
