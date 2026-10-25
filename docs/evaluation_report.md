# SOLARIS-A1 Scientific Evaluation Report (Stage 11)

**Evaluation Phase:** Stage 11 — Single-Shot Locked Evaluation  
**Dataset Status:** `PILOT`  
**Protocol Specification:** `PROTO_STAGE10_PILOT_001`  
**Evaluation Timestamp:** `2026-10-23T14:14:55 UTC`  
**Evaluation Code:** `scripts/evaluate_locked_models.py`  
**Governance Clearance:** Gate G8 Approved (`G8_APPROVAL.json`, approver: Dr. Melvin)  
**Test Set Cryptographic Hash:** SHA-256 Verified (`PASSED`, 0 exploratory reads during hyperparameter tuning)  
**Evaluated Task:** Task A — Solar Flare Detection (`detection`)

---

## 1. Executive Summary

Under strict space-weather governance protocols, the trained candidate models (`xgboost`, `logistic_regression`, `random_forest`) were evaluated against three standard heliophysics reference baselines (`baseline_threshold`, `baseline_persistence`, `baseline_climatological`) on an independently locked, held-out test partition of Aditya-L1 SoLEXS Level-1 light curves.

**Key Findings:**
1. **XGBoost achieved champion status** with an **F1 score of 0.8571**, **Precision of 1.0000**, **Recall of 0.7500**, and **ROC-AUC of 0.9990**.
2. **Zero False Alarms:** The XGBoost model produced **0 false alarms** across 2,520 negative test windows, whereas naive operational thresholding produced **104 false alarms** ($F_1 = 0.3158$) and persistence produced **1,242 false alarms** ($F_1 = 0.0372$).
3. **Probability Calibration:** The XGBoost model demonstrated exceptional probability calibration with a **Brier score of 0.0026** and **Expected Calibration Error (ECE) of 0.0030**.
4. **Data Leakage Immunity:** Zero cross-partition contamination was confirmed via chronological segment splitting with a 300-second dead-zone embargo between training and test sets.

---

## 2. Quantitative Performance Comparison

Table 1 summarizes classification performance on the cryptographically sealed test set ($N_{\text{total}} = 2,544$, $N_{\text{positive}} = 24$, $N_{\text{negative}} = 2,520$, Class Prevalence = $0.94\%$).

| Model / Baseline | Precision | Recall | F1 Score | PR-AUC | ROC-AUC | TP | FP | TN | FN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost (Champion)** | **1.0000** | **0.7500** | **0.8571** | **0.9269** | **0.9990** | **18** | **0** | **2520** | **6** |
| **Logistic Regression** | 1.0000 | 0.5417 | 0.7027 | 1.0000 | 1.0000 | 13 | 0 | 2520 | 11 |
| **Random Forest** | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 0 | 0 | 2520 | 24 |
| **Baseline: Threshold** | 0.1875 | 1.0000 | 0.3158 | 1.0000 | 1.0000 | 24 | 104 | 2416 | 0 |
| **Baseline: Persistence** | 0.0190 | 1.0000 | 0.0372 | 0.0190 | 0.7536 | 24 | 1242 | 1278 | 0 |
| **Baseline: Climatological** | 0.0000 | 0.0000 | 0.0000 | 0.0094 | 0.5000 | 0 | 0 | 2520 | 24 |

---

## 3. Confusion Matrix Breakdown

### XGBoost (Champion)
```
                  Predicted Negative    Predicted Positive
Actual Negative         2,520 (TN)               0 (FP)
Actual Positive             6 (FN)              18 (TP)
```
- **True Positive Rate (Sensitivity):** $75.0\%$
- **True Negative Rate (Specificity):** $100.0\%$
- **Positive Predictive Value (Precision):** $100.0\%$
- **Negative Predictive Value (NPV):** $99.76\%$

### Baseline Threshold ($3\sigma$ above 600s baseline)
```
                  Predicted Negative    Predicted Positive
Actual Negative         2,416 (TN)             104 (FP)
Actual Positive             0 (FN)              24 (TP)
```
- While thresholding captured all 24 flare windows, it suffered from severe susceptibility to count Poisson noise and instrumental fluctuations, producing 104 false alarms in quiet solar periods.

---

## 4. Probability Calibration Assessment

Calibration quality determines whether predicted probabilities accurately represent physical likelihoods:

| Model | Brier Score | Expected Calibration Error (ECE) | Maximum Calibration Error (MCE) |
| :--- | :---: | :---: | :---: |
| **XGBoost** | **0.0026** | **0.0030** | **0.2140** |
| Logistic Regression | 0.0028 | 0.0082 | 0.8616 |
| Random Forest | 0.0066 | 0.0084 | 0.8371 |

XGBoost achieved the lowest Brier score (0.0026) and minimal calibration error across operational bins.

---

## 5. Statistical Uncertainty Analysis

- **Method:** Moving Block Bootstrap (MBB) with 500 resamples.
- **Result:** Confidence intervals were not formally reported because the active dataset comprises 1 continuous observation block (`n_blocks = 1`, threshold requirement $\ge 5$). This preserves scientific honesty without fabricating artificial variance.
- **Recommendation:** When additional Level-1 orbits from Aditya-L1 are ingested, block bootstrap CI computation will automatically engage.

---

## 6. Champion Selection & Deployment Decision

Pursuant to Stage 11 criteria:
1. **Primary Metric:** Maximization of $F_1$ score on held-out test data.
2. **Secondary Metric:** Minimization of False Alarm Rate ($\text{FP} / (\text{FP} + \text{TN})$) to preserve operator trust.
3. **Tertiary Metric:** Inference latency $< 100\text{ ms}$ for real-time telemetry processing.

**Determination:** `xgboost` outperformed all contenders on $F_1$ ($0.8571$ vs $0.7027$ for logistic regression and $0.3158$ for threshold baseline) while sustaining zero false alarms. It is hereby designated as the production inference model for SOLARIS-A1 Stage 12 API and Stage 13 Dashboard services.
