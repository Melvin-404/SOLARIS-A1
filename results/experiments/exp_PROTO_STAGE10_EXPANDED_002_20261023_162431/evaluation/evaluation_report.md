# SOLARIS-A1 Scientific Evaluation Report (Stage 11)

**Dataset Status:** `APPROVED-main`  
**Protocol ID:** `PROTO_STAGE10_EXPANDED_002`  
**Test Set Lock Hash Verified:** `PASSED`  
**Evaluation Timestamp (UTC):** `2026-10-23T16:27:17.518390+00:00`  
**Task:** `detection`  

> **MANDATORY NOTICE:**  
> This report contains computed values only. Interpretation is the responsibility of the human researcher.

---

## 1. Window-Level Classification Performance (Sealed Test Set)

| Model / Baseline | Prevalence | Precision | Recall | F1 | PR-AUC | ROC-AUC | TP | FP | TN | FN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **logistic_regression** | 0.2002 | 0.5201 | 0.6677 | 0.5847 | 0.6176 | 0.8430 | 2122 | 1958 | 10736 | 1056 |
| **random_forest** | 0.2002 | 0.4812 | 0.7203 | 0.5769 | 0.5530 | 0.8364 | 2289 | 2468 | 10226 | 889 |
| **xgboost** | 0.2002 | 0.3499 | 0.9012 | 0.5041 | 0.6622 | 0.8480 | 2864 | 5321 | 7373 | 314 |
| **baseline_threshold** | 0.2002 | 0.3823 | 0.8228 | 0.5220 | 0.5112 | 0.8012 | 2615 | 4226 | 8468 | 563 |
| **baseline_climatological** | 0.2002 | 0.0000 | 0.0000 | 0.0000 | 0.2002 | 0.5000 | 0 | 0 | 12694 | 3178 |
| **baseline_persistence** | 0.2002 | 0.3478 | 0.8685 | 0.4967 | 0.3284 | 0.7304 | 2760 | 5176 | 7518 | 418 |

## 4. Probability Calibration Assessment

| Model | Brier Score | Expected Calibration Error (ECE) | Max Calibration Error (MCE) |
| :--- | :---: | :---: | :---: |
| **logistic_regression** | 0.1484 | 0.1354 | 0.5145 |
| **random_forest** | 0.1609 | 0.1516 | 0.5186 |
| **xgboost** | 0.2803 | 0.3847 | 0.6115 |

## 5. Statistical Uncertainty (Block Bootstrap)

- **Status:** `CI NOT COMPUTED — insufficient independent blocks (n=4)`
- **Independent Observation Blocks:** 4 (Threshold required: 5)
- **Resamples:** 500
