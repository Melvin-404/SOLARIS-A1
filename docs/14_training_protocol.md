# SOLARIS-A1: Machine Learning Training Protocol (Stage 10)

## 1. Scientific Governance & The Human Protocol Gate (Gate G7)

In `SOLARIS-A1`, the machine learning training protocol is strictly owned and approved by the human researcher. Antigravity drafts options in `config/training_protocol.yaml` under status `DRAFT`.
**Antigravity is strictly forbidden from self-approving or freezing the protocol.**
Only the human researcher sets `status: FROZEN` (for the main experiment) or `status: PILOT` (for exploratory pilot runs), recording their name and approval date.

---

## 2. Why Random Row-Level Splitting Is Invalid

> [!WARNING]
> **CATASTROPHIC TEMPORAL LEAKAGE WARNING:**  
> Standard machine learning practices often employ randomized row-level train/test partitioning (e.g. `sklearn.model_selection.train_test_split(shuffle=True)`). **This practice is strictly invalid for continuous time series with overlapping sliding windows.**

In `SOLARIS-A1`, sliding windows are generated with duration $W = 60\text{ s}$ and stride $S = 10\text{ s}$. As a consequence:
$$\text{Overlap Duration} = W - S = 50.0\text{ s} \quad \implies \quad \frac{50}{60} \approx 83.3\% \text{ of raw observational samples are shared between adjacent windows.}$$

If rows are shuffled randomly:
1. Training windows will share over $80\%$ of their raw sensor samples with test windows.
2. Estimators will trivially memorize window-specific flux fluctuations rather than learning generalizable flare precursor dynamics.
3. Cross-validation and test scores will be artificially inflated, failing catastrophically when deployed on novel continuous observations.

To prevent this, `SOLARIS-A1` enforces strictly partitioned, non-random split strategies.

---

## 3. Approved Partitioning Strategies

### Strategy A: Chronological Splitting with Embargo Buffers (`chronological`)
- **Structure:**
  - Training: all windows with $w_{\text{end}} \le t_{\text{train\_end}}$.
  - Embargo 1: $(t_{\text{train\_end}}, t_{\text{train\_end}} + \text{embargo}]$. Windows in this buffer are **completely dropped**.
  - Validation: windows with $w_{\text{start}} \ge t_{\text{train\_end}} + \text{embargo}$ and $w_{\text{end}} \le t_{\text{val\_end}}$.
  - Embargo 2: $(t_{\text{val\_end}}, t_{\text{val\_end}} + \text{embargo}]$. Windows in this buffer are **completely dropped**.
  - Test: windows with $w_{\text{start}} \ge t_{\text{val\_end}} + \text{embargo}$.
- **Embargo Buffer ($T_{\text{embargo}}$):** Default $300.0\text{ s}$ (5 minutes) ensures that autocorrelation and transient sensor memory decay to zero across boundaries.

### Strategy B: Event-Grouped Splitting (`event_grouped`)
- All windows originating from the same continuous segment or associated with the same solar flare event ID are grouped together.
- Groups are assigned atomically to either train, validation, or test.
- No group is ever split across two partitions.

---

## 4. Training-Only Preprocessing Fit

Feature normalization (e.g. `StandardScaler`, `RobustScaler`) and any optional feature selection must be fitted **exclusively on the training partition**:
$$\mu_{\text{train}} = \frac{1}{N_{\text{train}}} \sum_{i \in \text{train}} x_i, \qquad \sigma_{\text{train}} = \sqrt{\frac{1}{N_{\text{train}} - 1} \sum_{i \in \text{train}} (x_i - \mu_{\text{train}})^2}$$

The learned $\mu_{\text{train}}$ and $\sigma_{\text{train}}$ are then applied to transform validation and test sets:
$$z_{\text{val}} = \frac{x_{\text{val}} - \mu_{\text{train}}}{\sigma_{\text{train}}}, \qquad z_{\text{test}} = \frac{x_{\text{test}} - \mu_{\text{train}}}{\sigma_{\text{train}}}$$

Computing scaling parameters over the entire dataset prior to splitting leaks validation and test distributions into the training pipeline and is blocked by [`assert_no_test_in_fit`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/modelling/guards.py).

### Imputation Policy: Strict Prohibition
The default imputer is `NONE`. If non-finite values (`NaN`, `Inf`) appear in training features, [`MissingFeatureError`](file:///c:/Users/melvi/Desktop/SOLARIS-A1/src/solar_flare/modelling/guards.py) is raised. Silent mean or median imputation is strictly prohibited.

---

## 5. Candidate Estimators & Deterministic Seeds

Stage 10 implements three foundational estimators:
1. **Logistic Regression (L2 / ElasticNet regularized):** Interpretable linear baseline with explicit coefficient weights.
2. **Random Forest Classifier (Ensemble bagging):** Non-linear tree ensemble capturing complex feature interactions and non-monotonic thresholds.
3. **XGBoost Classifier (Gradient boosted trees):** State-of-the-art gradient boosting with histogram-based binning (`tree_method='hist'`).

All estimators are pinned to deterministic random seeds (`random_state=42`) and single-threaded or deterministic execution to ensure bit-for-bit reproducibility.

---

## 6. Validation-Only Selection & The Sealed Test Set Lock

1. **Hyperparameter Selection:**
   - Candidate hyperparameter configurations are evaluated strictly on the **validation partition** using Precision-Recall Area Under Curve (`PR_AUC`).
   - The test set is **never passed** to the tuning function (`run_selection` signature accepts only train and val).
2. **Cryptographic Sealing:**
   - Prior to model selection, the test partition is sealed in `results/experiments/<experiment_id>/sealed/test_set.csv`.
   - A cryptographic SHA-256 hash is recorded in `lock_record.json`.
   - File permissions are set to read-only where the operating system permits.
3. **Zero Test Read Obligation:**
   - Every read to the test set is logged in `access_log.jsonl`.
   - During Stage 10, the access log must record **zero read events**.
   - Test evaluation is performed exclusively in **Stage 11** under Gate G8 approval.
