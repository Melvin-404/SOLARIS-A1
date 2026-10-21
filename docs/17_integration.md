# SOLARIS-A1 Pipeline Integration, Lineage & Status Architecture (Stage 13)

**Document ID:** `DOC-17-PIPELINE-INTEGRATION`  
**Milestone:** Stage 13 — Dashboard and Pipeline Integration  
**Governance Status:** Standardized Scientific Methodology  

---

## 1. Executive Summary

Stage 13 connects the SOLARIS-A1 Streamlit presentation layer with the underlying scientific data products produced across Stages 3 through 11.

To ensure reproducible, auditable science without data corruption or accidental mutation:
1. **Pure Status Function (`pipeline_status`)**: Evaluates the health and readiness of all stages with zero side effects.
2. **Schema & Lineage Validation (`integrity.py`)**: Formally validates artifact schemas and tracks cryptographic SHA-256 lineage from raw Level-1 observations through feature matrices, model selections, and single-shot evaluation locks.
3. **Stale-Artifact Detection**: Flags any discrepancy between current configuration parameters (`config/default.yaml`) and recorded artifact parameters (`build_log.json`, `run_manifest.json`).
4. **Architectural Isolation**: Guaranteed by automated AST tests ensuring the dashboard cannot import training pipelines, execute fitting methods, or write to raw or results directories.

---

## 2. Pipeline Status Categories & Meanings

The pipeline status function assigns exactly one unambiguous status to each stage:

| Status Code | Scientific Meaning | Required Action |
| :---: | :--- | :--- |
| **`COMPLETE`** | All required stage artifacts exist, schemas are valid, and cryptographic hashes match. | Ready for downstream use. |
| **`PROVISIONAL`** | Stage artifacts exist and pass validation, but depend on provisional parameters or thresholds awaiting human confirmation. | Valid for development; requires human researcher approval before final conclusions. |
| **`PARTIAL`** | Some expected artifacts are present, but others are missing. | Re-run stage to complete missing outputs. |
| **`MISSING`** | No outputs found for this stage. | Run the stage's execution script. |
| **`BLOCKED`** | Execution was strictly stopped by a safety guard (e.g. `AWAITING_G*.md` or `BLOCKED_*.md`) pending human gate approval. | Review blocking gate requirements with the human researcher. |
| **`STALE`** | Configuration parameters or upstream artifact hashes have changed since this stage was generated. | Regenerate stage following the pipeline execution sequence. |
| **`ERROR`** | An artifact exists but failed schema validation or suffered cryptographic hash tampering. | Investigate corruption; do not proceed with downstream stages. |

---

## 3. Artifact Dependency Graph

```text
[Raw Level-1 FITS Data] (data/raw/)
       │
       ▼
[Stage 3: Inventory] (results/inventory/inventory.csv)
       │
       ▼
[Stage 4: Data Quality] (results/quality/summary.csv, quality_report.md)
       │
       ▼
[Stage 5: EDA & Burst Candidates] (results/eda/candidate_bursts.csv)
       │
       ▼
[Stage 6: Ground-Truth Policy (Gate G3)] (docs/08_labelling_policy.md) ──► BLOCKED (Pending G3)
       │
       ▼
[Stage 7: Preprocessing & Segments] (data/processed/segments/, results/preprocessing/)
       │
       ▼
[Stage 8: Sliding Windows & Features] (data/processed/features/, results/features/build_log.json)
       │
       ▼
[Stage 9: Dataset Export (Gates G3/G6)] (data/processed/datasets/) ──► BLOCKED (Pending G3/G6)
       │
       ▼
[Stage 10: Model Training (Gate G7)] (results/experiments/<id>/sealed/) ──► BLOCKED (Pending G7)
       │
       ▼
[Stage 11: Single-Shot Evaluation (Gate G8)] (results/experiments/<id>/evaluation/) ──► BLOCKED (Pending G8)
       │
       ▼
[Stage 12/13: Dashboard Integration] (dashboard/app.py) ──► Read-only inspection & lineage audit
```

---

## 4. End-to-End Regeneration Sequence

When upstream parameters, raw files, or policies change, stages must be regenerated in strict topological order:

```powershell
# 1. Inspect FITS files (Stage 3)
python scripts/inspect_fits.py

# 2. Quality Assessment (Stage 4)
python scripts/run_quality.py --raw-dir data/raw --manifest data/manifests/manifest.csv --out-dir results/quality

# 3. Exploratory Data Analysis (Stage 5)
python scripts/run_eda.py --out-dir results/eda

# 4. Check Labelling Policy Guard (Stage 6)
python scripts/check_labelling_guard.py

# 5. Preprocessing & Continuous Segmentation (Stage 7)
python scripts/run_preprocessing.py --stem all

# 6. Sliding Windows & Feature Engineering (Stage 8)
python scripts/build_features.py --stem all

# 7. Dataset Export (Stage 9 — Requires Gate G3/G6 approval)
python scripts/export_dataset.py --task detection
python scripts/export_dataset.py --task prediction

# 8. Model Training & Test Set Sealing (Stage 10 — Requires Gate G7 frozen protocol)
python scripts/train_models.py --protocol config/training_protocol.yaml

# 9. Single-Shot Test Set Evaluation (Stage 11 — Requires Gate G8 approval)
python scripts/evaluate_locked_models.py --experiment-id <experiment_id>

# 10. Launch Interactive Dashboard (Stage 12/13)
python -m streamlit run dashboard/app.py
```

---

## 5. What Triggers STALE Status?

A stage is flagged as `STALE` when:
1. **Parameter Drift**: A configuration parameter in `config/default.yaml` (e.g. `window_length_seconds`, `stride_seconds`, or `max_gap_seconds`) is changed after downstream artifacts have already been computed. The loader identifies that the recorded parameter in `build_log.json` differs from current configuration.
2. **Upstream Mutation**: A raw file or segment file was modified, causing its SHA-256 hash to mismatch the recorded hash in downstream audit logs (`segment_hashes_before` or `raw_hashes_before`).
3. **Protocol Drift**: A training protocol YAML file was altered after an experiment was trained.

When `STALE` is triggered:
- The dashboard displays a prominent orange warning banner.
- Both the recorded value and current configuration value are displayed side-by-side.
- The pipeline status function reports `STALE` with diagnostic details.
- No automatic repair or regeneration is attempted; the human researcher must intentionally execute the regeneration sequence.
