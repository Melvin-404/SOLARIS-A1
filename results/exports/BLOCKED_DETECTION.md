# DATASET EXPORT BLOCKED: DETECTION (Gate G3 (Ground-Truth Labelling Policy))

**Execution Timestamp:** `2026-10-21T08:45:18.904066+00:00`  
**Task:** `detection`  
**Status:** `BLOCKED — PREREQUISITES NOT MET`  

--- 

## Missing Scientific Prerequisites:

- Supervised labelling is strictly BLOCKED pending Gate G3 human approval.
The following approval items must be confirmed by the human researcher:
  - Policy status line in '08_labelling_policy.md' is 'DRAFT — REQUIRES HUMAN APPROVAL'. Requires exact format 'Status: APPROVED by <name>, date <YYYY-MM-DD>'.
  - Decision 'D-01' status is 'PENDING' (required: 'APPROVED')
  - Decision 'D-02' status is 'PENDING' (required: 'APPROVED')
  - Decision 'D-03' status is 'PENDING' (required: 'APPROVED')
  - Decision 'D-04' status is 'PENDING' (required: 'APPROVED')
  - Decision 'D-08' status is 'PENDING' (required: 'APPROVED')
  - Decision 'D-10' status is 'PROVISIONAL' (required: 'APPROVED')
  - Decision 'D-15' status is 'PENDING' (required: 'APPROVED')
- Approved event records file does not exist at 'data\manifests\event_records_approved.csv'. Gate G3 requires human verification and placement of approved independent flare event records.

--- 

## Next Required Human Action:
1. Review and formally approve the labelling policy in `docs/`.
2. Confirm all pending decisions in `config/decisions.yaml` with status `APPROVED` and non-null values.
3. Place approved independent flare event records in `data/manifests/event_records_approved.csv`.
4. Re-run `python scripts/export_dataset.py --task detection`.
