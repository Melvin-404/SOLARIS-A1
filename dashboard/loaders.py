"""Artifact and data loaders for the SOLARIS-A1 Streamlit Dashboard (Stage 12).

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Strictly Read-Only: Loaders never write to data/raw, data/processed, or results.
2. Structured Response: Every loader returns LoadResult(data, status, message, source_path).
3. Status Codes: 'OK', 'MISSING', 'PROVISIONAL', 'PILOT', 'STALE', 'ERROR', 'EMPTY'.
4. UI Safety: Loaders never raise unhandled exceptions to the UI. Malformed or unparseable
   artifacts return status='ERROR' with actionable diagnostic details.
5. Separation of Concerns: Pure data extraction functions are decoupled from Streamlit
   caching decorators, allowing standalone automated testing without a running server.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
import yaml

from solar_flare.paths import project_root


@dataclass(frozen=True)
class LoadResult:
    """Standardized result envelope for all dashboard data loading operations."""

    data: Any
    status: str  # 'OK', 'MISSING', 'PROVISIONAL', 'PILOT', 'STALE', 'ERROR', 'EMPTY'
    message: str
    source_path: Optional[str] = None

    @property
    def is_ok(self) -> bool:
        return self.status in {"OK", "PROVISIONAL", "PILOT"}


def _resolve_root(root: Optional[Union[Path, str]] = None) -> Path:
    if root is not None:
        return Path(root)
    return project_root()


# ---------------------------------------------------------------------------
# Pure Loading Functions (Testable without Streamlit runtime)
# ---------------------------------------------------------------------------

def load_inventory_pure(root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load FITS inventory table from results/inventory/inventory.csv."""
    r = _resolve_root(root)
    inv_csv = r / "results" / "inventory" / "inventory.csv"
    if not inv_csv.is_file():
        return LoadResult(
            data=None,
            status="MISSING",
            message=f"Inventory table not found at {inv_csv}",
            source_path=str(inv_csv),
        )

    try:
        df = pd.read_csv(inv_csv)
        if df.empty:
            return LoadResult(data=df, status="EMPTY", message="Inventory file is empty.", source_path=str(inv_csv))
        return LoadResult(data=df, status="OK", message="Loaded inventory successfully.", source_path=str(inv_csv))
    except Exception as exc:
        return LoadResult(data=None, status="ERROR", message=f"Failed to parse inventory: {exc}", source_path=str(inv_csv))


def load_open_questions_pure(root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load unresolved questions from results/inventory/open_questions.md."""
    r = _resolve_root(root)
    q_file = r / "results" / "inventory" / "open_questions.md"
    if not q_file.is_file():
        return LoadResult(data="", status="MISSING", message="Open questions document not found.", source_path=str(q_file))
    try:
        text = q_file.read_text(encoding="utf-8")
        return LoadResult(data=text, status="OK", message="Loaded open questions.", source_path=str(q_file))
    except Exception as exc:
        return LoadResult(data="", status="ERROR", message=f"Error reading open questions: {exc}", source_path=str(q_file))


def load_quality_summary_pure(root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load data quality summary from results/quality/summary.csv."""
    r = _resolve_root(root)
    q_csv = r / "results" / "quality" / "summary.csv"
    if not q_csv.is_file():
        return LoadResult(data=None, status="MISSING", message="Quality summary table not found.", source_path=str(q_csv))

    try:
        df = pd.read_csv(q_csv)
        if df.empty:
            return LoadResult(data=df, status="EMPTY", message="Quality summary table is empty.", source_path=str(q_csv))
        return LoadResult(data=df, status="PROVISIONAL", message="Quality summary loaded (PROVISIONAL pending Gate G1).", source_path=str(q_csv))
    except Exception as exc:
        return LoadResult(data=None, status="ERROR", message=f"Error parsing quality summary: {exc}", source_path=str(q_csv))


def load_quality_report_pure(stem: Optional[str] = None, root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load quality report markdown for a specific file stem or overall."""
    r = _resolve_root(root)
    q_dir = r / "results" / "quality"
    if stem:
        rep_file = q_dir / f"{stem}_quality.md"
    else:
        rep_file = q_dir / "quality_report.md"

    if not rep_file.is_file():
        # Fallback to search any .md in results/quality/
        mds = list(q_dir.glob("*.md")) if q_dir.is_dir() else []
        if mds:
            rep_file = mds[0]
        else:
            return LoadResult(data="", status="MISSING", message="Quality report document not found.", source_path=str(rep_file))

    try:
        text = rep_file.read_text(encoding="utf-8")
        return LoadResult(data=text, status="PROVISIONAL", message="Quality report loaded (PROVISIONAL).", source_path=str(rep_file))
    except Exception as exc:
        return LoadResult(data="", status="ERROR", message=f"Failed to read quality report: {exc}", source_path=str(rep_file))


def load_column_roles_pure(root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load column roles specification from config/column_roles.yaml."""
    r = _resolve_root(root)
    roles_file = r / "config" / "column_roles.yaml"
    if not roles_file.is_file():
        return LoadResult(data={}, status="MISSING", message="Column roles configuration not found.", source_path=str(roles_file))
    try:
        content = yaml.safe_load(roles_file.read_text(encoding="utf-8")) or {}
        status = "PROVISIONAL"
        for v in content.values():
            if isinstance(v, dict) and v.get("status") == "PROVISIONAL":
                status = "PROVISIONAL"
                break
        return LoadResult(data=content, status=status, message="Column roles loaded.", source_path=str(roles_file))
    except Exception as exc:
        return LoadResult(data={}, status="ERROR", message=f"Error parsing column roles: {exc}", source_path=str(roles_file))


def load_decisions_pure(root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load architectural and scientific decisions from config/decisions.yaml."""
    r = _resolve_root(root)
    dec_file = r / "config" / "decisions.yaml"
    if not dec_file.is_file():
        return LoadResult(data={}, status="MISSING", message="Decisions log not found.", source_path=str(dec_file))
    try:
        content = yaml.safe_load(dec_file.read_text(encoding="utf-8")) or {}
        return LoadResult(data=content, status="OK", message="Decisions loaded.", source_path=str(dec_file))
    except Exception as exc:
        return LoadResult(data={}, status="ERROR", message=f"Error parsing decisions: {exc}", source_path=str(dec_file))


def load_policy_status_pure(root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Check labelling policy status in docs/08_labelling_policy.md and results/labels/."""
    r = _resolve_root(root)
    policy_md = r / "docs" / "08_labelling_policy.md"
    if not policy_md.is_file():
        return LoadResult(
            data={"status": "MISSING", "approved": False},
            status="MISSING",
            message="Labelling policy documentation not found.",
            source_path=str(policy_md),
        )

    try:
        text = policy_md.read_text(encoding="utf-8")
        approved = "STATUS: APPROVED" in text.upper()
        if approved:
            return LoadResult(
                data={"status": "APPROVED", "approved": True},
                status="OK",
                message="Labelling policy is formally APPROVED by human researcher.",
                source_path=str(policy_md),
            )
        else:
            return LoadResult(
                data={"status": "DRAFT", "approved": False},
                status="PROVISIONAL",
                message="Labelling policy is DRAFT (NOT APPROVED — no labelled dataset should be interpreted).",
                source_path=str(policy_md),
            )
    except Exception as exc:
        return LoadResult(
            data={"status": "ERROR", "approved": False},
            status="ERROR",
            message=f"Error reading policy: {exc}",
            source_path=str(policy_md),
        )


def load_eda_candidates_pure(stem: Optional[str] = None, root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load candidate burst intervals from results/eda/candidate_bursts.csv."""
    r = _resolve_root(root)
    burst_csv = r / "results" / "eda" / "candidate_bursts.csv"
    if not burst_csv.is_file():
        return LoadResult(data=None, status="MISSING", message="Candidate bursts table not found.", source_path=str(burst_csv))
    try:
        df = pd.read_csv(burst_csv)
        if df.empty:
            return LoadResult(data=df, status="EMPTY", message="Candidate bursts table is empty.", source_path=str(burst_csv))
        # Ensure status column is set to CANDIDATE — UNVERIFIED
        if "status" not in df.columns:
            df["status"] = "CANDIDATE — UNVERIFIED"
        return LoadResult(data=df, status="OK", message="Loaded candidate burst intervals (UNVERIFIED).", source_path=str(burst_csv))
    except Exception as exc:
        return LoadResult(data=None, status="ERROR", message=f"Error parsing candidate bursts: {exc}", source_path=str(burst_csv))


def load_segments_pure(stem: Optional[str] = None, root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load segmentation summary or segment files."""
    r = _resolve_root(root)
    seg_summary = r / "results" / "preprocessing" / "segment_summary.csv"
    if seg_summary.is_file():
        try:
            df = pd.read_csv(seg_summary)
            return LoadResult(data=df, status="PROVISIONAL", message="Loaded segmentation summary.", source_path=str(seg_summary))
        except Exception as exc:
            return LoadResult(data=None, status="ERROR", message=f"Error loading segment summary: {exc}", source_path=str(seg_summary))

    # Check data/processed/segments/
    seg_dir = r / "data" / "processed" / "segments"
    if seg_dir.is_dir():
        files = list(seg_dir.glob("*/*.csv"))
        if files:
            return LoadResult(data={"segment_files": [str(f) for f in files]}, status="OK", message=f"Found {len(files)} segment files.", source_path=str(seg_dir))

    return LoadResult(data=None, status="MISSING", message="No segmentation outputs found.", source_path=str(seg_dir))


def load_feature_index_pure(stem: Optional[str] = None, root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load window index from data/processed/features/<stem>/window_index.csv."""
    r = _resolve_root(root)
    feat_base = r / "data" / "processed" / "features"
    idx_file = None
    if stem:
        idx_file = feat_base / stem / "window_index.csv"
    else:
        found = list(feat_base.glob("*/window_index.csv"))
        if found:
            idx_file = found[0]

    if not idx_file or not idx_file.is_file():
        return LoadResult(data=None, status="MISSING", message="Window index table not found.", source_path=str(idx_file or feat_base))

    try:
        df = pd.read_csv(idx_file)
        if df.empty:
            return LoadResult(data=df, status="EMPTY", message="Window index is empty.", source_path=str(idx_file))
        return LoadResult(data=df, status="OK", message="Loaded window index table.", source_path=str(idx_file))
    except Exception as exc:
        return LoadResult(data=None, status="ERROR", message=f"Error parsing window index: {exc}", source_path=str(idx_file))


def load_feature_table_pure(stem: Optional[str] = None, root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load feature table from data/processed/features/<stem>/window_features.csv or features.csv."""
    r = _resolve_root(root)
    feat_base = r / "data" / "processed" / "features"
    feat_file = None
    target_stem = stem

    if stem:
        candidates = [
            feat_base / stem / "window_features.csv",
            feat_base / stem / "features.csv",
        ]
        for c in candidates:
            if c.is_file():
                feat_file = c
                break
    else:
        found = list(feat_base.glob("*/window_features.csv")) + list(feat_base.glob("*/features.csv"))
        if found:
            feat_file = found[0]
            target_stem = feat_file.parent.name

    if not feat_file or not feat_file.is_file():
        return LoadResult(data=None, status="MISSING", message="Feature table not found.", source_path=str(feat_file or feat_base))

    try:
        df = pd.read_csv(feat_file)
        if df.empty:
            return LoadResult(data=df, status="EMPTY", message="Feature table is empty.", source_path=str(feat_file))

        # Check STALE: compare build_log parameters against current config/default.yaml
        if target_stem:
            build_log_file = r / "results" / "features" / target_stem / "build_log.json"
            cfg_file = r / "config" / "default.yaml"
            if build_log_file.is_file() and cfg_file.is_file():
                try:
                    b_data = json.loads(build_log_file.read_text(encoding="utf-8"))
                    rec_w = b_data.get("parameters", {}).get("window_seconds")
                    c_data = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}
                    curr_w = c_data.get("features", {}).get("window_length_seconds")
                    if rec_w is not None and curr_w is not None and float(rec_w) != float(curr_w):
                        return LoadResult(
                            data=df,
                            status="STALE",
                            message=f"STALE FEATURE ARTIFACT: Recorded window_length={rec_w}s, current config={curr_w}s.",
                            source_path=str(feat_file),
                        )
                except Exception:
                    pass

        return LoadResult(data=df, status="OK", message="Loaded feature table.", source_path=str(feat_file))
    except Exception as exc:
        return LoadResult(data=None, status="ERROR", message=f"Error parsing feature table: {exc}", source_path=str(feat_file))


def load_dataset_status_pure(task: str = "detection", root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load exported dataset status from results/exports/."""
    r = _resolve_root(root)
    exp_dir = r / "results" / "exports"
    blocked_file = exp_dir / f"BLOCKED_{task.upper()}.md"
    log_file = exp_dir / "export_log.json"

    if blocked_file.is_file():
        text = blocked_file.read_text(encoding="utf-8")
        return LoadResult(
            data={"status": "BLOCKED", "report": text},
            status="BLOCKED",
            message=f"Stage 9 export for task '{task}' is BLOCKED pending human gate approval.",
            source_path=str(blocked_file),
        )

    # Check for exported datasets
    ds_dir = r / "data" / "processed" / "datasets" / task
    if ds_dir.is_dir() and any(ds_dir.iterdir()):
        export_dirs = [d for d in ds_dir.iterdir() if d.is_dir()]
        if export_dirs:
            exp_id = export_dirs[0].name
            # Under Decision D-15, single-day observation datasets are PILOT
            return LoadResult(
                data={"status": "PILOT", "export_id": exp_id, "task": task},
                status="PILOT",
                message=f"Dataset exported under PILOT status (single observation date).",
                source_path=str(export_dirs[0]),
            )

    if log_file.is_file():
        try:
            log_data = json.loads(log_file.read_text(encoding="utf-8"))
            return LoadResult(data=log_data, status="OK", message="Dataset export completed.", source_path=str(log_file))
        except Exception as exc:
            return LoadResult(data=None, status="ERROR", message=f"Failed to parse export log: {exc}", source_path=str(log_file))

    return LoadResult(data=None, status="MISSING", message=f"Dataset not yet available for task '{task}'. See docs/data_acquisition.md.", source_path=str(exp_dir))


def load_experiments_pure(root: Optional[Union[Path, str]] = None) -> LoadResult:
    """List available experiment runs from results/experiments/ with lock & manifest checks."""
    r = _resolve_root(root)
    exp_base = r / "results" / "experiments"
    if not exp_base.is_dir():
        return LoadResult(data=[], status="MISSING", message="Experiments directory does not exist.", source_path=str(exp_base))

    subdirs = [d for d in exp_base.iterdir() if d.is_dir() and (d / "run_manifest.json").is_file()]
    if not subdirs:
        return LoadResult(data=[], status="EMPTY", message="No completed experiment directories found.", source_path=str(exp_base))

    from solar_flare.integrity import verify_test_lock_integrity

    exp_records = []
    for d in subdirs:
        try:
            manifest = json.loads((d / "run_manifest.json").read_text(encoding="utf-8"))
            lock_res = verify_test_lock_integrity(d)
            status_val = manifest.get("status", "UNKNOWN")
            if lock_res.status in {"MISMATCH", "ERROR"}:
                status_val = "ERROR"

            exp_records.append({
                "experiment_id": d.name,
                "status": status_val,
                "protocol_id": manifest.get("protocol_id", "UNKNOWN"),
                "dataset_export_id": manifest.get("dataset_export_id", "UNKNOWN"),
                "lock_status": lock_res.status,
                "lock_message": lock_res.message,
                "path": str(d),
            })
        except Exception:
            exp_records.append({
                "experiment_id": d.name,
                "status": "UNPARSEABLE",
                "protocol_id": "UNKNOWN",
                "lock_status": "ERROR",
                "path": str(d),
            })

    return LoadResult(data=exp_records, status="OK", message=f"Found {len(exp_records)} experiment runs.", source_path=str(exp_base))


def load_evaluation_report_pure(experiment_id: str, root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load evaluation report for a given experiment."""
    r = _resolve_root(root)
    eval_dir = r / "results" / "experiments" / experiment_id / "evaluation"
    rep_md = eval_dir / "evaluation_report.md"
    rep_json = eval_dir / "evaluation_report.json"

    if not rep_md.is_file() and not rep_json.is_file():
        return LoadResult(
            data=None,
            status="MISSING",
            message=f"Evaluation report not found for experiment '{experiment_id}'.",
            source_path=str(eval_dir),
        )

    try:
        report_text = rep_md.read_text(encoding="utf-8") if rep_md.is_file() else ""
        report_data = json.loads(rep_json.read_text(encoding="utf-8")) if rep_json.is_file() else {}
        return LoadResult(
            data={"markdown": report_text, "json": report_data},
            status="OK",
            message="Evaluation report loaded.",
            source_path=str(eval_dir),
        )
    except Exception as exc:
        return LoadResult(data=None, status="ERROR", message=f"Failed to read evaluation report: {exc}", source_path=str(eval_dir))


def load_metrics_pure(experiment_id: str, root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load evaluation metrics CSV for an experiment."""
    r = _resolve_root(root)
    m_csv = r / "results" / "experiments" / experiment_id / "evaluation" / "metrics.csv"
    if not m_csv.is_file():
        return LoadResult(data=None, status="MISSING", message="Metrics CSV not found.", source_path=str(m_csv))
    try:
        df = pd.read_csv(m_csv)
        return LoadResult(data=df, status="OK", message="Loaded metrics table.", source_path=str(m_csv))
    except Exception as exc:
        return LoadResult(data=None, status="ERROR", message=f"Failed to read metrics CSV: {exc}", source_path=str(m_csv))


def load_light_curve_pure(stem: str = "AL1_SOLEXS_20261018_SDD2_L1", root: Optional[Union[Path, str]] = None) -> LoadResult:
    """Load light-curve time series data (read-only) from raw FITS or quality extraction."""
    r = _resolve_root(root)
    raw_lc_gz = r / "data" / "raw" / f"{stem}.lc.gz"
    raw_lc = r / "data" / "raw" / f"{stem}.lc"
    target_fits = raw_lc_gz if raw_lc_gz.is_file() else (raw_lc if raw_lc.is_file() else None)

    if not target_fits:
        return LoadResult(data=None, status="MISSING", message=f"Light-curve FITS file not found for {stem}.", source_path=str(raw_lc_gz))

    try:
        from astropy.io import fits
        with fits.open(target_fits, memmap=True) as hdul:
            # Table is typically at HDU 1
            table_hdu = None
            for hdu in hdul:
                if hdu.data is not None and hasattr(hdu.data, "names") and hdu.data.names:
                    table_hdu = hdu
                    break

            if table_hdu is None:
                return LoadResult(data=None, status="EMPTY", message="No tabular data found in FITS file.", source_path=str(target_fits))

            colnames = [c.lower() for c in table_hdu.data.names]
            time_col = next((c for c in table_hdu.data.names if "time" in c.lower()), table_hdu.data.names[0])
            count_col = next((c for c in table_hdu.data.names if any(k in c.lower() for k in ["rate", "count", "flux"])), table_hdu.data.names[1])

            times = np.array(table_hdu.data[time_col], dtype=float)
            counts = np.array(table_hdu.data[count_col], dtype=float)

            df = pd.DataFrame({"time": times, "counts": counts})

            # Check raw hash against Stage 7 audit
            audit_hash_file = r / "results" / "preprocessing" / "raw_hashes_before.json"
            if audit_hash_file.is_file():
                try:
                    rec_hashes = json.loads(audit_hash_file.read_text(encoding="utf-8"))
                    rel_key = f"data/raw/{target_fits.name}"
                    if rel_key in rec_hashes:
                        rec_hash = rec_hashes[rel_key]
                        from solar_flare.integrity import compute_sha256
                        curr_hash = compute_sha256(target_fits)
                        if curr_hash != rec_hash:
                            return LoadResult(
                                data=df,
                                status="ERROR",
                                message=f"RAW DATA HASH MISMATCH for {target_fits.name}! Recorded={rec_hash[:8]}..., Current={curr_hash[:8]}...",
                                source_path=str(target_fits),
                            )
                except Exception:
                    pass

            return LoadResult(data=df, status="OK", message=f"Loaded light curve ({len(df)} samples).", source_path=str(target_fits))
    except Exception as exc:
        return LoadResult(data=None, status="ERROR", message=f"Error reading FITS light curve: {exc}", source_path=str(target_fits))


# ---------------------------------------------------------------------------
# Streamlit Caching Wrappers (Instantiated when Streamlit is available)
# ---------------------------------------------------------------------------

try:
    import streamlit as st

    @st.cache_data(show_spinner=False)
    def load_inventory() -> LoadResult:
        return load_inventory_pure()

    @st.cache_data(show_spinner=False)
    def load_open_questions() -> LoadResult:
        return load_open_questions_pure()

    @st.cache_data(show_spinner=False)
    def load_quality_summary() -> LoadResult:
        return load_quality_summary_pure()

    @st.cache_data(show_spinner=False)
    def load_quality_report(stem: Optional[str] = None) -> LoadResult:
        return load_quality_report_pure(stem)

    @st.cache_data(show_spinner=False)
    def load_column_roles() -> LoadResult:
        return load_column_roles_pure()

    @st.cache_data(show_spinner=False)
    def load_decisions() -> LoadResult:
        return load_decisions_pure()

    @st.cache_data(show_spinner=False)
    def load_policy_status() -> LoadResult:
        return load_policy_status_pure()

    @st.cache_data(show_spinner=False)
    def load_eda_candidates(stem: Optional[str] = None) -> LoadResult:
        return load_eda_candidates_pure(stem)

    @st.cache_data(show_spinner=False)
    def load_segments(stem: Optional[str] = None) -> LoadResult:
        return load_segments_pure(stem)

    @st.cache_data(show_spinner=False)
    def load_feature_index(stem: Optional[str] = None) -> LoadResult:
        return load_feature_index_pure(stem)

    @st.cache_data(show_spinner=False)
    def load_feature_table(stem: Optional[str] = None) -> LoadResult:
        return load_feature_table_pure(stem)

    @st.cache_data(show_spinner=False)
    def load_dataset_status(task: str = "detection") -> LoadResult:
        return load_dataset_status_pure(task)

    @st.cache_data(show_spinner=False)
    def load_experiments() -> LoadResult:
        return load_experiments_pure()

    @st.cache_data(show_spinner=False)
    def load_evaluation_report(experiment_id: str) -> LoadResult:
        return load_evaluation_report_pure(experiment_id)

    @st.cache_data(show_spinner=False)
    def load_metrics(experiment_id: str) -> LoadResult:
        return load_metrics_pure(experiment_id)

    @st.cache_data(show_spinner=False)
    def load_light_curve(stem: str = "AL1_SOLEXS_20261018_SDD2_L1") -> LoadResult:
        return load_light_curve_pure(stem)

except ImportError:
    # Fallback to direct pure functions if Streamlit is not installed or outside app context
    load_inventory = load_inventory_pure
    load_open_questions = load_open_questions_pure
    load_quality_summary = load_quality_summary_pure
    load_quality_report = load_quality_report_pure
    load_column_roles = load_column_roles_pure
    load_decisions = load_decisions_pure
    load_policy_status = load_policy_status_pure
    load_eda_candidates = load_eda_candidates_pure
    load_segments = load_segments_pure
    load_feature_index = load_feature_index_pure
    load_feature_table = load_feature_table_pure
    load_dataset_status = load_dataset_status_pure
    load_experiments = load_experiments_pure
    load_evaluation_report = load_evaluation_report_pure
    load_metrics = load_metrics_pure
    load_light_curve = load_light_curve_pure
