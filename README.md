# SOLARIS-A1

## Project Title
**Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis Using Aditya-L1 SoLEXS Observations**

**Permanent Project Identifier:** `SOLARIS-A1`

---

## Current Status
**Status:** `Stage 3 — FITS Data Inventory and Metadata Inspection`

Reusable, non-destructive FITS inspection tools (`src/solar_flare/inspection/`) and the automated inventory generator (`scripts/inspect_fits.py`) are fully implemented and verified. Real Aditya-L1 SoLEXS Level-1 data files are indexed in `data/manifests/manifest.csv` and verified in `data/raw/`. An initial metadata inventory, inspection report, and open questions register have been generated with 100% hash immutability verified.

---

## Data Acquisition & Inspection

### 1. Data Acquisition
Download official Level-1 SoLEXS light-curve and GTI FITS files from the ISRO ISSDC PRADAN portal following [`docs/data_acquisition.md`](docs/data_acquisition.md). Record entries in [`data/manifests/manifest.csv`](data/manifests/manifest.csv) and verify disk consistency:
```powershell
python scripts/check_manifest.py data/manifests/manifest.csv
```

### 2. Inspect FITS Files
Extract FITS HDU structures, column metadata, time-system keywords, and numerical statistics without modifying raw files:
```powershell
python scripts/inspect_fits.py
```
This command generates:
- `results/inventory/inventory.csv` & `inventory.json`
- `results/inventory/inspection_report.md`
- `results/inventory/open_questions.md`

For interactive, visual inspection of light curves and headers in Jupyter, open [`notebooks/01_fits_inspection.ipynb`](notebooks/01_fits_inspection.ipynb).

---

## Windows Setup

To configure and verify the local Python environment on Windows, execute the following commands in PowerShell from the project root:

```powershell
# 1. Create the virtual environment
python -m venv .venv

# 2. Configure process-scoped script execution policy (if blocked by Windows security)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 3. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install runtime and development dependencies
python -m pip install -r requirements-dev.txt

# 6. Verify environment, packages, and configuration
python scripts/verify_environment.py

# 7. Run unit test suite
python -m pytest -v
```

> **PowerShell Execution Policy Note:** If Windows reports that running scripts is disabled (`PSSecurityException`), do not disable security globally. Instead, apply the process-level bypass shown above (`-Scope Process`), which grants execution permissions solely to the current terminal session without weakening system-wide security. See [`docs/setup_windows.md`](docs/setup_windows.md) for full troubleshooting.

---

## Project Structure
```text
SOLARIS-A1/
├── README.md                      # Project overview, status, and setup instructions
├── requirements.txt               # Pinned core runtime dependencies
├── requirements-dev.txt           # Development and testing dependencies
├── .gitignore                     # Git ignore rules (protects data, venv, logs)
├── pyproject.toml                 # Pytest pythonpath configuration and project metadata
├── config/
│   └── default.yaml               # Application configuration with pending scientific params
├── data/
│   ├── raw/                       # STRICTLY READ-ONLY: Real Level-1 SoLEXS FITS files
│   │   └── gti/                   # GTI storage subfolder (if categorized separately)
│   ├── processed/                 # Exported tabular feature matrices and labels
│   └── manifests/                 # Provenance logs and checksum manifests
│       ├── manifest.csv           # Active dataset manifest
│       └── manifest_template.csv  # Manifest schema template
├── docs/
│   ├── 00_requirements.md         # Requirements, scope, and responsibility split
│   ├── 01_decision_log.md         # Architectural and scientific decision register
│   ├── 02_roadmap.md              # 17-stage implementation roadmap
│   ├── 03_architecture.md         # System architecture and layer boundaries
│   ├── 03_inspection_methods.md   # FITS inspection methodology & interpretation guide
│   ├── setup_windows.md           # Windows setup and troubleshooting notes
│   └── data_acquisition.md        # Official PRADAN data access and pairing protocol
├── logs/                          # Application logs (rotating file logs)
├── notebooks/                     # Jupyter notebooks for EDA and student training
│   └── 01_fits_inspection.ipynb   # Interactive FITS inspection notebook
├── results/                       # Generated outputs and figures (gitignored)
│   └── inventory/                 # Generated inventory tables and inspection reports
├── scripts/
│   ├── verify_environment.py      # Automated environment and config diagnostic tool
│   ├── check_manifest.py          # Offline manifest and disk hash verification tool
│   └── inspect_fits.py            # FITS metadata inventory and inspection tool
├── src/
│   └── solar_flare/
│       ├── __init__.py            # Package metadata
│       ├── config.py              # YAML config loader with path resolution & validation
│       ├── logging_setup.py       # Idempotent console & rotating file logging
│       ├── manifest.py            # Manifest parsing, chunked SHA-256, and disk audit
│       ├── paths.py               # Repository-anchored path resolution utilities
│       └── inspection/            # FITS inspection subsystem
│           ├── __init__.py
│           ├── fits_inspect.py    # Non-destructive HDU, column, and statistics extraction
│           ├── time_systems.py    # Astronomical time keyword extraction and interpretation
│           └── inventory.py       # Tabular inventory builder with UNRESOLVED role flags
└── tests/
    ├── __init__.py                # Test package
    ├── test_config.py             # Config loading and error handling tests
    ├── test_inspection.py         # FITS inspection and immutability tests (synthetic fixtures)
    ├── test_logging.py            # Logging setup and idempotency tests
    ├── test_manifest.py           # Manifest loading, hashing, and pairing tests
    └── test_paths.py              # Path resolution unit tests
```

---

## Project Overview
`SOLARIS-A1` is an academic research project investigating machine learning methods for solar flare detection and pre-flare activity analysis using real Level-1 solar X-ray light-curve FITS files and corresponding Good Time Interval (GTI) FITS files from the Solar Low Energy X-ray Spectrometer (SoLEXS) onboard India's Aditya-L1 mission (archived at the official ISRO/ISSDC PRADAN portal).

The project is structured into two distinct scientific tasks:
- **Task A (Solar Flare Detection):** Determine whether solar flare activity occurs within a defined observation window using independently verified ground-truth event labels.
- **Task B (Pre-Flare Prediction / Forecasting):** A separate forecasting experiment evaluating whether light-curve characteristics prior to a prediction epoch are informative of a future flare occurring within a defined horizon, strictly avoiding temporal leakage from active flare onset.

---

## Division of Responsibilities
- **Antigravity (Automated IDE Assistant):** Implements project structure, environment configuration, data ingestion, GTI-aware preprocessing, exploratory analysis, labelling infrastructure, segmentation, windowing, feature engineering, dataset export, baseline detectors, evaluation harnesses, tests, documentation, and the Streamlit dashboard.
- **Student Researcher (Human):** Holds sole authority for approval of scientific assumptions, labelling policies, and ground-truth catalogues; implements and executes training for Logistic Regression, Random Forest, and XGBoost; conducts hyperparameter tuning and model selection; executes validation and final test runs; and performs scientific interpretation of results. **Antigravity does not train research models or invent performance figures.**

---

## Documentation Index
Detailed project documentation is available in the [`docs/`](docs/) directory:

- [**00. Requirements Specification**](docs/00_requirements.md) — Research questions, 16 functional requirements, non-functional requirements, constraints, and division of responsibility.
- [**01. Decision Log**](docs/01_decision_log.md) — Log of architectural and scientific decisions (D-01 through D-14) tracking open, provisional, and approved statuses.
- [**02. Roadmap**](docs/02_roadmap.md) — The 17-stage project implementation lifecycle (Stages 0–16), including dependencies, deliverables, and student approval gates.
- [**03. System Architecture**](docs/03_architecture.md) — Layered software architecture, unidirectional data flow, write permissions, and subsystem designs.
- [**03b. FITS Inspection Methods**](docs/03_inspection_methods.md) — Inspection algorithms, role detection heuristics, and inventory interpretation guidelines.
- [**04. Quality Assessment Methods**](docs/04_quality_methods.md) — Pure functional quality checks, cadence diagnostics, GTI coverage quantification, and Gate G1/G2 protocols.
- [**05. EDA Methods**](docs/05_eda_methods.md) — Robust running baseline, candidate burst intervals, and variability metrics.
- [**05b. EDA Findings**](docs/05_eda_findings.md) — Automated statistical summaries and qualitative observation prompts.
- [**06. Event Record Schema**](docs/06_event_record_schema.md) — Ground-truth solar flare event record specification (template).
- [**Setup & Troubleshooting (Windows)**](docs/setup_windows.md) — Step-by-step PowerShell environment setup, execution policies, and Windows troubleshooting.
- [**Official Data Acquisition Protocol**](docs/data_acquisition.md) — ISRO ISSDC PRADAN portal retrieval instructions, pairing rules, and checksum logging.

---

## Quality Assessment (Stage 4)
Stage 4 establishes non-destructive data quality characterisation of Aditya-L1 SoLEXS Level-1 light-curve and GTI observations:
- **Zero Mutation:** Real data is never clipped, imputed, interpolated, or filtered.
- **Segregated Sample Tracking:** NaN samples (4,849 observed in SDD2), zero counts, negative counts (0 detected), backward steps (0 detected), duplicate timestamps (0 detected), and candidate statistical spikes ($z_{\text{robust}} > 5.0$) are reported in dedicated, isolated metrics.
- **Candidate Spikes:** Flagged strictly as *"candidate spike — not a verified event"*.
- **Cadence & GTI:** Empirical median cadence (1.0000 s) and GTI coverage quantified without discarding points.
- **PROVISIONAL Status:** All results remain strictly `PROVISIONAL pending G1` human researcher confirmation.

Run quality assessment CLI:
```powershell
python scripts/run_quality.py --raw-dir data/raw --manifest data/manifests/manifest.csv --out-dir results/quality
```

---

## Exploratory Data Analysis (Stage 5)
Stage 5 implements reproducible exploratory data analysis of light-curve variability, count distributions, coverage timelines, running baselines, and candidate transient bursts:
- **Unverified Candidate Status:** All detected candidate intervals are strictly tagged `CANDIDATE — UNVERIFIED`.
- **Zero Labeling Guarantee:** Nothing produced in Stage 5 is a flare label, ground truth, or training target.
- **Event Comparison Check:** Returns strictly `NOT PERFORMED — no independent event records supplied` until external event catalogues are confirmed at Gate G3.

Run EDA CLI:
```powershell
python scripts/run_eda.py --out-dir results/eda
```

Execute exploratory notebook:
```powershell
jupyter nbconvert --to notebook --execute notebooks/02_eda.ipynb --output 02_eda_executed.ipynb --output-dir results/eda/notebook_runs
```

---

## Next Steps (Stage 6 Source Research)
- The human student researcher may review candidate burst behavior in [`docs/05_eda_findings.md`](docs/05_eda_findings.md) and [`notebooks/02_eda.ipynb`](notebooks/02_eda.ipynb).
- Stage 6 independent event catalogue research may begin now.
- **Label generation and training table creation remain strictly blocked until Gate G3.**
