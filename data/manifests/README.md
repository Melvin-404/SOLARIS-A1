# Data Manifests and Provenance Directory

This directory contains provenance records and verification manifests for all downloaded observation data in project `SOLARIS-A1`.

The primary manifest file is maintained manually by the student researcher:
```text
data/manifests/manifest.csv
```
A template is provided in [`data/manifests/manifest_template.csv`](manifest_template.csv).

---

## Manifest Column Specifications

Every file downloaded from the official ISRO ISSDC PRADAN portal must be recorded with the following 14 columns:

| Column Name | Allowed Values / Format | Description |
| :--- | :--- | :--- |
| `file_name` | String (filename) | Exact filename as stored in `data/raw/` (e.g., `solexs_l1_20240101_v1.fits`). |
| `file_type` | `LIGHTCURVE` \| `GTI` \| `OTHER` | Classification of the product. |
| `observation_id` | String | Observation identifier as displayed on the PRADAN portal. |
| `start_time_as_displayed` | String (timestamp) | Observation start timestamp displayed on the portal. |
| `end_time_as_displayed` | String (timestamp) | Observation end timestamp displayed on the portal. |
| `time_system_as_displayed` | String (e.g., `UTC`, `MET`) | Time standard specified on the portal. |
| `portal_url` | String (URL) | URL of the portal page where the file was retrieved. |
| `product_label_as_displayed`| String | Descriptive label or title shown in the search results table. |
| `download_date` | `YYYY-MM-DD` | Date when the file was fetched. |
| `sha256` | 64-char Hexadecimal String | Cryptographic SHA-256 hash computed using `Get-FileHash`. |
| `file_size_bytes` | Integer | Exact file size in bytes on disk. |
| `paired_gti_file` | String (filename) | For `LIGHTCURVE`: filename of paired GTI file. For `GTI`: self or `N/A`. |
| `pairing_verified` | `yes` \| `no` | Confirmation that time windows and observation IDs match. |
| `notes` | String | Processing version, archive tags, or anomalies. |

---

## Verification Workflow
The student researcher can verify the consistency of their manifest against files stored on disk by running:
```powershell
python scripts/check_manifest.py data/manifests/manifest.csv
```
This utility checks that:
- Every file listed in the manifest exists in `data/raw/`.
- Every file on disk in `data/raw/` is tracked in the manifest.
- SHA-256 hashes match bit-for-bit with the files on disk.
- Every `LIGHTCURVE` entry has an existing, verified `paired_gti_file`.
