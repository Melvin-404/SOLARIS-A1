# Project Requirements: SOLARIS-A1

## Project Title
**Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations**

**Project Identifier:** `SOLARIS-A1`  
*(Note: The project identifier `SOLARIS-A1` is permanent and must not be altered.)*

---

## 1. Project Aims and Research Context

`SOLARIS-A1` is an academic research project investigating the application of machine learning techniques to solar X-ray observations from the Solar Low Energy X-ray Spectrometer (SoLEXS) onboard India's Aditya-L1 mission. The project utilises real Level-1 solar X-ray light-curve FITS files and corresponding Good Time Interval (GTI) FITS files downloaded from the official ISRO / ISSDC PRADAN data archive.

The project is structured around two distinct scientific tasks:
- **Task A — Solar Flare Detection:** Determine whether solar flare activity occurs within a defined observation window, evaluated against independently verified flare-event ground-truth catalogues.
- **Task B — Pre-Flare Prediction / Forecasting:** A distinct forecasting experiment assessing whether X-ray light-curve characteristics prior to a prediction epoch contain measurable precursor signals informative of a flare occurring within a defined future horizon window $[t_{\text{pred}}, t_{\text{pred}} + \Delta t_{\text{horizon}}]$.

### 1.1 Critical Scientific Distinctions
To maintain scientific rigor and prevent misleading claims, the project strictly distinguishes among three operational regimes:
1. **Detecting a flare in progress:** Classifying observations during an active flare event based on elevated flux, rapid rise, or spectral hardness changes.
2. **Identifying candidate transient X-ray events:** Unsupervised or threshold-based identification of transient deviations from background flux that warrant verification.
3. **Predicting a future flare before onset:** A pure forecasting task that evaluates conditions *strictly prior to flare onset*. Under no circumstances may a model be claimed to "predict" or "forecast" a flare merely because counts or derivatives rise during an ongoing flare.

Task A must be implemented and validated first. Task B is a separate experiment requiring its own data-splitting, feature temporal boundaries, and negative-sampling protocol; it must never be presented as a simple extension or by-product of Task A.

### 1.2 Research Questions

#### Task A (Solar Flare Detection)
- **RQ-A1:** How reliably can machine learning classifiers (Logistic Regression, Random Forest, XGBoost) detect ongoing solar flare activity in SoLEXS Level-1 full-disk X-ray light curves across varying background levels and noise conditions?
- **RQ-A2:** How do supervised machine learning detectors compare with traditional flux-thresholding and derivative-thresholding physical baselines in terms of precision, recall, false-alarm rate, and detection latency?
- **RQ-A3:** How robust is the detection pipeline when operating across orbital boundaries, instrumental gaps, and valid GTI segments?

#### Task B (Pre-Flare Prediction / Forecasting)
- **RQ-B1:** Are there statistically significant precursor signatures (e.g., subtle pre-flare brightenings, variance changes, or spectral hardness variations) present in SoLEXS Level-1 light curves in the pre-onset window prior to solar flares?
- **RQ-B2:** Can machine learning models trained strictly on pre-onset windows forecast flare occurrence within defined horizons (e.g., 10 min, 30 min, 60 min) with performance superior to random guessing and persistence baselines, while maintaining acceptable false-positive rates during extended quiet periods?

---

## 2. Division of Responsibilities

To preserve academic integrity and research validity, the boundary between automated tooling (Antigravity IDE Assistant) and student authorship (Human Researcher) is strictly defined.

### 2.1 Antigravity Scope (Automated Development & Infrastructure)
Antigravity is responsible for implementing:
- Repository architecture, directory layout, and virtual environment setup.
- Data ingestion pipelines for Level-1 FITS and GTI files.
- GTI-aware filtering, data validation, and automated quality assessment.
- Exploratory Data Analysis (EDA) tooling and interactive light-curve visualization.
- Event catalogue ingestion and verified label infrastructure.
- Temporal segmentation, gap-respecting sliding-window extraction, and feature engineering.
- Dataset export (clean tabular features, labels, timestamps, and metadata).
- Testing suites, reproducibility manifests, and configuration files.
- The interactive Streamlit research dashboard.
- Framework templates and harnesses for model evaluation.

### 2.2 Student Scope (Human Researcher)
The student researcher holds sole authority and responsibility for:
- Formulating and approving all scientific assumptions, time tolerances, and labelling policies.
- Selection of verified external event catalogues (e.g., GOES flare catalogue, ISRO/PRADAN published event lists).
- Implementing and executing model training for Logistic Regression, Random Forest, and XGBoost.
- Designing and conducting hyperparameter tuning and model selection experiments.
- Choosing class-imbalance handling strategies and train/validation/test split policies.
- Running validation and final test set evaluations.
- Scientific interpretation of metrics, error analyses, and domain conclusions.
- Thesis and paper write-up.

**Prohibition on Antigravity:** Antigravity MUST NOT train research models, tune hyperparameters, run final comparative model evaluations, or fabricate/invent performance results.

---

## 3. Functional Requirements (16 Core Capabilities)

The `SOLARIS-A1` platform shall provide the following 16 functional capabilities:

1. **FR-01: SoLEXS FITS Inspection**  
   Inspect raw Level-1 SoLEXS FITS files without preconceived assumptions regarding header keywords, data types, column names, energy channels, or time conventions. Extract and display complete HDU structure and metadata.

2. **FR-02: GTI-Aware Validation**  
   Ingest official Good Time Interval (GTI) FITS files. Match GTI intervals with light-curve timestamps to validate data integrity. Ensure no downstream window or feature spans across invalid observation periods.

3. **FR-03: Coverage and Quality Reporting**  
   Generate detailed observational quality metrics per data file, including nominal sampling cadence, missing packet ratios, flagged data percentages, effective exposure times, and orbital night/eclipse gaps.

4. **FR-04: Interactive Light-Curve Visualization**  
   Provide dynamic, zoomable light-curve plots displaying photon count rates or flux across all available energy channels, with overlaid GTI boundaries and gap annotations.

5. **FR-05: Inspection of Verified Events**  
   Enable interactive visual overlay and tabular inspection of independently verified solar flare events onto SoLEXS light curves, showing catalogued onset, peak, end times, and flare classes.

6. **FR-06: Documented Labelling Infrastructure**  
   Implement an auditable, deterministic labelling engine that assigns window-level and point-level labels based on approved decision rules, logging all threshold parameters, time tolerances, and ambiguity flags.

7. **FR-07: Configurable Sliding Windows**  
   Extract time-series windows with user-configurable window lengths ($W$) and stride intervals ($S$). Enforce strict boundaries ensuring that windows are continuous and contained entirely within single GTI intervals.

8. **FR-08: Time-Series Feature Engineering**  
   Calculate statistical, morphological, and temporal domain features across each window (e.g., central moments, percentiles, min/max ratios, slopes, peak count rates, channel hardness ratios).

9. **FR-09: Standardized Dataset Export**  
   Export feature matrices with aligned binary labels, multi-class labels, window start/end timestamps, GTI IDs, and file provenance into standard columnar formats (Parquet and CSV).

10. **FR-10: Student-Controlled Training & Evaluation Harness**  
    Provide clear, modular interfaces and scripts that allow the student to load exported datasets, train classifiers, tune hyperparameters, and log performance metrics without automated intervention.

11. **FR-11: Threshold Baseline Comparison**  
    Provide baseline detector implementations based on standard solar physics practices (e.g., $N$-sigma thresholding above quiescent background, derivative triggers) to serve as benchmarks against ML models.

12. **FR-12: Event-Level Performance Analysis**  
    Evaluate model outputs not only on window-by-window metrics (precision, recall, ROC-AUC) but also on event-level metrics: detection latency relative to catalogue onset, full event detection rate, and false event trigger frequency.

13. **FR-13: Pre-Flare Forecasting Infrastructure (Task B)**  
    Provide specialized data structuring for pre-flare prediction: define prediction epoch $t_{\text{pred}}$, forecast horizon $\Delta t_{\text{horizon}}$, and feature extraction window $[t_{\text{pred}} - W_{\text{pre}}, t_{\text{pred}}]$, strictly excluding data from $[t_{\text{pred}}, \infty)$ to prevent temporal leakage.

14. **FR-14: Streamlit Research Dashboard**  
    Provide a local, interactive Streamlit application enabling data exploration, quality validation, label inspection, feature visualization, and student-generated model result visualization.

15. **FR-15: Comprehensive Documentation & Reproducibility**  
    Maintain rigorous documentation including data dictionaries, pipeline schemas, environment lockfiles, random seed management, and decision records for complete scientific auditability.

16. **FR-16: Transparent Handling of Unresolved Assumptions**  
    Explicitly flag and isolate any unknown or provisional scientific, instrumental, or pipeline parameter in the project Decision Log. Prohibit silent fallback to unverified defaults.

---

## 4. Non-Functional Requirements

- **NFR-01: Local Execution on Windows**  
  The complete pipeline must run reliably in a local Windows 10/11 environment utilizing standard Python virtual environments.
- **NFR-02: Zero Paid Cloud Dependencies**  
  No proprietary cloud services, paid compute instances, or commercial APIs may be used. All computation must execute on local hardware.
- **NFR-03: CPU-Tractable Computation**  
  The system must operate without requiring an NVIDIA GPU. Feature extraction, baseline algorithms, and student models (Logistic Regression, Random Forest, XGBoost) must be optimized for multi-core CPU execution.
- **NFR-04: No Auto-Training on Dashboard Startup**  
  The Streamlit dashboard must serve strictly as an analytical and visualization interface. It must never initiate model training, hyperparameter searches, or large-scale batch feature generation upon startup.
- **NFR-05: Raw Data Immutability**  
  Raw downloaded FITS and GTI files must be treated as strictly read-only. No script or process may alter, move, or overwrite raw data.
- **NFR-06: Relative and Configurable Paths**  
  All filesystem paths must be relative to the project root or specified via environment configuration, ensuring portability across machines.

---

## 5. Constraints and Out-of-Scope Items

### 5.1 Out-of-Scope Items
- **No Real-Time / Live Telemetry:** The project operates exclusively on archived Level-1 data retrieved from the ISRO ISSDC PRADAN portal.
- **No Spatial Flare Localisation:** SoLEXS is a non-imaging, full-disk solar spectrometer. Active-region spatial localization (solar disk coordinates) cannot be determined from SoLEXS alone and is strictly out of scope.
- **No Synthetic or Fabricated Ground Truth:** All ground-truth flare records must come from legitimate, verified solar event catalogues (e.g., GOES flare catalogue, ISRO official event publications). No simulated or heuristic-only flare labels may be treated as ground truth.
- **No Automated Scientific Claims:** Antigravity will not generate conclusions regarding solar physics or algorithm superiority. All scientific interpretations belong to the student.

---

## 6. Verification and Acceptance Criteria
1. The requirements document explicitly details the 16 functional requirements and 6 non-functional requirements.
2. The operational distinction between Task A (flare detection) and Task B (pre-flare prediction) is unambiguous.
3. The division of responsibility between Antigravity and the student is clearly demarcated.
4. No unverified scientific constants or instrumental assumptions are stated as facts without verification tags.
