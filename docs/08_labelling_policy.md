# SOLARIS-A1: Ground-Truth Labelling Policy Specification (Stage 6)

Status: APPROVED by Dr. Melvin / Solar Physics Group, date 2026-10-23

> **CRITICAL SCIENTIFIC GOVERNANCE NOTICE:**
> This document specifies the approved labelling rules, ground-truth matching algorithms,
> and positive/negative window definitions for `SOLARIS-A1` (Task A: Solar Flare Detection;
> Task B: Pre-Flare Forecasting).
> Formally APPROVED by the human researcher at Gate G3.

---

## 1. Decision D-01: Source of Verified Positive Flare Events

### Adopted Source:
- **Adopted Option 1A (`SRC_NOAA_NCEI_GOES`):** NOAA NCEI GOES Level-2 XRS Science-Quality Flare Summaries supplemented by NOAA SWPC Solar Geophysical Event Reports.
- **Approved Source ID:** `SRC_NOAA_NCEI_GOES`
- **Approved By (Human):** Dr. Melvin / Solar Physics Group
- **Date Approved:** 2026-10-23

---

## 2. Decision D-02: Matching Tolerance ($\Delta t_{\text{match}}$) Between Event Timestamps and SoLEXS Samples

### Adopted Tolerance:
- **Adopted Value:** $\Delta t_{\text{match}} = 30.0\text{ s}$
- **Value (seconds):** 30.0
- **Approved By (Human):** Dr. Melvin / Solar Physics Group
- **Date Approved:** 2026-10-23

---

## 3. Decision D-03: Definition of Flare Onset, Peak, and End Boundaries

### Adopted Boundary Criteria:
- **Adopted Criteria:** Option 3A (`OFFICIAL_CATALOG_START_END`)
- **Value:** `OFFICIAL_CATALOG_START_END`
- **Approved By (Human):** Dr. Melvin / Solar Physics Group
- **Date Approved:** 2026-10-23

---

## 4. Positive-Window Labelling Rule for Task A (Solar Flare Detection)

### Adopted Positive Rule:
- **Adopted Rule:** Option 4B (Significant Overlap $\ge 50\%$ or peak epoch containment).
- **Approved By (Human):** Dr. Melvin / Solar Physics Group
- **Date Approved:** 2026-10-23

---

## 5. Decision D-08: Verified-Negative Labelling Rule (Task A and Task B)

### Adopted Embargo Rules:
- **Pre-Flare Embargo Duration (s):** 1800.0 (30 min)
- **Post-Flare Embargo Duration (s):** 3600.0 (60 min)
- **Approved By (Human):** Dr. Melvin / Solar Physics Group
- **Date Approved:** 2026-10-23

---

## 6. Decision D-04: Treatment of Ambiguous, Overlapping, and Partially Observed Events (GTI Truncation)

### Adopted Handling Strategy:
- **Adopted Strategy:** Option 6A (`EXCLUDE_PARTIAL_WINDOWS`). Ambiguous windows assigned `<NA>` with explicit `label_reason`.
- **Approved By (Human):** Dr. Melvin / Solar Physics Group
- **Date Approved:** 2026-10-23

---

## 7. Minimum Observation Coverage Requirements

- **Approved Minimum Window Coverage:** 0.80 (80% finite samples within window)
- **Approved By (Human):** Dr. Melvin / Solar Physics Group
- **Date Approved:** 2026-10-23

---

## 8. Decision D-15: Minimum Number of Independent Positive Events Required for Experimentation

- **Minimum Positive Events Required:** 2 (approved for single-day pilot experimentation)
- **Approved By (Human):** Dr. Melvin / Solar Physics Group
- **Date Approved:** 2026-10-23

---

## 9. Final Human Approval Record

- **Current Policy Status:** `APPROVED`
- **Approved By:** Dr. Melvin / Solar Physics Group
- **Date Approved:** 2026-10-23
- **Gate Clearance:** Gate G3 formally APPROVED.
