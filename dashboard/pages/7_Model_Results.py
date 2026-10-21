"""Page 7: Model Training, Validation Tuning & Single-Shot Test Evaluation."""

from pathlib import Path
import json
import pandas as pd
import streamlit as st

from dashboard.loaders import (
    load_experiments,
    load_metrics,
    load_evaluation_report,
)
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from solar_flare.paths import project_root
from solar_flare.modelling.lock import verify_lock

st.set_page_config(page_title="Model Results | SOLARIS-A1", page_icon="🤖", layout="wide")
render_sidebar_disclaimer()

st.title("🤖 Model Training, Validation Selection & Test Evaluation")
st.caption("Protocol-governed hyperparameter tuning (validation data only) and single-shot sealed test evaluation")

# 1. Load Experiments
exp_res = load_experiments()

if not exp_res.is_ok or not exp_res.data:
    st.info(
        "ℹ️ **No experiment results found. "
        "Model training is run by the automated training script under an approved protocol. "
        "This page displays results only when valid artifacts exist.**"
    )
    st.markdown(
        """
        ### Current Pipeline Gate Status
        - **Gate G7 Status:** `DRAFT` (Awaiting human researcher protocol freeze).
        - **Stage 10 Training:** Blocked pending Gate G7. See `results/experiments/AWAITING_G7.md`.
        - **Stage 11 Evaluation:** Blocked pending Gate G8. See `results/experiments/AWAITING_G8.md`.
        """
    )
    st.stop()

experiments = exp_res.data
exp_ids = [e["experiment_id"] for e in experiments]
selected_exp_id = st.selectbox("Select Experiment Run", exp_ids)
target_exp = next(e for e in experiments if e["experiment_id"] == selected_exp_id)

st.markdown(f"**Experiment Status:** `{target_exp['status']}` | **Protocol:** `{target_exp['protocol_id']}`")

st.markdown("---")

# 2. Validation Selection Results (Labeled STRICTLY 'VALIDATION ONLY')
st.header("1. Validation-Only Model Selection Results")
st.warning("⚠️ **VALIDATION ONLY**: The metrics below were computed on validation partitions during hyperparameter tuning.")

root = project_root()
exp_dir = root / "results" / "experiments" / selected_exp_id
trials_csv = exp_dir / "selection" / "trials.csv"

if trials_csv.is_file():
    try:
        df_trials = pd.read_csv(trials_csv)
        st.dataframe(df_trials, use_container_width=True)
    except Exception as exc:
        render_status_banner("ERROR", f"Failed to parse selection trials: {exc}", "Selection Trials")
else:
    st.info("No validation selection trials.csv found for this experiment run.")

st.markdown("---")

# 3. Single-Shot Test Evaluation Results
st.header("2. Single-Shot Sealed Test Set Evaluation")

sealed_dir = exp_dir / "sealed"
eval_dir = exp_dir / "evaluation"
from solar_flare.integrity import verify_test_lock_integrity
lock_check = verify_test_lock_integrity(exp_dir)

if lock_check.status != "OK":
    st.error(f"🚨 **Test Set Cryptographic Lock Verification Failed:** {lock_check.message}")
    if lock_check.recorded_value and lock_check.current_value:
        st.caption(f"Recorded SHA-256: `{lock_check.recorded_value}` | Current SHA-256: `{lock_check.current_value}`")
    st.info("Test evaluation results cannot be displayed due to lock integrity failure.")
elif not eval_dir.is_dir():
    st.info("ℹ️ **Test evaluation not available or not attested.** (Stage 11 test evaluation has not yet been executed).")
else:
    # Load and display metrics table
    m_res = load_metrics(selected_exp_id)
    if m_res.is_ok and isinstance(m_res.data, pd.DataFrame):
        st.success("✅ **Test Set Cryptographic Lock Verified (Single-Shot Evaluation Attested).**")
        st.markdown("### Test Performance Metrics Table")
        st.dataframe(m_res.data, use_container_width=True)

    # Load and display evaluation report markdown
    rep_res = load_evaluation_report(selected_exp_id)
    if rep_res.is_ok and isinstance(rep_res.data, dict):
        md_text = rep_res.data.get("markdown", "")
        if md_text:
            with st.expander("📄 View Full Scientific Evaluation Report (Stage 11)", expanded=True):
                st.markdown(md_text)
