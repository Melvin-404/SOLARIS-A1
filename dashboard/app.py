"""SOLARIS-A1 Streamlit Dashboard Entrypoint (Stage 12).

Machine Learning-Based Solar Flare Detection and Pre-Flare Activity Analysis
Using Aditya-L1 SoLEXS Observations.
"""

import sys
from pathlib import Path
import streamlit as st

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from dashboard.loaders import (
    load_inventory,
    load_quality_summary,
    load_policy_status,
    load_decisions,
    load_experiments,
)
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner

# Configure wide layout
st.set_page_config(
    page_title="SOLARIS-A1: Solar Flare Analysis Dashboard",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar disclaimer
render_sidebar_disclaimer()

st.title("☀️ SOLARIS-A1: Solar Flare Detection and Pre-Flare Activity Analysis")
st.caption("Aditya-L1 SoLEXS Level-1 Science Observation and Machine Learning Pipeline")

st.markdown("---")

# 1. Research Framing: Distinct Tasks
st.header("1. Research Framing & Task Separation")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Task A: Current-Window Flare Detection")
    st.markdown(
        """
        - **Objective:** Determine whether solar flare activity is occurring in a defined observation window ($W = 60\\text{ s}$).
        - **Input:** Causal summary and morphological features extracted from Level-1 X-ray count rates.
        - **Ground Truth:** Independently verified flare events from documented external catalogues.
        - **Key Challenge:** Extreme class imbalance (flares are rare transients; quiet Sun accounts for $>95\\%$ of time).
        """
    )

with col_b:
    st.subheader("Task B: Pre-Flare Activity Forecasting")
    st.markdown(
        """
        - **Objective:** Predict whether an independently verified flare onset will occur within a future horizon.
        - **Input:** Features computed strictly using samples prior to the prediction reference time ($t \\le t_0$).
        - **Critical Scientific Governance:** **Task B is a forecasting experiment.** 
          *Detection performance (Task A) does NOT establish forecasting skill (Task B).*
          Forecasting skill requires outperforming both climatological (training prevalence) and persistence baselines.
        """
    )

st.markdown("---")

# 2. Labelling Policy & Governance Status
st.header("2. Scientific Policy Status (Gate G3)")
policy_res = load_policy_status()
if policy_res.data.get("approved"):
    render_status_banner("OK", "Labelling policy is formally APPROVED by the human researcher.", "Gate G3")
else:
    render_status_banner(
        "PROVISIONAL",
        "Labelling policy status is DRAFT (NOT APPROVED — no labelled dataset should be scientifically interpreted).",
        "Gate G3",
    )

st.markdown("---")

# 3. Artifact Readiness Panel
st.header("3. Pipeline Artifacts Readiness Panel")

inv_res = load_inventory()
qual_res = load_quality_summary()
exp_res = load_experiments()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("FITS Inventory", "OK" if inv_res.is_ok else "MISSING")
    st.caption(inv_res.message)

with col2:
    st.metric("Data Quality Summary", "PROVISIONAL" if qual_res.status == "PROVISIONAL" else qual_res.status)
    st.caption(qual_res.message)

with col3:
    st.metric("Labelling Policy", "APPROVED" if policy_res.data.get("approved") else "DRAFT")
    st.caption("Awaiting human approval at G3")

with col4:
    st.metric("Trained Experiments", f"{len(exp_res.data)}" if exp_res.is_ok else "0")
    st.caption(exp_res.message)

st.markdown("---")
st.info("👈 Use the sidebar navigation to explore Overview, Raw Data, Quality, Light Curves, Candidate Events, Features, and Model Results.")
