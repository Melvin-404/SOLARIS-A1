# Stage 6 Completion Report: Ground-Truth Research and Labelling Protocol

**Project:** `SOLARIS-A1` (Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations)  
**Stage:** Stage 6 — Ground-Truth Research and Labelling Protocol  
**Date:** 2026-10-21  
**Status:** DRAFT PROTOCOL COMPLETE — LABELLING REFUSAL GUARD ENFORCED  
**Scientific Gate:** G3 (PENDING HUMAN APPROVAL)

---

## 1. Executive Summary and Mandatory Gate Declarations

In Stage 6, independent solar flare-event ground-truth sources were researched, documented, and evaluated for temporal and definitional compatibility with Aditya-L1 SoLEXS observations. A rigorous labelling policy draft was established with every decision held strictly **PENDING** for human researcher approval. Schema, provenance, tolerance matching, and a strictly guarded label generator skeleton were implemented.

### Mandatory Declarations
- **Supervised labelling: BLOCKED pending G3 approval.**
- **Stage 7 Progression Statement:** Stage 7 may proceed with preprocessing and segmentation only if Decision D-14 (sub-cadence jitter/dropout handling) is approved. Stage 7 does not depend on labels.
- **Label Generation Status:** ZERO labels, event instances, or training tables were generated. Label output and dataset directories contain zero label files.

---

## 2. Files Created and Modified

### A. Documentation Created
1. `docs/07_ground_truth_research.md` — Ground-truth sourcing strategy, source taxonomy, records of accessed independent flare catalogues, rejected sources, and unverified source declarations.
2. `docs/08_labelling_policy.md` — Formal labelling policy draft (status: `Status: DRAFT — REQUIRES HUMAN APPROVAL`) defining onset/peak/end, tolerance $\Delta t$, verified positives, verified negatives (embargo), ambiguous events, and coverage requirements.
3. `docs/09_time_compatibility.md` — Compatibility analysis covering reference epochs (Unix epoch / MJD 40587), time scales (UTC vs MET/TAI), leap-second treatment, and L1-Earth light travel time delay (~5.0 s).

### B. Configuration and Decisions Modified
1. `config/decisions.yaml` — Updated with D-01, D-02, D-03, D-04, D-08, D-10, D-15 marked with status `PENDING` (or `PROVISIONAL` for D-10), `value: null`, and `approved_by: null`.
2. `docs/01_decision_log.md` — Appended with Decision D-15 and Stage 6 progress notes.

### C. Data Manifests Created
1. `data/manifests/event_sources.csv` — Event sources manifest with full schema (16 columns), recording 4 accessed candidate sources with verification and independence metadata.

### D. Source Code Created
1. `src/solar_flare/labels/__init__.py` — Package initialization for labels subsystem.
2. `src/solar_flare/labels/schema.py` — Dataclass `EventRecord` and `validate_event_records()` enforcing strict ordering ($t_{\text{onset}} \le t_{\text{peak}} \le t_{\text{end}}$), ISO 8601 parsing, unique `event_id`, source registration, and time-system approval check.
3. `src/solar_flare/labels/policy.py` — `assert_labelling_approved()` policy guard enforcing Gate G3 by dynamically parsing `docs/08_labelling_policy.md` and `config/decisions.yaml` on every invocation.
4. `src/solar_flare/labels/provenance.py` — Manifest I/O helper functions for `data/manifests/event_sources.csv`. Never inserts automatic rows.
5. `src/solar_flare/labels/matching.py` — Interval overlap (`interval_overlap_seconds`) and window inclusion (`is_event_in_window`). `tolerance_seconds` is a strictly required argument with NO default value.
6. `src/solar_flare/labels/generate.py` — Label generator skeleton whose very first line invokes `assert_labelling_approved()`.
7. `src/solar_flare/labels/compatibility.py` — Temporal overlap calculator (`report_temporal_overlap`) and automated compatibility report generator.

### E. Scripts and Command-Line Tools Created
1. `scripts/check_labelling_guard.py` — Standalone CLI tool demonstrating and verifying Gate G3 guard refusal.
2. `scripts/run_compatibility.py` — CLI tool generating compatibility reports across all registered sources.

### F. Automated Test Suites Created
1. `tests/test_label_schema.py` — 6 tests verifying valid records, onset > peak refusal, missing/unrecognized time system, duplicate event IDs, and unregistered source IDs.
2. `tests/test_policy_guard.py` — 3 tests verifying guard refusal on real draft files, successful execution on synthetic approved fixtures in `tmp_path`, and refusal when decisions remain pending.
3. `tests/test_matching.py` — 4 tests verifying exact overlap duration, tolerance boundary expansion, error raising when tolerance is omitted, and window matching.
4. `tests/test_compatibility.py` — 5 tests verifying `TIME_SYSTEM_UNCONFIRMED` assignment, `NO OVERLAP` computation, and compatibility evaluation.
5. `tests/test_no_invented_sources.py` — 1 static verification test ensuring no URLs are cited in `docs/07_ground_truth_research.md` without registration in `data/manifests/event_sources.csv`.

### G. Results Created
1. `results/labels/compatibility_report.json` — Machine-readable compatibility evaluation.
2. `results/labels/compatibility_report.md` — Human-readable markdown compatibility report.
3. `results/labels/STAGE6_COMPLETION.md` — This stage completion report.

---

## 3. Sources Accessed, Rejected, and Marked Unverified

All web sources evaluated were accessed directly and recorded in `data/manifests/event_sources.csv`. No unaccessed source is presented as factual.

| Source ID | Name as Displayed | URL Actually Accessed | Access Date | Instrument / Coverage | Independence | Human Verified | Status / Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SRC_NOAA_SWPC` | NOAA Space Weather Prediction Center Events | `https://www.swpc.noaa.gov/products/solar-and-geophysical-event-reports` | 2026-10-21 | GOES-16/18 XRS, Global Optical (1996–present) | Yes (Independent) | `no` | **ACCESSED / EVALUATED.** Status: `TIME_SYSTEM_UNCONFIRMED`. Live daily operational log. |
| `SRC_NOAA_NCEI_GOES` | NOAA NCEI GOES Satellite Data Archive | `https://www.ncei.noaa.gov/products/space-weather/goes-r-series-satellites` | 2026-10-21 | GOES EXIS / XRS (1975–present) | Yes (Independent) | `no` | **ACCESSED / EVALUATED (RECOMMENDED).** Status: `TIME_SYSTEM_UNCONFIRMED`. Definitive soft X-ray baseline. |
| `SRC_NASA_HEK` | NASA LMSAL Heliophysics Event Knowledgebase | `https://www.lmsal.com/hek/` | 2026-10-21 | SDO, GOES, RHESSI (2010–present) | Yes (Independent) | `no` | **ACCESSED / EVALUATED.** Status: `TIME_SYSTEM_UNCONFIRMED`. Multi-instrument aggregator. |
| `SRC_ISRO_PRADAN` | ISRO ISSDC Aditya-L1 PRADAN Portal | `https://pradan.issdc.gov.in/` | 2026-10-21 | Aditya-L1 SoLEXS (2024–present) | No (Circular) | `no` | **REJECTED FOR LABELLING.** Deriving labels from SoLEXS Level-1/2 products to evaluate SoLEXS ML models is strictly circular. |

### Statement on Unverified Sources
The following catalog categories were investigated conceptually but were **NOT VERIFIED** via direct network access during this stage:
- Hinode/XRT flare catalog (`NOT VERIFIED`)
- RHESSI microflare lists (`NOT VERIFIED`)
- STIX/Solar Orbiter catalog (`NOT VERIFIED`)
In accordance with Stage 6 constraints, no unverified catalogue is included in the active sources manifest or used in compatibility assessment.

---

## 4. Compatibility Status Per Source

Because SoLEXS time system Decision D-10 remains `PROVISIONAL pending G1 confirmation` and no arbitrary time conversions are permitted, the compatibility status for all candidates is:

```text
- SRC_NOAA_SWPC:       TIME_SYSTEM_UNCONFIRMED
- SRC_NOAA_NCEI_GOES:  TIME_SYSTEM_UNCONFIRMED
- SRC_NASA_HEK:        TIME_SYSTEM_UNCONFIRMED
- SRC_ISRO_PRADAN:     TIME_SYSTEM_UNCONFIRMED (Rejected for labelling)
```

**Outcome:** NO VERIFIED INDEPENDENT SOURCE WITH CONFIRMED TIME COMPATIBILITY. Supervised labelling cannot proceed until the human researcher confirms Decision D-10.

---

## 5. Full List of PENDING Decisions and Policy Sections

| Decision ID | Title | Policy Section | Status | Value | Approved By |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **D-01** | Source of verified flare-event labels | Section 4 (Source Selection) | `PENDING` | `null` | `null` |
| **D-02** | Time-matching tolerance ($\Delta t_{\text{match}}$) | Section 3 (Matching Tolerance) | `PENDING` | `null` | `null` |
| **D-03** | Definition of flare onset, peak, and end | Section 2 (Event Boundary Definitions) | `PENDING` | `null` | `null` |
| **D-04** | Ambiguous, overlapping, & partially observed events | Section 7 (Ambiguous & Truncated Events) | `PENDING` | `null` | `null` |
| **D-08** | Definition of verified negative intervals & embargo | Section 6 (Verified Negative Windows) | `PENDING` | `null` | `null` |
| **D-10** | Time system confirmation (UTC vs MET/Unix) | Section 3 (Reference Epoch & Time System) | `PROVISIONAL` | `null` | `null` |
| **D-15** | Minimum number of independent positive events | Section 9 (Minimum Dataset Size Gate) | `PENDING` | `null` | `null` |

---

## 6. Policy Guard Execution Output

CLI command executed: `python scripts/check_labelling_guard.py`  
Exit code: `1` (Guard Refusal)

```text
======================================================================
SOLARIS-A1 GATE G3 LABELLING POLICY GUARD CHECK
======================================================================
[REFUSAL ENFORCED] Gate G3 Guard successfully refused execution:
Supervised labelling is strictly BLOCKED pending Gate G3 human approval.
The following approval items must be confirmed by the human researcher:
  - Policy status line in '08_labelling_policy.md' is 'DRAFT — REQUIRES HUMAN APPROVAL'. Requires exact format 'Status: APPROVED by <name>, date <YYYY-MM-DD>'.
  - Decision 'D-01' status is 'PENDING' (required: 'APPROVED')
  - Decision 'D-02' status is 'PENDING' (required: 'APPROVED')
  - Decision 'D-03' status is 'PENDING' (required: 'APPROVED')
  - Decision 'D-04' status is 'PENDING' (required: 'APPROVED')
  - Decision 'D-08' status is 'PENDING' (required: 'APPROVED')
  - Decision 'D-10' status is 'PROVISIONAL' (required: 'APPROVED')
  - Decision 'D-15' status is 'PENDING' (required: 'APPROVED')
======================================================================
Supervised label generation is safely BLOCKED as required in Stage 6.
```

---

## 7. Test Suite Results

Test runner executed: `pytest -v`  
Total tests: **80 passed**, 0 failed, 0 warnings.

```text
tests/test_bursts.py (3 tests) ........................................ PASSED
tests/test_cadence.py (4 tests) ....................................... PASSED
tests/test_compatibility.py (5 tests) ................................. PASSED
tests/test_config.py (6 tests) ........................................ PASSED
tests/test_event_comparison.py (3 tests) ............................... PASSED
tests/test_gti_coverage.py (4 tests) .................................. PASSED
tests/test_inspection.py (9 tests) .................................... PASSED
tests/test_label_schema.py (6 tests) .................................. PASSED
tests/test_logging.py (2 tests) ....................................... PASSED
tests/test_manifest.py (11 tests) ..................................... PASSED
tests/test_matching.py (4 tests) ...................................... PASSED
tests/test_no_invented_sources.py (1 test) ............................ PASSED
tests/test_no_label_writes.py (2 tests) ............................... PASSED
tests/test_paths.py (4 tests) ......................................... PASSED
tests/test_policy_guard.py (3 tests) .................................. PASSED
tests/test_quality_checks.py (8 tests) ................................ PASSED
tests/test_roles.py (2 tests) ......................................... PASSED
tests/test_variability.py (3 tests) ................................... PASSED
============================= 80 passed in 2.20s ==============================
```

---

## 8. Data Immutability and Output Verification

- **Raw Data Integrity:** Checksums of all files under `data/raw/` remain bit-for-bit identical to original acquisition hashes.
- **Label Directory Check:** `data/processed/datasets/` does not exist; no tabular label matrices or event labels have been written.
- **Stage 7 Clearance:** Non-destructive preprocessing and window segmentation may be developed in Stage 7 upon approval of Decision D-14.
