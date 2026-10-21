# SOLARIS-A1 Evaluation Methodology and Governance (Stage 11)

**Document ID:** `DOC-15-EVALUATION-METHODS`  
**Task Applicability:** Task A (Solar Flare Detection) & Task B (Pre-Flare Prediction)  
**Governance Status:** Standardized Scientific Methodology  

---

## 1. Executive Summary

Evaluation in solar flare machine learning must confront extreme class imbalance, temporal autocorrelation across overlapping time series windows, and the divergence between instantaneous window predictions and macro physical solar events.

This document establishes the scientific principles, mathematical formulations, and governance rules codified in Stage 11 of SOLARIS-A1:
1. **Window-Level vs. Event-Level Duality**: Why window classification metrics and event detection rates answer fundamentally different questions.
2. **Prevalence Transparency and PR-AUC**: Why accuracy and ROC-AUC can be misleading under extreme rarity.
3. **Overlapping Windows & Effective Sample Size**: Why adjacent windows violate independence and how embargo buffers mitigate leakage.
4. **False Alarms Normalized by Covered Science Time**: Why wall-clock duration must never be used to normalize false alarm rates.
5. **Probability Calibration Assessment**: Reliability diagrams, Brier score, and expected calibration error without artificial post-hoc manipulation.
6. **Block Bootstrap Uncertainty**: Resampling continuous observation segments rather than individual rows.
7. **The Inviolable Single-Shot Evaluation Rule**: Why test set evaluation occurs exactly once under cryptographic seal.

---

## 2. Window-Level vs. Event-Level Evaluation

In sliding-window solar flare analysis, the model produces predictions on discrete temporal intervals (e.g., $W = 60\text{ s}$ with stride $S = 10\text{ s}$). However, astronomers and space weather forecasters evaluate flare detections at the level of distinct physical eruption events.

| Property | Window-Level Classification | Event-Level Macro Detection |
| :--- | :--- | :--- |
| **Fundamental Unit** | Discrete temporal window $W_i = [t_i - W, t_i]$ | Full physical flare event $E_j = [T_{\text{start}}, T_{\text{end}}]$ |
| **Sample Size** | Tens of thousands of overlapping windows | Small integer count of physical events (e.g. 1 to 5 per observation day) |
| **Target Question** | "Is a solar flare actively occurring in this 60 s window?" | "Did the detection system successfully alert scientists to this eruption?" |
| **Positive Instance** | Positive window sample ($y_i = 1$) | An independently verified physical flare event |
| **Negative Instance** | Verified quiet/background window ($y_i = 0$) | Observation periods devoid of solar flare activity |
| **Primary Risk** | High window recall can mask fragmented, erratic event alerting | High event recall can mask thousands of consecutive false alarm windows |

### Event Clustering & Window Merging
To transition from window predictions to event detections, adjacent positive windows separated by a gap less than or equal to `merge_gap_seconds` (e.g., $60\text{ s}$) are clustered into candidate event episodes:
$$\text{Interval}_k = [t_{\text{start}}, t_{\text{end}}]$$
- An event $E_j$ is deemed **detected** if any candidate episode overlaps the interval $[T_{\text{start}}, T_{\text{end}}]$.
- Candidate episodes that do not overlap any verified reference event are recorded as **False Alarm Episodes**.
- For each detected event, the **timing error** $\Delta t_{\text{onset}} = t_{\text{pred\_onset}} - T_{\text{onset}}$ is computed, reporting median and interquartile range (IQR).

---

## 3. Class Imbalance, Prevalence, and PR-AUC

Solar flares are rare transient events; quiet Sun observations constitute $> 95\%$ to $> 99\%$ of operational data.

### Why Accuracy is Prohibited as a Headline Metric
Under a 98% negative class prevalence, a degenerate trivial classifier that unconditionally predicts 0 achieves $98.0\%$ accuracy while detecting zero solar flares. Accuracy gives a false impression of performance and must never be cited as a primary metric.

### Precision-Recall AUC (PR-AUC) as the Primary Metric
Under extreme imbalance, ROC curves are overly optimistic because the large number of true negatives keeps the false positive rate $\text{FPR} = \frac{\text{FP}}{\text{TN} + \text{FP}}$ very small even when false positives vastly outnumber true positives.

In contrast, the Precision-Recall curve focuses directly on the minority class:
$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \quad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
Every metric table in SOLARIS-A1 **must explicitly report prevalence** ($P = \frac{N_{\text{pos}}}{N_{\text{total}}}$). The baseline uninformative PR-AUC is equal to the prevalence $P$, providing an immediate, honest benchmark.

---

## 4. Overlapping Windows, Effective Sample Size, and Embargoes

With window length $W = 60\text{ s}$ and stride $S = 10\text{ s}$, consecutive windows share:
$$\text{Overlap} = \frac{W - S}{W} = \frac{50\text{ s}}{60\text{ s}} = 83.3\%$$
adjacent sensor readings.

### Statistical Implications
1. **Inflated Nominal Sample Size**: 1,000 sliding windows do not represent 1,000 independent degrees of freedom. The effective sample size $N_{\text{eff}} \ll N$.
2. **Leakage Hazard**: If windows are randomly split into training and test sets, window $i$ in the training set and window $i+1$ in the test set share $83.3\%$ of their raw time series, allowing models to memorize noise fluctuations.
3. **Mandatory Embargo Buffer**: To prevent leakage across partition boundaries, a temporal embargo buffer of duration $E \ge 300\text{ s}$ is excised between the training, validation, and test partitions.

---

## 5. False Alarms Normalized by Covered Science Time

In space observatories like Aditya-L1 SoLEXS, observations are interrupted by orbital night, South Atlantic Anomaly (SAA) passages, and telemetry downlink dropouts.

Operational false alarm rates must be calculated **strictly against valid Good Time Intervals (GTI)**:
$$\text{FAR} = \frac{N_{\text{false\_alarms}}}{T_{\text{covered\_hours}}} \quad \left[\text{hour}^{-1}\right]$$
where:
$$T_{\text{covered\_hours}} = \frac{1}{3600} \sum_{k=1}^M (T_{k, \text{stop}} - T_{k, \text{start}})$$
Using uncorrected wall-clock time artificially inflates the denominator during non-operational periods, masking high false-alarm rates during active science observations.

---

## 6. Probability Calibration Assessment

Machine learning models (especially tree ensembles and neural networks) often output scores that do not reflect true posterior event probabilities.

Stage 11 assesses probability calibration using:
1. **Reliability Diagrams**: Grouping predicted scores $p \in [0, 1]$ into $B$ equal-width bins and plotting mean predicted probability versus empirical positive fraction.
2. **Expected Calibration Error (ECE)**:
   $$\text{ECE} = \sum_{b=1}^B \frac{N_b}{N} |\bar{p}_b - \bar{y}_b|$$
3. **Brier Score**: Mean squared error between probabilistic forecasts and binary outcomes:
   $$\text{Brier} = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$$

Calibration in Stage 11 is strictly observational: no post-hoc scaling (e.g. Platt scaling or isotonic regression) is applied to the test set, as fitting calibration parameters on test data violates test isolation.

---

## 7. Block Bootstrap Uncertainty Estimation

Standard row-level bootstrapping assumes independent and identically distributed (i.i.d.) observations. Applying row bootstrapping to overlapping time series windows yields invalid, artificially narrow confidence intervals.

SOLARIS-A1 implements **Block Bootstrapping**:
- Entire contiguous science segments (or isolated event episodes) are resampled with replacement.
- All windows belonging to a selected segment are drawn together, preserving internal temporal autocorrelation.
- **Scientific Floor Requirement**: If the test set contains fewer than $N_{\text{min}} = 5$ independent segments, computing confidence intervals is statistically unsound. The pipeline withholds the computation and reports:
  `"CI NOT COMPUTED — insufficient independent blocks (n=<n>)"`.

---

## 8. The Single-Shot Evaluation Rule

Under scientific best practices:
1. The test set represents the final unseen trial of the trained model.
2. If models are evaluated on test data, adjusted, and re-evaluated, the test set effectively becomes a tuning validation set, causing silent overoptimism (data snooping).
3. In SOLARIS-A1:
   - The test set is cryptographically sealed in Stage 10 with a SHA-256 hash.
   - Stage 11 executes the evaluation **exactly once**.
   - The experiment status transitions to `EVALUATED_ONCE`.
   - Any subsequent call to evaluate the experiment directory raises an error and refuses to run.
   - Test results are immutable and await human researcher scientific review at Gate **G9**.
