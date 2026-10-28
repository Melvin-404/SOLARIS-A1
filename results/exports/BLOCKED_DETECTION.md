# DATASET EXPORT BLOCKED: DETECTION (Gate G3 (Ground-Truth Labelling Policy))

**Execution Timestamp:** `2026-10-28T17:40:09.883407+00:00`  
**Task:** `detection`  
**Status:** `BLOCKED — PREREQUISITES NOT MET`  

--- 

## Missing Scientific Prerequisites:

- Gate G3 draft refusal: requires approval

--- 

## Next Required Human Action:
1. Review and formally approve the labelling policy in `docs/`.
2. Confirm all pending decisions in `config/decisions.yaml` with status `APPROVED` and non-null values.
3. Place approved independent flare event records in `data/manifests/event_records_approved.csv`.
4. Re-run `python scripts/export_dataset.py --task detection`.
