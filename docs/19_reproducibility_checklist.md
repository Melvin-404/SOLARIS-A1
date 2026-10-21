# Reproducibility Checklist (Stage 14)

**Project:** `SOLARIS-A1`  
**Execution Date:** `2026-10-21`  
**Evaluation Scope:** Development pipeline, automated tests, and cryptographic integrity verification.  

Every checklist item below is annotated with an explicit status from the standard vocabulary:
- `VERIFIED in this run`: Verified by direct execution and inspection in Stage 14.
- `NOT RUN`: Deliberately not executed in this run (e.g. prohibited test-set re-evaluation).
- `FAILED`: Executed and failed to meet expected condition.
- `NOT APPLICABLE`: Not applicable to current single-day development state.

---

## 1. Reproducibility Register

| Item # | Verification Item | Status | Evidence / Artifact Reference | Details |
| :---: | :--- | :---: | :--- | :--- |
| **01** | **Environment reproducible from requirements** | `VERIFIED in this run` | `requirements.txt`<br>`scripts/verify_environment.py`<br>`pip check` | Fresh environment installs all required packages without dependency conflicts (`pip check` exit code 0). |
| **02** | **Raw data hashes unchanged** | `VERIFIED in this run` | `results/checks/pre_hashes.json`<br>`data/raw/` | All 6 files in `data/raw/` have byte-for-byte identical SHA-256 hashes before and after all test runs. |
| **03** | **Manifest checker passes** | `VERIFIED in this run` | `tests/test_ingestion_manifest.py`<br>`data/manifests/` | Ingestion manifest matches raw file directory structure, sizes, and cryptographic checksums. |
| **04** | **Column roles status** | `VERIFIED in this run` | `config/column_roles.yaml`<br>`results/quality/column_role_evidence.json` | Explicitly marked as `PROVISIONAL pending Gate G1`. Rate column `COUNTS` and time system documented. |
| **05** | **Quality outputs reproducible** | `VERIFIED in this run` | `scripts/check_real_reproducibility.py`<br>`data/processed/quality/` | Quality metrics table generated in temporary environment matches workspace artifact bit-for-bit. |
| **06** | **Preprocessing reproducible** | `VERIFIED in this run` | `scripts/check_real_reproducibility.py`<br>`data/processed/segments/` | Segment CSV files and sample reconciliation table match workspace artifacts bit-for-bit. |
| **07** | **Window and feature reproducible** | `VERIFIED in this run` | `scripts/check_real_reproducibility.py`<br>`data/processed/features/` | Sliding-window indices and causal feature matrices match workspace artifacts bit-for-bit. |
| **08** | **Export reproducible** | `VERIFIED in this run` | `tests/integration/test_reproducibility_synthetic.py`<br>`results/exports/` | Synthetic export under approved fixture is 100% deterministic; production export refuses under draft policy. |
| **09** | **Policy approval status and hash** | `VERIFIED in this run` | `docs/08_labelling_policy.md`<br>`config/decisions.yaml` (D-01..D-04) | Policy status verified as `DRAFT` (Gate G3 pending); SHA-256 recorded in pipeline status reports. |
| **10** | **Protocol status and hash** | `VERIFIED in this run` | `docs/14_training_protocol.md`<br>`results/training/` | Training protocol verified as `PROTO_STAGE10_DRAFT_001`; configuration snapshot hashed. |
| **11** | **Lock status** | `VERIFIED in this run` | `results/training/test_set_lock.json`<br>`tests/test_integrity.py` | Test set sealed with SHA-256 hash `d20058b8...`. Integrity test asserts tamper detection. |
| **12** | **Random seeds recorded** | `VERIFIED in this run` | `config/default.yaml`<br>`results/training/` | Random seeds (`seed: 42`) recorded across configuration, model initialization, and data splitting modules. |
| **13** | **Software versions recorded** | `VERIFIED in this run` | `docs/18_test_report.md`<br>`results/checks/full_check_*.md` | Exact runtime versions recorded: Python 3.12.10, numpy 2.5.4, pandas 3.0.6, astropy 8.0.2, scikit-learn 1.9.1, xgboost 3.4.1. |
| **14** | **Dashboard read-only** | `VERIFIED in this run` | `tests/test_readonly_dashboard.py`<br>`dashboard/` | Static AST audit and runtime AppTest simulations verify no data mutation, training, or writing calls. |
| **15** | **Documentation links** | `VERIFIED in this run` | `docs/`, `README.md` | All technical documentation files (00 through 20) are cross-referenced with valid relative links. |
| **16** | **Test-set model evaluation re-run** | `NOT RUN` | `results/evaluation/`<br>`docs/15_evaluation_methods.md` | Deliberately **NOT RUN** in Stage 14 to prevent post-hoc snooping and preserve single-shot test set purity. |

---

## 2. Integrity Verification Protocol for Human Researchers

When performing independent verification, researchers can replicate the entire reproducibility audit using:

```powershell
# 1. Activate isolated virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Run the end-to-end full check runner
python scripts/run_full_pipeline_check.py

# 3. Verify real-data reproducibility against isolated execution
python scripts/check_real_reproducibility.py
```
