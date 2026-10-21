"""Page 1: Project Overview & Scientific Stage Summary."""

import streamlit as st
from dashboard.loaders import load_inventory, load_open_questions
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner

st.set_page_config(page_title="Overview | SOLARIS-A1", page_icon="📋", layout="wide")
render_sidebar_disclaimer()

st.title("📋 Project Overview & Repository Status")
st.caption("Current scientific stage, inventory summary, and open scientific questions")

# 1. Project Stage
st.header("1. Active Implementation Lifecycle Stage")
st.markdown(
    """
    - **Current Milestone:** **Stage 12 — Streamlit Dashboard Foundation**
    - **Upstream Stage Status:** Stages 0 through 11 fully implemented with 179 passing automated tests.
    - **Dataset Classification:** **PILOT (Single Observation Day: 2026-10-18)** under Decision D-15.
    - **Human Approval Gates:**
      - Gate G1/G2 (Data Quality & Column Roles): PROVISIONAL.
      - Gate G3 (Labelling Policy): DRAFT (Awaiting Human Approval).
      - Gate G7 (Training Protocol Freeze): DRAFT.
      - Gate G8 (Single-Shot Test Evaluation): PENDING.
    """
)

st.markdown("---")

# 2. Inventory Summary
st.header("2. FITS Data Inventory Summary")
inv_res = load_inventory()

if inv_res.status == "MISSING":
    render_status_banner("MISSING", inv_res.message, "Inventory")
elif inv_res.status == "ERROR":
    render_status_banner("ERROR", inv_res.message, "Inventory")
elif inv_res.status == "EMPTY":
    render_status_banner("EMPTY", inv_res.message, "Inventory")
else:
    df = inv_res.data
    n_files = len(df)
    file_types = df["product_type"].unique().tolist() if "product_type" in df.columns else []
    obs_ids = df["observation_id"].unique().tolist() if "observation_id" in df.columns else []

    col1, col2, col3 = st.columns(3)
    col1.metric("Total FITS Files", n_files)
    col2.metric("Product Types", ", ".join(str(t) for t in file_types) if file_types else "N/A")
    col3.metric("Observation Date", "2026-10-18" if obs_ids else "N/A")

    st.markdown("### Inventory Records")
    st.dataframe(df, use_container_width=True)

st.markdown("---")

# 3. Open Scientific Questions
st.header("3. Unresolved Questions & Decision Log Register")
q_res = load_open_questions()

if q_res.status == "MISSING":
    st.info("No open questions file found at results/inventory/open_questions.md.")
elif q_res.status == "ERROR":
    render_status_banner("ERROR", q_res.message, "Open Questions")
else:
    # Count open questions (e.g. lines with '## ' or 'Q-')
    lines = q_res.data.splitlines()
    q_count = sum(1 for line in lines if line.strip().startswith("## Q") or "Question" in line)
    st.metric("Open Questions Flagged", q_count if q_count > 0 else "Documented")
    with st.expander("View open_questions.md Document"):
        st.markdown(q_res.data)
