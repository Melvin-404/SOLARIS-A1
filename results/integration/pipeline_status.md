# SOLARIS-A1 Pipeline Stages Status Report (Stage 13)

| Stage | Stage Name | Status | Gate | Details & Reasons | Artifacts Checked |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **3** | FITS Inventory | **COMPLETE** | `G0` | Inventory and FITS metadata inspected and confirmed. | `inventory.csv`<br>`inventory.json`<br>`inspection_report.md` |
| **4** | Data Quality | **COMPLETE** | `G1/G2` | Data quality characterisation complete. | `summary.csv`<br>`AWAITING_G1.md` |
| **5** | Exploratory Analysis | **COMPLETE** | `G3-pre` | EDA variability metrics and candidate burst intervals computed (all candidates UNVERIFIED). | `candidate_bursts.csv`<br>`variability_summary.csv` |
| **6** | Labelling Protocol | **BLOCKED** | `G3` | Labelling policy status is DRAFT. Gate G3 human approval is required before supervised labelling. | `08_labelling_policy.md` |
| **7** | Preprocessing & Segmentation | **PROVISIONAL** | `G4` | Segmentation complete in PROVISIONAL mode (Gate G4 approval pending). | `summary.csv`<br>`AWAITING_G4.md` |
| **8** | Feature Engineering | **PROVISIONAL** | `G5` | Sliding windows and causal features generated in PROVISIONAL mode (Gate G5 approval pending). | `window_index.csv`<br>`window_features.csv`<br>`build_log.json` |
| **9** | Dataset Export | **BLOCKED** | `G3/G6` | Dataset export is strictly BLOCKED pending Gate G3 (labelling policy) and Gate G6 (forecasting policy). | `BLOCKED_DETECTION.md`<br>`BLOCKED_PREDICTION.md`<br>`export_log.json` |
| **10** | Model Training | **BLOCKED** | `G7` | Model training is strictly BLOCKED pending Gate G7 (training protocol freeze). | `AWAITING_G7.md`<br>`training_protocol.yaml` |
| **11** | Scientific Evaluation | **BLOCKED** | `G8` | Single-shot test evaluation is strictly BLOCKED pending Gate G8 human researcher approval. | `AWAITING_G8.md` |
