# Sliding Window Methodology and Reference-Time Anchoring (Stage 8)

**Project:** `SOLARIS-A1` (Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations)  
**Stage:** Stage 8 — Sliding Windows and Feature Engineering  
**Status:** PROVISIONAL (Development Mode) — Requires Gate G5 Human Approval  

---

## 1. Sliding Window Geometry & Mathematical Formulation

Sliding windows are extracted strictly within continuous, gap-free observation segments produced in Stage 7.
Given a continuous segment with physical start time $T_{\text{start}}$, end time $T_{\text{end}}$, and duration $D = T_{\text{end}} - T_{\text{start}}$:

For each window index $i = 0, 1, 2, \dots, N_{\text{windows}} - 1$:
$$w_{\text{start}}(i) = T_{\text{start}} + i \times S$$
$$w_{\text{end}}(i) = w_{\text{start}}(i) + W$$

Where:
- $W$: Window length in seconds ($W = 60.0\text{ s}$, Decision D-05).
- $S$: Window stride in seconds ($S = 10.0\text{ s}$, Decision D-06).

### Closed Segment Constraint
Windows are restricted strictly to the segment interior:
$$w_{\text{end}}(i) \le T_{\text{end}}$$

The total number of valid windows that can be fitted within a segment of duration $D$ is given by:
$$N_{\text{windows}} = \left\lfloor \frac{D - W}{S} \right\rfloor + 1$$

If $D < W$, the segment is insufficient for even a single window, and exactly zero windows are produced with a logged reason. **No partial windows extending past segment boundaries or across telemetry gaps are created.**

---

## 2. Reference Time Convention ($t_{\text{ref}} = t_0 = w_{\text{end}}$)

In real-time space weather monitoring and operational forecasting, decisions are made at the **current observation epoch**.
Therefore, for every window $i$:
$$\text{Reference Time } t_{\text{ref}} \equiv t_0 = w_{\text{end}}(i)$$

### Implications for Scientific Tasks:
1. **Task A (Current-Window Solar Flare Detection):**
   - The classifier evaluates whether solar flare activity occurred during the window $[t_0 - W, t_0]$.
   - All extracted features describe physical behavior up to the decision epoch $t_0$.
2. **Task B (Pre-Flare Prediction / Forecasting):**
   - The forecast predicts whether a flare onset will occur in the future horizon:
     $$t_{\text{flare}} \in (t_0, t_0 + \Delta t_{\text{horizon}}]$$
   - All features are anchored at $t_0$. Causality requires that no sample with $t > t_0$ is accessed, preventing temporal leakage from the target flare onset.

---

## 3. Sample Coverage and Quality Qualification

For a nominal detector cadence $\Delta t_{\text{cadence}} = 1.0\text{ s}$, the expected number of samples in a window of duration $W$ is:
$$N_{\text{expected}} = \left\lfloor \frac{W}{\Delta t_{\text{cadence}}} \right\rceil$$

The sample coverage fraction is defined as:
$$\text{Coverage Fraction } C = \frac{N_{\text{observed}}}{N_{\text{expected}}}$$

### Quality Flagging:
- If $C \ge C_{\text{min}}$ (Decision D-20, default $0.80$): `quality_flag = "OK"`, `include_flag = True`.
- If $C < C_{\text{min}}$: `quality_flag = "LOW_COVERAGE"`.
- **Zero Silent Dropping:** Low-coverage windows are never silently discarded. They are preserved in `window_index.csv` and `window_features.csv` with `quality_flag = "LOW_COVERAGE"` and an explicit `include_flag` (configurable via `include_low_coverage: true`). Downstream models in Stage 10 may filter or retain them based on experimental design.

---

## 4. Overlap, Autocorrelation, and Effective Sample Size

With $W = 60\text{ s}$ and $S = 10\text{ s}$, adjacent windows share $50\text{ s}$ of data:
$$\text{Temporal Overlap Fraction} = \frac{W - S}{W} = \frac{50}{60} = 83.33\%$$

### Statistical Considerations:
1. **High Autocorrelation:** Consecutive feature vectors are strongly correlated.
2. **Effective Sample Size ($N_{\text{eff}}$):** The number of independent degrees of freedom is approximately:
   $$N_{\text{eff}} \approx \frac{D_{\text{total}}}{W}$$
   For an 8-hour continuous segment, $N_{\text{windows}} \approx 2,875$, but $N_{\text{eff}} \approx 480$.
3. **Partitioning Integrity:** As warned in [`docs/11_feature_dictionary.md`](11_feature_dictionary.md), standard randomized train/test splitting across overlapping windows is scientifically invalid. Splitting must occur across non-overlapping days or block-separated segments.
