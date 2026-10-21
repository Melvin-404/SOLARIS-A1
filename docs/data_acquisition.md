# Official Data Access and Acquisition Guidance: SOLARIS-A1

## Overview
This document provides instructions for the student researcher to manually obtain authentic Aditya-L1 Solar Low Energy X-ray Spectrometer (SoLEXS) Level-1 observation data from the official Indian Space Research Organisation (ISRO) archive, record cryptographic provenance, and maintain data integrity throughout project `SOLARIS-A1`.

---

## 1. Official Data Source
- **Primary Archive:** The official source for all Level-1 Aditya-L1 science data is the **ISRO Indian Space Science Data Centre (ISSDC) PRADAN (Policy and PRocedures for Scientific Data Dissemination Archive)** portal.
- **Access Protocol:** The student researcher must navigate to the PRADAN portal starting from the official ISRO / ISSDC website ([VERIFY URL FROM OFFICIAL SITE]).
- **Recording Archive URL:** Because portal access URLs and login endpoints may update over mission lifecycles, the student must document the exact URL used for data retrieval in the provenance manifest.
- **Prohibition on Automated Scraping:** Automated scrapers, unofficial mirrors, and third-party redistribution sites are strictly prohibited. All data must be fetched directly by the student researcher through official ISSDC channels.

---

## 2. User Account and Data-Use Terms
- **Account Registration:** Access to ISSDC PRADAN may require creating an authorized user account using an academic or personal email address.
- **Terms of Service:** The student must review and adhere to all ISSDC PRADAN terms of service, user agreements, and data access policies.
- **No Circumvention:** The student must never attempt to bypass, circumvent, or script around access controls, authentication barriers, or CAPTCHA mechanisms on the portal.

---

## 3. Locating SoLEXS Level-1 Products
When navigating the PRADAN search interface, the student should filter for the following product attributes:
- **Mission:** `Aditya-L1` [TO BE CONFIRMED ON THE PORTAL]
- **Payload / Instrument:** `SoLEXS` (Solar Low Energy X-ray Spectrometer) [TO BE CONFIRMED ON THE PORTAL]
- **Data Processing Level:** `Level-1` (or `L1`) [TO BE CONFIRMED ON THE PORTAL]
- **Product Type 1 (Science Light Curve):** Soft X-ray light-curve FITS files containing integrated count rates and time series [TO BE CONFIRMED ON THE PORTAL].
- **Product Type 2 (Good Time Intervals - GTI):** Corresponding Level-1 GTI FITS files specifying valid observation intervals, spacecraft day/night passes, and detector health windows [TO BE CONFIRMED ON THE PORTAL].
- **Observation Epochs:** Target observations covering solar flare events identified in independent solar catalogues (e.g., GOES flare catalogue) as well as extended non-flaring quiet-Sun intervals.

*Note: The exact terminology, filter dropdown labels, and product category codes must be visually confirmed on the portal by the student and logged in the manifest.*

---

## 4. Light-Curve and GTI Pairing Rule
A fundamental requirement for valid scientific analysis in `SOLARIS-A1` is the strict temporal and observational pairing between each science light-curve file and its corresponding Good Time Interval (GTI) file.

- **Pairing Rule:** Every Level-1 light-curve FITS file must have an explicitly paired Level-1 GTI FITS file covering the identical observation window and pointing epoch.
- **How to Verify Pairing:**
  1. Inspect the Observation ID (`OBS_ID`) or Target ID associated with both products on the portal [TO BE CONFIRMED ON THE PORTAL].
  2. Confirm that the observation start time and end time displayed on the portal match between the light-curve file and the GTI file.
  3. Record the exact filename of the paired GTI file in the light curve's `paired_gti_file` column in the manifest.
  4. Set `pairing_verified` to `yes` only after manual confirmation.
- **Unpaired Products:** Any light-curve file lacking an authentic GTI file must be marked with `pairing_verified = no`. Unpaired files must never be assigned a guessed or synthetic GTI file; downstream quality filters will reject unpaired files.

---

## 5. Recording Provenance and Checksums
For every downloaded FITS file, the student must immediately record a row in `data/manifests/manifest.csv` containing:
1. `file_name`: Exact file name as saved to disk.
2. `file_type`: `LIGHTCURVE`, `GTI`, or `OTHER`.
3. `observation_id`: Observation identifier shown on the portal [TO BE CONFIRMED ON THE PORTAL].
4. `start_time_as_displayed`: Start timestamp shown on the portal.
5. `end_time_as_displayed`: End timestamp shown on the portal.
6. `time_system_as_displayed`: Time standard shown on the portal (e.g., UTC, MET, TAI) [TO BE CONFIRMED ON THE PORTAL].
7. `portal_url`: Specific PRADAN URL from which the file was fetched.
8. `product_label_as_displayed`: Full product descriptor or title displayed in the portal results table.
9. `download_date`: Date of download in `YYYY-MM-DD` format.
10. `sha256`: Cryptographic SHA-256 hash of the downloaded file.
11. `file_size_bytes`: Exact byte size of the file on disk.
12. `paired_gti_file`: Filename of the associated GTI file (for light curves) or self/none (for GTI files).
13. `pairing_verified`: `yes` or `no`.
14. `notes`: Any relevant archive notes, processing pipeline versions, or flags.

### Calculating SHA-256 on Windows
In PowerShell, run:
```powershell
Get-FileHash data\raw\<filename>.fits -Algorithm SHA256
```
Copy the resulting `Hash` string (hexadecimal) into the manifest.

---

## 6. Local Storage Layout and Immutability
- **Destination Directory:** Place all downloaded files directly into:
  ```text
  data/raw/
  ```
  *(or `data/raw/gti/` if GTI files are categorized separately, as documented in the manifest).*
- **Strict Immutability:** Raw files must remain completely untouched.
  - Do NOT modify, resave, or overwrite any downloaded file.
  - Do NOT rename files unless the original name collides with an existing file, in which case the exact mapping must be recorded in the manifest.
  - If files are downloaded as `.fits.gz` or `.tar`, do NOT uncompress or overwrite the original archive inside `data/raw/` without documenting the uncompressed filenames.

---

## 7. Common Acquisition Issues and Remediation

| Issue | Description | Remediation Protocol |
| :--- | :--- | :--- |
| **Partial / Incomplete Download** | Network drop causes incomplete file transfer. | Compare byte size and SHA-256 against portal metadata. If hash does not match, re-download the file. |
| **Duplicate Downloads** | Same observation downloaded multiple times under slightly different names. | Run `python scripts/check_manifest.py` to identify duplicate hashes; delete the duplicate file and retain the primary record. |
| **Hash Mismatch on Re-Download** | Archive republished a revised Level-1 data version. | Document the archive version increment in the `notes` column; archive the older file under a versioned subfolder if required. |
| **Filename Collisions** | Different observation segments sharing generic names (e.g., `lightcurve.fits`). | Document the renamed target name in `file_name` and record the original portal filename in `notes`. |

---

## 8. Compliance, Attribution, and Citation
- **ISRO / ISSDC Data Policy:** The student must verify the official citation and acknowledgement guidelines published on the ISSDC PRADAN portal.
- **Do Not Invent Citation Text:** The exact phrasing requested by ISRO for research publications utilizing Aditya-L1 SoLEXS data must be copied directly from the official portal and documented in project reports.
- **Public Dissemination:** Ensure that all usage of Level-1 data complies with ISRO's scientific data dissemination policy regarding public release, academic theses, and journal submissions.
