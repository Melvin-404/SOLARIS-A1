# SOLARIS-A1: Unresolved Questions and Observation Anomalies

This document lists all ambiguous roles, missing units, time-system questions, and observational anomalies
identified during the automated Stage 3 inspection. Each item requires review by the student researcher
against official SoLEXS instrument manuals before Stage 4 validation.

**Total Unresolved Items Identified:** 16

---

| File | Category | Unresolved Question / Action Required |
| :--- | :--- | :--- |
| `AL1_SOLEXS_20261018_SDD2_L1.lc.gz` | Missing Physical Unit | Column `TIME` in `RATE` has no recorded unit keyword (TUNIT). Confirm whether counts, count rate (c/s), or flux. |
| `AL1_SOLEXS_20261018_SDD2_L1.lc.gz` | Missing Physical Unit | Column `COUNTS` in `RATE` has no recorded unit keyword (TUNIT). Confirm whether counts, count rate (c/s), or flux. |
| `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` | Time System | Header does not define TIMESYS; time standard is UNRESOLVED. |
| `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` | Time System | TIMEREF keyword missing; barycentric/geocentric/spacecraft clock origin is UNRESOLVED. |
| `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` | Missing Physical Unit | Column `START` in `GTI` has no recorded unit keyword (TUNIT). Confirm whether counts, count rate (c/s), or flux. |
| `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` | Missing Physical Unit | Column `STOP` in `GTI` has no recorded unit keyword (TUNIT). Confirm whether counts, count rate (c/s), or flux. |
| `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` | Time System | Header does not define TIMESYS; time standard is UNRESOLVED. |
| `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` | Time System | TIMEREF keyword missing; barycentric/geocentric/spacecraft clock origin is UNRESOLVED. |
| `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` | Missing Physical Unit | Column `START` in `GTI` has no recorded unit keyword (TUNIT). Confirm whether counts, count rate (c/s), or flux. |
| `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` | Missing Physical Unit | Column `STOP` in `GTI` has no recorded unit keyword (TUNIT). Confirm whether counts, count rate (c/s), or flux. |
| `AL1_SOLEXS_20261018_SDD1_L1.gti.gz` | Zero Rows Table | Extension `GTI` has 0 rows. Verify detector status (e.g., SDD1 vs SDD2 operational state). |
| `AL1_SOLEXS_20261018_SDD2_L1.pi.gz` | Time System | Header does not define TIMESYS; time standard is UNRESOLVED. |
| `AL1_SOLEXS_20261018_SDD2_L1.pi.gz` | Time System | TIMEREF keyword missing; barycentric/geocentric/spacecraft clock origin is UNRESOLVED. |
| `AL1_SOLEXS_20261018_SDD2_L1.pi.gz` | Missing Physical Unit | Column `SPEC_NUM` in `SPECTRUM` has no recorded unit keyword (TUNIT). Confirm whether counts, count rate (c/s), or flux. |
| `AL1_SOLEXS_20261018_SDD2_L1.pi.gz` | Missing Physical Unit | Column `CHANNEL` in `SPECTRUM` has no recorded unit keyword (TUNIT). Confirm whether counts, count rate (c/s), or flux. |
| `AL1_SOLEXS_20261018_SDD2_L1.pi.gz` | Missing Physical Unit | Column `COUNTS` in `SPECTRUM` has no recorded unit keyword (TUNIT). Confirm whether counts, count rate (c/s), or flux. |
