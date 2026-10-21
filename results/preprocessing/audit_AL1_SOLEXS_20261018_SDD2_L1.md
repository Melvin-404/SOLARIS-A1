# Preprocessing & Segmentation Audit: `AL1_SOLEXS_20261018_SDD2_L1`

- **Run Mode:** **PROVISIONAL (DEVELOPMENT)**
- **Processing Timestamp (UTC):** `2026-10-21T08:07:51.081968+00:00`
- **Software Version:** `SOLARIS-A1 Stage 7 (1.0.0)`
- **Source Raw Hash (Before):** `1c1a5371663267d39a8e89c8d29640aed69dcad427f0d8139b97e61071746c94`
- **Source Raw Hash (After):**  `1c1a5371663267d39a8e89c8d29640aed69dcad427f0d8139b97e61071746c94`
- **Raw Immutability:** `PASS (100% IDENTICAL)`
- **Mathematical Reconciliation:** `PASS (retained + excluded == original)`

---

## Sample Conservation Table

| Category | Count | Percentage of Original |
| :--- | :--- | :--- |
| **Original Total Samples** | `86,400` | `100.0000%` |
| **Retained in Valid Segments** | `81,379` | `94.1887%` |
| **Total Excluded Samples** | `5,021` | `5.8113%` |
| ↳ Excluded: `NON_FINITE` | `4,849` | `5.6123%` |
| ↳ Excluded: `OUTSIDE_GTI` | `134` | `0.1551%` |
| ↳ Excluded: `SEGMENT_TOO_SHORT` | `38` | `0.0440%` |

---

## Segmentation Results

- **Total Valid Segments:** `4`

| Segment ID | Start (s) | End (s) | Duration (s) | N Samples | Median Cadence (s) | Gap Before (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `AL1_SOLEXS_20261018_SDD2_L1_seg_001` | `1792286428.0` | `1792316628.0` | `30200.0` | `30,201` | `1.0000` | `0.0` |
| `AL1_SOLEXS_20261018_SDD2_L1_seg_002` | `1792316631.0` | `1792323431.0` | `6800.0` | `6,801` | `1.0000` | `3.0` |
| `AL1_SOLEXS_20261018_SDD2_L1_seg_003` | `1792323469.0` | `1792341677.0` | `18208.0` | `18,209` | `1.0000` | `38.0` |
| `AL1_SOLEXS_20261018_SDD2_L1_seg_004` | `1792341831.0` | `1792367998.0` | `26167.0` | `26,168` | `1.0000` | `74.0` |

---

## Preprocessing Parameters Applied

```yaml
time_column: TIME
count_column: COUNTS
flag_column: None
max_gap_seconds: 2.0
min_segment_seconds: 60.0
gti_boundary_convention: START_INCLUSIVE_STOP_EXCLUSIVE
duplicate_timestamp_policy: ERROR
excluded_quality_flags: []
is_final: False
file_format: CSV (pyarrow not present in requirements)
```
