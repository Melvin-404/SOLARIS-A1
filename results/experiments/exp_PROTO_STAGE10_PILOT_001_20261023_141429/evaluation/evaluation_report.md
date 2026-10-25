# SOLARIS-A1 Scientific Evaluation Report (Stage 11)

**Dataset Status:** `PILOT`  
**Protocol ID:** `PROTO_STAGE10_PILOT_001`  
**Test Set Lock Hash Verified:** `PASSED`  
**Evaluation Timestamp (UTC):** `2026-10-23T14:14:55.605456+00:00`  
**Task:** `detection`  

> **MANDATORY NOTICE:**  
> This report contains computed values only. Interpretation is the responsibility of the human researcher.

---

## 1. Window-Level Classification Performance (Sealed Test Set)

| Model / Baseline | Prevalence | Precision | Recall | F1 | PR-AUC | ROC-AUC | TP | FP | TN | FN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **logistic_regression** | 0.0094 | 1.0000 | 0.5417 | 0.7027 | 1.0000 | 1.0000 | 13 | 0 | 2520 | 11 |
| **random_forest** | 0.0094 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 0 | 0 | 2520 | 24 |
| **xgboost** | 0.0094 | 1.0000 | 0.7500 | 0.8571 | 0.9269 | 0.9990 | 18 | 0 | 2520 | 6 |
| **baseline_threshold** | 0.0094 | 0.1875 | 1.0000 | 0.3158 | 1.0000 | 1.0000 | 24 | 104 | 2416 | 0 |
| **baseline_climatological** | 0.0094 | 0.0000 | 0.0000 | 0.0000 | 0.0094 | 0.5000 | 0 | 0 | 2520 | 24 |
| **baseline_persistence** | 0.0094 | 0.0190 | 1.0000 | 0.0372 | 0.0190 | 0.7536 | 24 | 1242 | 1278 | 0 |

## 4. Probability Calibration Assessment

| Model | Brier Score | Expected Calibration Error (ECE) | Max Calibration Error (MCE) |
| :--- | :---: | :---: | :---: |
| **logistic_regression** | 0.0028 | 0.0082 | 0.8616 |
| **random_forest** | 0.0066 | 0.0084 | 0.8371 |
| **xgboost** | 0.0026 | 0.0030 | 0.2140 |

## 5. Statistical Uncertainty (Block Bootstrap)

- **Status:** `CI NOT COMPUTED — insufficient independent blocks (n=1)`
- **Independent Observation Blocks:** 1 (Threshold required: 5)
- **Resamples:** 500
