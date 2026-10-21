"""Page 6: Sliding Windows, Feature Engineering & Causal Dictionary."""

from pathlib import Path
import pandas as pd
import streamlit as st

from dashboard.loaders import (
    load_feature_index,
    load_feature_table,
)
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from dashboard.components.figures import build_feature_histogram
from solar_flare.paths import project_root

st.set_page_config(page_title="Features | SOLARIS-A1", page_icon="🧬", layout="wide")
render_sidebar_disclaimer()

st.title("🧬 Sliding Windows & Causal Feature Engineering (Stage 8)")
st.caption("Causal feature extraction within continuous segments, window coverage, and leakage warnings")

# 1. Critical Methodological Warning
st.error(
    "🚨 **CRITICAL METHODOLOGICAL WARNING — OVERLAPPING WINDOW LEAKAGE**\n\n"
    "Sliding windows with length $W = 60\\text{ s}$ and stride $S = 10\\text{ s}$ share **83.3% of raw observations** with adjacent windows. "
    "**Random row-level splitting is strictly prohibited**, as it leaks identical temporal fluctuations across training and test sets. "
    "All partitioning must be chronological with temporal embargo buffers or event-grouped by continuous segment."
)

st.markdown("---")

# 2. Window Index Browser
st.header("1. Sliding Window Index Browser")
idx_res = load_feature_index()

if idx_res.status == "MISSING":
    st.info("No window index table found. Run Stage 8 feature extraction to generate sliding windows.")
elif idx_res.status == "ERROR":
    render_status_banner("ERROR", idx_res.message, "Window Index")
elif idx_res.status == "EMPTY":
    st.info("Window index table is empty.")
else:
    df_idx = idx_res.data
    st.markdown(f"**Total Generated Windows:** {len(df_idx)}")
    st.dataframe(df_idx.head(500), use_container_width=True)
    if len(df_idx) > 500:
        st.caption(f"Showing first 500 of {len(df_idx)} window records.")

st.markdown("---")

# 3. Engineered Features Distribution
st.header("2. Feature Value Distributions")
feat_res = load_feature_table()

if feat_res.status == "MISSING":
    st.info("No feature table found. Run Stage 8 feature extraction to compute causal features.")
elif feat_res.status == "ERROR":
    render_status_banner("ERROR", feat_res.message, "Feature Table")
elif feat_res.status == "EMPTY":
    st.info("Feature table is empty.")
else:
    df_feat = feat_res.data
    feature_cols = [c for c in df_feat.columns if c not in {"window_id", "segment_id", "timestamp"}]

    if feature_cols:
        col_sel, col_bins = st.columns([2, 1])
        with col_sel:
            selected_feat = st.selectbox("Select Feature to Inspect", feature_cols)
        with col_bins:
            nbins = st.slider("Histogram Bins", min_value=10, max_value=100, value=40)

        fig_hist = build_feature_histogram(df_feat, selected_feat, nbins=nbins)
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("No numerical feature columns found in table.")

st.markdown("---")

# 4. Feature Dictionary Documentation
st.header("3. Causal Feature Dictionary (Stage 8)")
root = project_root()
dict_file = root / "docs" / "11_feature_dictionary.md"

if dict_file.is_file():
    with st.expander("📖 View docs/11_feature_dictionary.md Specification", expanded=False):
        st.markdown(dict_file.read_text(encoding="utf-8"))
else:
    st.info("Feature dictionary document not found at docs/11_feature_dictionary.md.")
