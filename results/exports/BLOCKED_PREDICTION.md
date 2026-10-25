# DATASET EXPORT BLOCKED: PREDICTION (Gate G6 (Pre-Flare Forecasting Policy))

**Execution Timestamp:** `2026-10-25T07:29:34.159032+00:00`  
**Task:** `prediction`  
**Status:** `BLOCKED — PREREQUISITES NOT MET`  

--- 

## Missing Scientific Prerequisites:

- Gate G6 draft refusal: requires approval

--- 

## Next Required Human Action:
1. Review and formally approve the labelling policy in `docs/`.
2. Confirm all pending decisions in `config/decisions.yaml` with status `APPROVED` and non-null values.
3. Place approved independent flare event records in `data/manifests/event_records_approved.csv`.
4. Re-run `python scripts/export_dataset.py --task prediction`.
