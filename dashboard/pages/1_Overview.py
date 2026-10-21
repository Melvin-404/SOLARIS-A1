"""Page 1: Project Overview, Pipeline Status & Scientific Stage Summary."""

from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import streamlit as st

from dashboard.loaders import load_inventory, load_open_questions
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from solar_flare.paths import project_root
from solar_flare.status import pipeline_status

st.set_page_config(page_title="Overview | SOLARIS-A1", page_icon="📋", layout="wide")
render_sidebar_disclaimer()

st.title("📋 Project Overview & Pipeline Integration Status")
st.caption("Active lifecycle status, artifact lineage verification, and open scientific questions")

root = project_root()

# 1. Action Bar: Cache Reload & File-System Timestamp
col_btn, col_time = st.columns([1, 2])
with col_btn:
    if st.button("🔄 Reload Artefacts (Clear Cache)"):
        st.cache_data.clear()
        st.rerun()

# Compute latest artefact generation time (max mtime across results/)
results_dir = root / "results"
latest_mtime = 0.0
if results_dir.is_dir():
    for f in results_dir.rglob("*"):
        if f.is_file():
            try:
                mt = f.stat().st_mtime
                if mt > latest_mtime:
                    latest_mtime = mt
            except Exception:
                pass

with col_time:
    if latest_mtime > 0:
        dt_str = datetime.fromtimestamp(latest_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        st.caption(f"🕒 **Last Artefact Generation Time:** `{dt_str}` (file-system time)")
    else:
        st.caption("🕒 **Last Artefact Generation Time:** N/A")

st.markdown("---")

# 2. Pipeline Stage Status Table (Pure status evaluation)
st.header("1. Pipeline Lifecycle Stages Status (Stages 3–11)")
status_rep = pipeline_status(root)
status_rows = []
for s in status_rep.stages:
    status_rows.append({
        "Stage": s.stage_id,
        "Name": s.stage_name,
        "Status": s.status,
        "Gate": s.gate_id or "-",
        "Details & Diagnostics": s.reason,
    })

df_status = pd.DataFrame(status_rows)
st.dataframe(df_status, use_container_width=True)

st.markdown("---")

# 3. Inventory Summary
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

# 4. Open Scientific Questions
st.header("3. Unresolved Questions & Decision Log Register")
q_res = load_open_questions()

if q_res.status == "MISSING":
    st.info("No open questions file found at results/inventory/open_questions.md.")
elif q_res.status == "ERROR":
    render_status_banner("ERROR", q_res.message, "Open Questions")
else:
    lines = q_res.data.splitlines()
    q_count = sum(1 for line in lines if line.strip().startswith("## Q") or "Question" in line)
    st.metric("Open Questions Flagged", q_count if q_count > 0 else "Documented")
    with st.expander("View open_questions.md Document"):
        st.markdown(q_res.data)
