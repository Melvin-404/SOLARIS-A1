# SOLARIS-A1: Exploratory Data Analysis Methods (Stage 5)

## Overview

Stage 5 of `SOLARIS-A1` (*Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations*) implements reproducible exploratory data analysis (EDA) across available SoLEXS Level-1 light-curve and GTI products.

---

## Methodological Principles and Non-Labeling Guarantee

1. **Exploratory Status:** Every candidate interval identified by statistical threshold crossing is strictly designated:
   $$\text{Status} = \text{"CANDIDATE — UNVERIFIED"}$$
2. **Zero Labeling Guarantee:** Nothing produced in this stage is a flare label, ground truth, or ML target. No candidate interval may be used for supervised model training.
3. **Event Comparison Policy:** Because verified independent solar flare event catalogs (e.g. NOAA/GOES or PRADAN official event lists) have not yet been approved, event comparison returns strictly:
   $$\text{"NOT PERFORMED — no independent event records supplied"}$$

---

## Mathematical and Statistical Formulations

### 1. Robust Time-Based Running Baseline
To evaluate localized transient activity against the diurnal or slowly evolving solar quiescent emission, a running median baseline $B(t)$ is computed over a physical time window $W_{\text{baseline}} = 600\text{ s}$ (marked `PROVISIONAL` in `config/default.yaml`):

$$B(t_i) = \text{median}\left(\left\{x_j : |t_j - t_i| \le \frac{W_{\text{baseline}}}{2},\, x_j \text{ is finite}\right\}\right)$$

**Edge Handling:**
- For sample points near the beginning of observation where $t_i - W/2 < t_{\text{start}}$, the window is truncated to $[t_{\text{start}}, t_i + W/2]$.
- For sample points near the end where $t_i + W/2 > t_{\text{end}}$, the window is truncated to $[t_i - W/2, t_{\text{end}}]$.
- If an entire window contains zero finite samples (such as during an extended telemetry gap), the global series median is assigned.

### 2. Candidate Transient Burst Intervals
Residual variations above baseline $\Delta_i = x_i - B(t_i)$ are evaluated using robust Median Absolute Deviation (MAD) dispersion:
$$\text{MAD} = \text{median}\left(|\Delta_i - \text{median}(\Delta)|\right)$$
$$\sigma_{\text{robust}} = 1.4826 \times \text{MAD}$$

The detection threshold is defined by:
$$T(t_i) = B(t_i) + k \cdot \sigma_{\text{robust}} \quad (k = 5.0)$$

Contiguous intervals where $x_i > T(t_i)$ exceeding a minimum physical duration $D_{\text{min}} = 10.0\text{ s}$ are catalogued as candidate transient bursts with:
- Start and end timestamps ($t_{\text{start}}, t_{\text{end}}$)
- Interval duration ($\Delta t$)
- Peak time and peak value ($t_{\text{peak}}, x_{\text{peak}}$)
- Peak-to-baseline ratio ($x_{\text{peak}} / B(t_{\text{peak}})$)
- Mandatory status: `CANDIDATE — UNVERIFIED`

### 3. Light-Curve Variability Statistics
- **Coefficient of Variation ($CV$):** $\sigma / \mu$
- **MAD Dispersion:** $1.4826 \times \text{MAD}$
- **Interquartile Range ($IQR$):** $Q_{75} - Q_{25}$
- **Fisher-Pearson Skewness:** $g_1$
- **Excess Kurtosis:** $g_2$

---

## Limitations and Operational Bounds
- **Single Calendar Day:** All analysis is derived from observation date `2026-10-18`.
- **Provisional Thresholds:** Parameters ($W_{\text{baseline}} = 600\text{ s}$, $k = 5.0$, $D_{\text{min}} = 10\text{ s}$) are provisional exploratory defaults subject to researcher review at Gate G2.
- **Instrumental vs Physical Ambiguity:** Statistically anomalous spikes and bursts may represent genuine quiet-Sun micro-activity, particle precipitation events, or detector noise. Verification requires multi-instrument cross-referencing in Stage 6.
