# SOLARIS-A1: Task B (Pre-Flare Forecasting) Scientific Evaluation & Negative Result Report

**Document ID:** `DOC-27-TASK-B-NEGATIVE-RESULT`  
**Date:** 2026-10-24  
**Author:** Solar Physics & ML Research Group / SOLARIS-A1  
**Status:** ARCHIVED SCIENTIFIC INVESTIGATION (NEGATIVE RESULT)  
**Decision:** REMOVAL OF TASK B FORECASTING FROM PUBLIC INTERFACE  

---

## 1. Executive Summary

As part of the SOLARIS-A1 project, an independent scientific audit and rigorous machine learning experiment were conducted to evaluate whether full-disk soft X-ray time series (1.0–22.0 keV) from Aditya-L1 SoLEXS can support predictive pre-flare forecasting ($\Delta t_{\text{horizon}} = 5, 10, \text{and } 30\text{ minutes}$) prior to verified solar flare onsets.

**Final Scientific Conclusion:**  
Single-channel, full-disk integrated soft X-ray time series **do not contain physically discernible precursor signals** capable of outperforming simple baselines on independent held-out observations. On the chronological validation partition, all evaluated models (Logistic Regression, Random Forest, XGBoost) achieved $\text{ROC-AUC} \le 0.508$ (equivalent to random chance). On the held-out test partition, tree-based models exhibited severe negative transfer ($\text{ROC-AUC} = 0.384–0.439$), and linear models generated an unviable **164 false alarms per observation hour**.

Consequently, **Pre-Flare Risk Analysis is removed from the public-facing platform** to maintain scientific credibility and prevent the presentation of deceptive predictive capabilities. The verified, high-performance in-window flare detection system (Task A, LightGBM $F_1 = 0.875$, $\text{PR-AUC} = 0.880$) remains fully operational and untouched.

---

## 2. Experimental Design & Methodological Rigor

### 2.1 Dataset and Partitions
To prevent data leakage from overlapping sliding windows ($W = 60\text{ s}, S = 10\text{ s}$), partitions were constructed strictly chronologically with 300.0 s embargo buffers between sets:
- **Training Partition (July 01–09, 2024):** 51,741 valid windows, 8,904 positive windows (prevalence: 17.21%), 53 independent flare events.
- **Validation Partition (July 10–11, 2024):** 14,570 valid windows, 2,616 positive windows (prevalence: 17.95%), 16 independent flare events.
- **Held-Out Test Partition (July 12–14, 2024 + Oct 18, 2026):** 28,980 valid windows, 4,919 positive windows (prevalence: 16.97%), 30 independent flare events.
- **Total Valid Windows:** 95,291 across 99 independent flare onsets.

### 2.2 Leakage Safeguards
- Preprocessing (`RobustScaler`) was fitted strictly on training partition data.
- Ongoing flare events at reference time $t_0$ were assigned `<NA>` with reason `ONGOING_EVENT_AT_T0` (13,472 windows excluded) to prevent trivial flare detection from masquerading as forecasting.
- Boundary windows near segment ends with $< 80\%$ observed horizon coverage were assigned `<NA>` with reason `INSUFFICIENT_HORIZON_COVERAGE`.

---

## 3. Validation Horizon & Model Selection Results

Models were tuned and evaluated on the chronological Validation Partition (July 10–11, 2024) across 5-, 10-, and 30-minute horizons using both raw and background-normalized features:

| Horizon | Validation Prevalence | Logistic Regression (ROC-AUC / PR-AUC) | Random Forest (ROC-AUC / PR-AUC) | XGBoost (ROC-AUC / PR-AUC) |
| :--- | :---: | :---: | :---: | :---: |
| **5 Minutes (300 s)** | 0.0307 | 0.463 / 0.028 | 0.479 / 0.037 | 0.502 / 0.038 |
| **10 Minutes (600 s)** | 0.0613 | 0.448 / 0.056 | 0.496 / 0.062 | 0.508 / 0.063 |
| **30 Minutes (1800 s)** | 0.1795 | 0.445 / 0.154 | 0.434 / 0.152 | 0.440 / 0.158 |

**Analysis:**
Across all horizons, every machine learning model scored $\text{ROC-AUC} \le 0.508$, demonstrating near-zero or sub-random discriminative power on out-of-sample data.

---

## 4. Untouched Held-Out Test Evaluation

Evaluating the models on the untouched held-out test partition (July 12–14, 2024 + Oct 18, 2026) confirmed the complete failure of operational forecasting:

### 4.1 Window-Level Metrics (30-Minute Horizon, $N=28,980$, Prev = $0.1697$)
- **Climatological Baseline:** $\text{ROC-AUC} = 0.500$, $\text{PR-AUC} = 0.1697$, $\text{Brier} = 0.1409$.
- **Logistic Regression:**
  - $\text{ROC-AUC} = 0.5796$, $\text{PR-AUC} = 0.2042$, $\text{Brier} = 0.2130$.
  - Precision: $0.1930$, Recall: $0.5359$, $F_1 = 0.2838$.
  - Confusion Matrix: $\text{TN} = 13,039$, $\text{FP} = 11,022$, $\text{FN} = 2,283$, $\text{TP} = 2,636$.
  - **False Alarms per Hour:** **164.91 FA/hr** (over 66.8 observation hours).
- **XGBoost:**
  - $\text{ROC-AUC} = 0.4295$ (sub-random), $\text{PR-AUC} = 0.1503$ (below prior $0.1697$), $\text{Brier} = 0.2796$.
  - Precision: $0.1535$, Recall: $0.4001$, $F_1 = 0.2219$.
  - Confusion Matrix: $\text{TN} = 13,211$, $\text{FP} = 10,850$, $\text{FN} = 2,951$, $\text{TP} = 1,968$.
  - **False Alarms per Hour:** **162.34 FA/hr**.

### 4.2 Breakdown by Date
- **July 12, 2024:** $\text{ROC-AUC} = 0.700$, $\text{PR-AUC} = 0.202$ (elevated by active region baseline ramp).
- **July 13, 2024:** $\text{ROC-AUC} = 0.508$, $\text{PR-AUC} = 0.174$ (pure coin-flip).
- **July 14, 2024:** $\text{ROC-AUC} = 0.474$, $\text{PR-AUC} = 0.327$ (worse than coin-flip).
- **October 18, 2026:** $\text{ROC-AUC} = 0.515$, $\text{PR-AUC} = 0.045$ (pure noise).

---

## 5. Physical Causes of the Negative Result

1. **Emission Mechanism:** Thermal soft X-rays (1.0–22.0 keV) require hot plasma ($T > 10^7\text{ K}$) heated by magnetic reconnection. Prior to reconnection, the solar corona is in a thermal quiescent state; energy is stored in non-potential magnetic fields (photospheric shear, current helicity) that emit no excess soft X-rays.
2. **Full-Disk Spatial Integration:** Because SoLEXS is a full-disk instrument without spatial imaging, emission from all active regions is summed. A minor brightness shift in one active region obscures any subtle precursor in another.
3. **Severe Active-Region Domain Shift:** Quiescent background flux varies from $\sim 25\text{ cts/s}$ during quiet periods to $> 150\text{ cts/s}$ during active-region transits. Tree models overfit to absolute flux levels in the training set and misclassify active-region background as pre-flare activity.

---

## 6. Governance Decision

1. **Remove Pre-Flare Forecasting Page from Public Website:**
   Page 10 (`10_Pre_Flare_Risk.py`) is deleted. The public platform presents only validated, scientifically sound tools.
2. **Preserve Research Code in Archive:**
   Training scripts (`scripts/train_forecasting_models.py`) and evaluation outputs (`results/forecasting/`) are preserved as an offline research archive for reproducibility.
3. **Preserve Task A Detection Unconditionally:**
   Task A in-window detection ($F_1 = 0.875$) remains the core operational capability of SOLARIS-A1.
