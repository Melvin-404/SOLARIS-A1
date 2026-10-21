# Feature Dictionary: SOLARIS-A1 (Stage 8)

**Project:** `SOLARIS-A1` (Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations)  
**Stage:** Stage 8 — Sliding Windows and Feature Engineering  
**Status:** PROVISIONAL (Development Mode) — Requires Gate G5 Human Approval for Final Model Training  

---

> [!WARNING]
> ### CRITICAL METHODOLOGICAL WARNING: ROW-LEVEL SPLITTING LEAKS INFORMATION
> In Stage 8, sliding windows are extracted with a 60-second window length ($W = 60\text{ s}$) and a 10-second stride ($S = 10\text{ s}$).
> Consecutive sliding windows share **83.3% of their temporal samples** ($50\text{ s} / 60\text{ s}$ overlap).
> 
> **Any random row-level train/validation/test split will catastrophically leak information across splits**, yielding artificially near-perfect test scores that fail on real data.
> - Data must **NEVER** be partitioned using standard randomized shuffling (e.g., `train_test_split(shuffle=True)`).
> - Partitioning in Stage 10 must be strictly block-temporal: whole active days or widely separated continuous segments separated by an embargo buffer.

---

## 1. Feature Library Overview

The SOLARIS-A1 causal feature library extracts 18 summary statistics from each 60-second observation window $[w_{\text{start}}, w_{\text{end}}]$. Every calculation uses strictly past-or-present samples where $t_i \le w_{\text{end}}$ ($t_{\text{ref}} = t_0$).

All non-finite samples (`NaN`, `±Inf`) are excluded prior to calculation and counted; **NaN is never filled, estimated, or interpolated**.

---

## 2. Feature Specifications

| Feature Name | Description | Mathematical Formula | Units | Required Inputs | Edge Cases & Reason Codes | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`mean`** | Arithmetic mean flux | $\frac{1}{N}\sum_{i=1}^N x_i$ | Counts | Counts | Returns `NaN` (`ZERO_SAMPLES`) if $N=0$. | PROVISIONAL |
| **`median`** | Median count rate | 50th percentile of $\{x_i\}$ | Counts | Counts | Returns `NaN` (`ZERO_SAMPLES`) if $N=0$. | PROVISIONAL |
| **`std`** | Sample standard deviation | $\sqrt{\frac{1}{N-1}\sum_{i=1}^N (x_i - \bar{x})^2}$ | Counts | Counts | Returns `0.0` if all values equal; `NaN` (`INSUFFICIENT_SAMPLES`) if $N<2$. | PROVISIONAL |
| **`robust_variability`** | Normalized MAD | $1.4826 \times \text{median}(\|x_i - \text{median}(x)\|)$ | Counts | Counts | Outlier-resistant dispersion. Returns `0.0` if identical; `NaN` if $N=0$. | PROVISIONAL |
| **`min`** | Minimum flux | $\min(x_i)$ | Counts | Counts | Returns `NaN` (`ZERO_SAMPLES`) if $N=0$. | PROVISIONAL |
| **`max`** | Peak flux | $\max(x_i)$ | Counts | Counts | Returns `NaN` (`ZERO_SAMPLES`) if $N=0$. | PROVISIONAL |
| **`p05`** | 5th percentile | 5th empirical percentile | Counts | Counts | Returns `NaN` (`ZERO_SAMPLES`) if $N=0$. | PROVISIONAL |
| **`p25`** | 25th percentile (Q1) | 25th empirical percentile | Counts | Counts | Returns `NaN` (`ZERO_SAMPLES`) if $N=0$. | PROVISIONAL |
| **`p75`** | 75th percentile (Q3) | 75th empirical percentile | Counts | Counts | Returns `NaN` (`ZERO_SAMPLES`) if $N=0$. | PROVISIONAL |
| **`p95`** | 95th percentile | 95th empirical percentile | Counts | Counts | Returns `NaN` (`ZERO_SAMPLES`) if $N=0$. | PROVISIONAL |
| **`iqr`** | Interquartile range | $p_{75} - p_{25}$ | Counts | Counts | Spread of core distribution. Returns `NaN` if $N=0$. | PROVISIONAL |
| **`mean_abs_first_difference`** | Mean step variability | $\frac{1}{N-1}\sum_{i=1}^{N-1} \|x_{i+1} - x_i\|$ | Counts / step | Counts | Average high-frequency jitter. Returns `NaN` (`INSUFFICIENT_SAMPLES`) if $N<2$. | PROVISIONAL |
| **`max_abs_first_difference`** | Maximum step jump | $\max_{i=1..N-1} \|x_{i+1} - x_i\|$ | Counts / step | Counts | Detects impulsive count jumps. Returns `NaN` if $N<2$. | PROVISIONAL |
| **`temporal_slope`** | Least-squares linear slope | $\frac{\text{Cov}(x, t)}{\text{Var}(t)}$ | Counts / s | Counts, Time | Quantifies flux rise or decay rate across window. Returns `NaN` (`INSUFFICIENT_SAMPLES`) if $N<3$ or $\Delta t=0$. | PROVISIONAL |
| **`rolling_trend`** | Trailing sub-window slope | Slope over samples with $t_i \ge w_{\text{end}} - K$ | Counts / s | Counts, Time, $K=15\text{ s}$ | Measures immediate gradient at window boundary $t_0$. Returns `NaN` (`INSUFFICIENT_TAIL_SAMPLES`) if $N_{\text{tail}}<3$. | PENDING (D-19) |
| **`peak_to_baseline_ratio`** | Peak-to-quiescent flux ratio | $\frac{\max(x_i)}{\text{baseline}}$ | Dimensionless | Counts, Causal Baseline | Relative flare enhancement above local background. Returns `NaN` (`BASELINE_NONPOSITIVE`) if baseline $\le 10^{-6}$; `NaN` (`BASELINE_UNAVAILABLE`) if baseline missing. | PENDING (D-18) |
| **`coverage_fraction`** | Observed sample fraction | $\frac{N_{\text{observed}}}{N_{\text{expected}}}$ | Ratio $[0, 1]$ | Counts | Measures telemetry completeness in window ($N_{\text{exp}}=60$ at 1 s cadence). | PROVISIONAL |
| **`n_observed_samples`** | Observed sample count | Count of finite samples | Integer | Counts | Raw integer sample count. | PROVISIONAL |

---

## 3. Causal Baseline Flux Methodology

The `peak_to_baseline_ratio` feature requires a local background reference.
To preserve temporal causality:
1. **Pre-Window Lookback:** The baseline is calculated from observations in:
   $$t \in [w_{\text{start}} - \text{lookback\_seconds}, w_{\text{start}})$$
   strictly preceding the window start ($t < w_{\text{start}}$).
2. **Segment Isolation:** The lookback interval is confined to the same continuous segment; it never spans past gaps or day boundaries.
3. **Robust Median:** Computed as the median of all finite samples in the lookback window.
4. **Minimum Sample Floor:** If fewer than 30 valid samples exist in the lookback interval, returns `NaN` with code `BASELINE_INSUFFICIENT`.
5. **Acausality Prevention:** Global, diurnal, or whole-file baselines are strictly prohibited as they leak future solar activity into pre-flare intervals.
