# Stage 7: Gate G4 Approval Pending

> **FINAL PREPROCESSING RUN REFUSED**
> The `--final` execution flag requires formal human approval of Gates G1, G2, and Gate G4.

## Unresolved Decisions Required for Final Run

- [ ] **Gate G1 / D-09: Energy band / light-curve column selection is not APPROVED**
- [ ] **Gate G1 / D-10: Time coordinate system alignment is not APPROVED**
- [ ] **Gate G2 / D-13: Quality check thresholds are not APPROVED**
- [ ] **Gate G4 / D-14: Gap splitting (max_gap_seconds) and min_segment_seconds are PENDING**
- [ ] **Gate G4 / D-17: GTI boundary convention is PENDING**

---

## How to Proceed
1. Review provisional outputs produced by development mode in `results/preprocessing/`.
2. Confirm column roles (Gate G1) and quality thresholds (Gate G2).
3. Approve gap threshold `max_gap_seconds` and `min_segment_seconds` (Decision D-14).
4. Approve GTI boundary convention (Decision D-17).
5. Update `config/decisions.yaml` with `status: APPROVED` and `approved_by: <Researcher Name>`.
6. Re-run `python scripts/run_preprocessing.py --final`.
