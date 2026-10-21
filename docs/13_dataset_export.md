# SOLARIS-A1: Dataset Export Specification (Stage 9)

## 1. Objective and Architecture

Stage 9 defines the interface between feature engineering (Stage 8), ground-truth labelling (Stage 6), and downstream machine learning experiments (Stages 10–14). It exports two distinct, completely separated tabular datasets:
1. **Task A (Solar Flare Detection):** Label indicates whether a verified solar flare event occurs within observation window $[w_{\text{start}}, w_{\text{end}}]$.
2. **Task B (Pre-Flare Activity Forecasting):** Label indicates whether a verified flare onset occurs within future horizon $(t_0, t_0 + H]$ after window reference time $t_0 = w_{\text{end}}$.

```
                     ┌─────────────────────────────┐
                     │ Stage 8: Feature Windows    │
                     │ (window_index, features)    │
                     └──────────────┬──────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │ Gate G3 / G6 Policy Guards  │
                     │ (Labelling & Forecasting)   │
                     └──────────────┬──────────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 ▼                                     ▼
   ┌───────────────────────────┐         ┌───────────────────────────┐
   │ Task A: Detection Export  │         │ Task B: Prediction Export │
   │ (exp_det_<hash>/)         │         │ (exp_pred_<hash>/)        │
   │ - X_features.csv          │         │ - X_features.csv          │
   │ - y_labels.csv            │         │ - y_labels.csv            │
   │ - metadata.csv            │         │ - metadata.csv            │
   │ - exclusions.csv          │         │ - exclusions.csv          │
   │ - config_snapshot.yaml    │         │ - config_snapshot.yaml    │
   │ - data_dictionary.md      │         │ - data_dictionary.md      │
   └───────────────────────────┘         └───────────────────────────┘
```

---

## 2. Strict Task Separation

Detection and prediction targets **never share directories, tables, or records**:
- Detection datasets are exported strictly to: `data/processed/datasets/detection/<export_id>/`
- Prediction datasets are exported strictly to: `data/processed/datasets/prediction/<export_id>/`

Cross-directory mixing triggers an immediate `DatasetExportError`.

---

## 3. Segregated File Structure

Each dataset export directory contains six standardized files:

| File Name | Schema / Description | Prohibited Contents |
|-----------|----------------------|---------------------|
| `X_features.csv` | Pure numeric feature matrix. One row per window, strictly containing mathematical features ($f_1, \dots, f_M$). | **STRICTLY PROHIBITED:** `window_id`, timestamps, file stems, labels, targets, or quality flags. |
| `y_labels.csv` | Primary key `window_id`, target `label` (Int8: `1`, `0`, `<NA>`), and `label_reason`. | Any feature column. |
| `metadata.csv` | Full provenance tracking: `window_id`, `file_stem`, `segment_id`, `window_start`, `window_end`, `coverage_fraction`, `quality_flag`, matched `event_id` or `next_onset_time`. | Target labels or training features. |
| `exclusions.csv` | Auditable ledger of every window where `label` is `<NA>`, including the exact exclusion reason and window coordinates. | Rows with finite labels (`0` or `1`). |
| `config_snapshot.yaml` | Machine-readable dump of all configuration parameters, Gate G3/G5/G6 decision statuses, input file hashes, and event counts. | Unverified assumptions. |
| `data_dictionary.md` | Human- and machine-readable dictionary generated automatically from feature registries and label schemas, including units and equations. | Informal definitions. |

---

## 4. Target Label Semantics and the Meaning of `<NA>`

### Task A (Detection)
- **`1` (Verified Positive):** A verified flare event overlaps the window by at least the approved tolerance and overlap fraction threshold.
- **`0` (Verified Negative):** The window is completely outside every verified flare event and its surrounding embargo buffer, AND has $\ge 80\%$ sample coverage.
- **`<NA>` (Excluded / Ambiguous):** Windows with partial overlap ($< \text{threshold}$), within event embargo buffers, or with $< 80\%$ sample coverage. Excluded intervals are strictly preserved in `exclusions.csv` and **MUST NEVER be filled with `0`**.

### Task B (Forecasting)
- **`1` (Verified Positive Onset):** A verified flare onset occurs within future forecast horizon $(t_0, t_0 + H]$.
- **`0` (Verified Clean Horizon):** No verified flare onset occurs within $(t_0 - \text{embargo}, t_0 + H]$, and the observation segment covers $\ge 80\%$ of the forecast horizon.
- **`<NA>` (Excluded / Right-Censored):** Windows where a flare is active at $t_0$, an onset occurred during recent embargo, or the observation segment ends before horizon $H$ expires.

> [!CRITICAL]
> **Zero Imputation of Unknowns:**  
> Unknown or unobserved intervals are **NEVER** treated as verified negatives. Setting `<NA> = 0` creates severe false negatives in training data and invalidates scientific conclusions.

---

## 5. Event Sufficiency and Decision D-15

Decision D-15 establishes the minimum number of independent, verified flare events required before machine learning models may be trained for scientific claims.

If the number of independent events in the dataset is below the D-15 threshold:
1. The exporter writes `data/processed/datasets/<task>/<export_id>/INSUFFICIENT.md`.
2. The dataset status is formally registered as **`INSUFFICIENT`**.
3. **Training Permissions:**
   - **Main Experiment Training:** **STRICTLY BLOCKED.**
   - **PILOT Pipeline Verification:** **PERMITTED.** The dataset may be used solely as a PILOT dataset to verify code pipelines, model initialization, and metric calculation syntax.

---

## 6. Reproducibility & Deterministic `export_id`

Every export directory is named deterministically via a content hash of its configuration and policy:
$$\text{export\_id} = \text{exp\_<task>\_} + \text{SHA256}(\text{config\_snapshot} + \text{policy\_text})[:10]$$

This guarantees that re-running the export pipeline with identical parameters and policies produces the exact same dataset identifier, preventing accidental duplication or stale artifacts.
