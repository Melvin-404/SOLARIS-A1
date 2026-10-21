# SOLARIS-A1: AWAITING GATE G1 HUMAN CONFIRMATION

> **STATUS: PROVISIONAL EXECUTION COMPLETE**
> Stage 4 data quality assessment has completed in **PROVISIONAL mode**.
> No data has been modified, clipped, or removed. No scientific conclusions are declared.
> Completion is strictly PROVISIONAL until the student researcher confirms Gate G1 items.

---

## Required Human Confirmations (Gate G1)

The student researcher must review official SoLEXS instrument documentation and confirm:

1. **Column Roles in Light-Curve Data (`AL1_SOLEXS_20261018_SDD2_L1.lc.gz`):**
   - Confirm column `TIME` represents elapsed observation seconds.
   - Confirm column `COUNTS` represents integrated detector counts or count rate (c/s).
   - Confirm whether a quality flag column exists or if data points are unflagged.

2. **Time System Alignment (Decision D-10):**
   - Confirm `TIMESYS = 'UTC'`, `MJDREFI = 40587` corresponds to Unix epoch (1970-01-01 00:00:00 UTC).
   - Confirm `TSTART = 1792281600.0` corresponds to `2026-10-18 00:00:00 UTC`.

3. **GTI Table Columns and Observation State:**
   - Confirm `START` and `STOP` in `AL1_SOLEXS_20261018_SDD2_L1.gti.gz` represent valid observation intervals.
   - Confirm why detector SDD1 (`AL1_SOLEXS_20261018_SDD1_L1.gti.gz`) has **0 intervals** (instrument status).

4. **Thresholds Confirmation (Gate G2 / Decision D-13):**
   - Review cadence tolerance factor: `1.5`.
   - Review robust MAD candidate spike threshold: `z > 5.0`.
   - Review minimum contiguous zero run length: `5` samples.

---

## How to Confirm Gate G1

1. Inspect [`column_role_evidence.md`](column_role_evidence.md) and [`summary.csv`](summary.csv).
2. Update [`config/column_roles.yaml`](file:///C:/Users/melvi/Desktop/SOLARIS-A1/config/column_roles.yaml) to set status from `PROVISIONAL` to `CONFIRMED`.
3. Record confirmation in `config/decisions.yaml` (D-09, D-10, D-13) and `docs/01_decision_log.md`.
