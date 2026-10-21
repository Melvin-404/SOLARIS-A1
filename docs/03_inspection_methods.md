# FITS Inspection Methods and Inventory Interpretation: SOLARIS-A1

## Overview
This document describes the architectural principles, modules, and interpretation guidelines for the Stage 3 FITS inspection pipeline in project `SOLARIS-A1`.

The inspection tools are engineered to be **strictly non-destructive and hypothesis-free**:
1. Files are opened exclusively in read-only mode (`mode='readonly', memmap=False`).
2. No column names (such as `TIME` or `RATE`) are hardcoded as definitive physical axes; they are detected as candidates and flagged for human student review.
3. Checksums (SHA-256) are calculated before and after every inspection run to prove immutability.

---

## 1. Inspection Subsystem Modules

### 1.1 `solar_flare.inspection.fits_inspect`
Core functions for examining FITS file headers, binary tables, and data columns:
- `list_hdus(path)`: Scans all header-data units and returns extension names, types, dimensions, row counts, and column counts.
- `read_header_dict(path, hdu)`: Extracts header keywords, values, and comments for any extension.
- `describe_columns(path, hdu)`: Returns column names, FITS data formats (`TFORM`), physical units (`TUNIT`), and display formats.
- `summarise_time_columns(path, hdu)`: Identifies candidate time axes, tests for monotonicity, calculates median cadence spacing, and flags gaps.
- `summarise_numeric_columns(path, hdu)`: Computes row counts, NaN counts, infinite value counts, min, max, mean, and median for every numerical column.

### 1.2 `solar_flare.inspection.time_systems`
Inspects astronomical time keywords across HDUs:
- Extracts `TIMESYS`, `MJDREF`, `MJDREFI`, `MJDREFF`, `TIMEZERO`, `TSTART`, `TSTOP`, `TIMEDEL`, `TIMEUNIT`, `TIMEREF`, `DATE-OBS`, `DATE-END`.
- Distinguishes observed facts from candidate interpretations.
- All candidate interpretations are explicitly tagged: `(candidate interpretation — requires confirmation against official documentation)`.

### 1.3 `solar_flare.inspection.inventory`
Compiles an end-to-end dataset inventory table:
- Maps manifest records to files on disk.
- Detects candidate column roles:
  - If a single candidate is found, it is recorded (e.g., `TIME`, `COUNTS`).
  - If multiple or ambiguous candidates are found, the role is marked `UNRESOLVED (<candidates>)`.
- Identifies paired GTI files and verifies whether corresponding GTI files exist on disk.
- Exports tabular summaries to `results/inventory/inventory.csv` and `results/inventory/inventory.json`.

---

## 2. Command-Line Usage

Execute the inspection pipeline using the CLI tool:
```powershell
python scripts/inspect_fits.py
```

### Command Options:
- `--raw-dir <path>`: Directory containing raw FITS files (defaults to `data/raw`).
- `--manifest <path>`: Path to manifest CSV (defaults to `data/manifests/manifest.csv`).
- `--out-dir <path>`: Directory for generated inspection reports (defaults to `results/inventory`).

### Generated Artifacts:
1. `results/inventory/inventory.csv`: Tabular index of all inspected files, row counts, and candidate roles.
2. `results/inventory/inventory.json`: JSON serialization of the inventory.
3. `results/inventory/inspection_report.md`: Comprehensive per-file breakdown of HDUs, columns, statistics, and time parameters.
4. `results/inventory/open_questions.md`: Filtered register of unresolved questions, missing physical units, and zero-length tables requiring student resolution.

---

## 3. Interpreting Inventory and Inspection Outputs

### 3.1 Understanding Column Candidates and "UNRESOLVED"
- When a file has unambiguous column names (e.g., `TIME` and `COUNTS`), they are proposed as candidate time and count axes.
- If a table has multiple candidate columns (e.g., `TIME_UTC` and `TIME_MET`, or multiple energy channels like `RATE_CH1`, `RATE_CH2`), the column role is automatically designated as `UNRESOLVED`.
- The student researcher must resolve all `UNRESOLVED` designations by consulting official ISRO SoLEXS Level-1 documentation before Stage 4.

### 3.2 Time Systems and Reference Epochs
- In SoLEXS Level-1 files, `MJDREFI = 40587` is commonly observed alongside `TIMESYS = UTC`.
  - MJD 40587.0 corresponds to `1970-01-01 00:00:00 UTC` (Unix Epoch).
  - Elapsed seconds since this epoch produce timestamps matching `DATE-OBS` (e.g., `1792281600.0` seconds corresponds to `2026-10-18 00:00:00 UTC`).
  - *Action for Student:* Confirm whether spacecraft clock drift, leap seconds, or local clock offsets require adjustment.

### 3.3 Missing Units
- If `TUNIT` keywords are missing in the FITS header, columns are flagged in `open_questions.md`.
- *Action for Student:* Verify whether the `COUNTS` column represents integrated raw counts per 1-second bin, or count rate in counts per second (cts/s).

### 3.4 Zero-Row Extensions
- In multi-detector setups (e.g., SDD1 and SDD2), some extensions or detectors may have 0 rows in specific observation runs (e.g., SDD1 GTI table with 0 rows).
- *Action for Student:* Confirm the operational status of the secondary detector during the observation interval.
