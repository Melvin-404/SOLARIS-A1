"""Page 3: Data Quality Characterisation & Quality Metrics."""

from pathlib import Path
import streamlit as st
from dashboard.loaders import (
    load_quality_summary,
    load_column_roles,
)
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from solar_flare.paths import project_root

st.set_page_config(page_title="Data Quality | SOLARIS-A1", page_icon="🛡️", layout="wide")
render_sidebar_disclaimer()

st.title("🛡️ Data Quality Assessment (Stage 4)")
st.caption("Pure functional quality diagnostics, cadence distributions, sample segregation, and column-role evidence")

# 1. Column Role Prominent Status Banner
st.header("1. Scientific Column Role Status")
roles_res = load_column_roles()
if roles_res.status == "PROVISIONAL":
    render_status_banner(
        "PROVISIONAL",
        "Column roles are PROVISIONAL pending Gate G1/G2 confirmation. No data was mutated, clipped, or filtered.",
        "Gate G1/G2",
    )
elif roles_res.status == "OK":
    render_status_banner("OK", "Column roles are formally CONFIRMED by human researcher.", "Gate G1/G2")
else:
    render_status_banner("MISSING", "Column roles specification not found.", "Gate G1/G2")

st.markdown("---")

# 2. Quality Summary Table
st.header("2. Observation Quality Summary Table")
q_res = load_quality_summary()

if q_res.status == "MISSING":
    render_status_banner("MISSING", q_res.message, "Quality Summary")
elif q_res.status == "ERROR":
    render_status_banner("ERROR", q_res.message, "Quality Summary")
elif q_res.status == "EMPTY":
    render_status_banner("EMPTY", q_res.message, "Quality Summary")
else:
    st.dataframe(q_res.data, use_container_width=True)

st.markdown("---")

# 3. Per-File Detailed Quality Inspection & Visualizations
st.header("3. Per-File Diagnostics and Quality Figures")

root = project_root()
q_base = root / "results" / "quality"
subdirs = [d for d in q_base.iterdir() if d.is_dir()] if q_base.is_dir() else []

if not subdirs:
    st.info("No detailed per-file quality directories found under results/quality/.")
else:
    selected_dir = st.selectbox("Select Analyzed File", [d.name for d in subdirs])
    target_dir = q_base / selected_dir

    col_md, col_figs = st.columns([1, 1])

    with col_md:
        st.subheader("Quality Audit Report")
        q_md_file = target_dir / "quality.md"
        if q_md_file.is_file():
            st.markdown(q_md_file.read_text(encoding="utf-8"))
        else:
            st.info("quality.md not found in selected directory.")

    with col_figs:
        st.subheader("Quality Diagnostic Figures")
        figs = [
            ("cadence_histogram.png", "Time Cadence Distribution"),
            ("count_distribution.png", "Count Rate Histogram"),
            ("time_coverage.png", "Observation Coverage Timeline"),
            ("flagged_samples.png", "Segregated Flagged & Non-Finite Samples"),
        ]

        for fig_name, fig_label in figs:
            p = target_dir / fig_name
            if p.is_file():
                st.image(str(p), caption=fig_label, use_container_width=True)
            else:
                st.caption(f"Figure '{fig_name}' not generated.")
