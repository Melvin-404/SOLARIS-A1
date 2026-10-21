# Final Human Acceptance Checklist

**Project:** `SOLARIS-A1`  
**Phase:** Final Human Acceptance Testing  
**Auditor / Reviewer:** Human Researcher / Principal Investigator  

> [!IMPORTANT]
> **Instructions for Human Researcher:**  
> This acceptance checklist must be performed and verified personally by the human researcher. Antigravity does **not** perform or sign off on human acceptance. Execute each command listed below in a fresh shell, verify the expected outcome, and mark your personal assessment in the blank result fields provided. Do not modify or fill in these fields programmatically.

---

## 1. Acceptance Criteria & Verification Protocol

### Check 1: Virtual Environment and Dependency Integrity
- **Command:**  
  ```powershell
  .\.venv\Scripts\Activate.ps1
  pip check
  python scripts/verify_environment.py
  ```
- **Expected Outcome:**  
  `pip check` outputs `No broken requirements found.` with exit code `0`.  
  `verify_environment.py` passes all checks (Platform, Dependencies, Scaffolding, Git) with exit code `0`.
- **Human Review Result:**  
  `[ ] PASS` &nbsp;&nbsp;&nbsp;&nbsp; `[ ] FAIL`  
  *Human Notes:*  
  *Date Checked:*  

---

### Check 2: Raw Data Immutability and Checksum Preservation
- **Command:**  
  ```powershell
  python -c "import json, hashlib, pathlib; hashes = json.load(open('results/checks/pre_hashes.json')); [print(f'{f}: MATCH' if hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest() == (h['sha256'] if isinstance(h, dict) else h) else f'{f}: MISMATCH') for f, h in hashes.items()]"
  ```
- **Expected Outcome:**  
  All 6 raw files in `data/raw/` report `MATCH`. Zero bytes altered.
- **Human Review Result:**  
  `[ ] PASS` &nbsp;&nbsp;&nbsp;&nbsp; `[ ] FAIL`  
  *Human Notes:*  
  *Date Checked:*  

---

### Check 3: Automated Test Suite and Static Safeguard AST Audit
- **Command:**  
  ```powershell
  pytest tests/ tests/integration/ -v
  ```
- **Expected Outcome:**  
  215 items collected, 215 passed, 0 failed, 0 skipped, 0 warnings.  
  AST static scans confirm zero interpolation in core modules, fit calls restricted to training/preprocessing_fit, zero raw directory writes, and zero network calls.
- **Human Review Result:**  
  `[ ] PASS` &nbsp;&nbsp;&nbsp;&nbsp; `[ ] FAIL`  
  *Human Notes:*  
  *Date Checked:*  

---

### Check 4: Full Pipeline Master Audit Runner
- **Command:**  
  ```powershell
  python scripts/run_full_pipeline_check.py
  ```
- **Expected Outcome:**  
  Script executes all 9 verification steps and exits with code `0`. Generates `results/checks/full_check_<timestamp>.md`.
- **Human Review Result:**  
  `[ ] PASS` &nbsp;&nbsp;&nbsp;&nbsp; `[ ] FAIL`  
  *Human Notes:*  
  *Date Checked:*  

---

### Check 5: Real-Data Pipeline Determinism & Reproducibility
- **Command:**  
  ```powershell
  python scripts/check_real_reproducibility.py
  ```
- **Expected Outcome:**  
  Isolated run in a temporary directory produces 10/10 deterministic tabular artifacts (CSV quality, segments, audit tables, window index, features) that match the workspace bit-for-bit.
- **Human Review Result:**  
  `[ ] PASS` &nbsp;&nbsp;&nbsp;& | `[ ] FAIL`  
  *Human Notes:*  
  *Date Checked:*  

---

### Check 6: Policy & Protocol Gates Integrity
- **Command:**  
  ```powershell
  python -c "import yaml; d = yaml.safe_load(open('config/decisions.yaml'))['decisions']; print('D-01:', d['D-01']['status']); print('D-07:', d['D-07']['status']); print('D-09:', d['D-09']['status']); print('D-10:', d['D-10']['status'])"
  ```
- **Expected Outcome:**  
  Scientific policy gates `D-01` and `D-07` remain `PENDING` (confirming unapproved policies refuse to generate production labels or export). `D-09` and `D-10` remain explicitly `PROVISIONAL`.
- **Human Review Result:**  
  `[ ] PASS` &nbsp;&nbsp;&nbsp;&nbsp; `[ ] FAIL`  
  *Human Notes:*  
  *Date Checked:*  

---

### Check 7: Interactive Research Dashboard Functionality
- **Command:**  
  ```powershell
  streamlit run dashboard/app.py
  ```
- **Expected Outcome:**  
  Local Streamlit application launches cleanly on `http://localhost:8501`. Pages 1 through 7 display observation data, quality summaries, light curves, and pilot results in read-only mode without throwing exceptions.
- **Human Review Result:**  
  `[ ] PASS` &nbsp;&nbsp;&nbsp;&nbsp; `[ ] FAIL`  
  *Human Notes:*  
  *Date Checked:*  

---

### Check 8: Documentation and Scientific Limitations Completeness
- **Inspect Files:**  
  - `docs/00_requirements.md` through `docs/17_integration.md`
  - `docs/18_test_report.md`
  - `docs/19_reproducibility_checklist.md`
  - `docs/20_limitations.md`
  - `CHANGELOG.md`
- **Expected Outcome:**  
  All 11 mandatory scientific limitations are clearly articulated. Software tests are explicitly stated not to constitute scientific validation.
- **Human Review Result:**  
  `[ ] PASS` &nbsp;&nbsp;&nbsp;&nbsp; `[ ] FAIL`  
  *Human Notes:*  
  *Date Checked:*  

---

## 2. Final Acceptance Sign-Off

**Human Researcher / Reviewer Statement:**  
*I have personally executed the verification commands above, inspected the generated outputs and documentation, and confirm that the software pipeline meets the functional, architectural, and reproducibility requirements.*

- **Final Acceptance Determination:**  
  `[ ] ACCEPTED FOR SCIENTIFIC USE (Multi-day phase authorized)`  
  `[ ] PROVISIONALLY ACCEPTED (Action items required)`  
  `[ ] REJECTED (Defects must be addressed)`  

- **Reviewer Signature:** ________________________________________  
- **Reviewer Name:** ____________________________________________  
- **Affiliation:** ________________________________________________  
- **Date Signed:** _______________________________________________  
