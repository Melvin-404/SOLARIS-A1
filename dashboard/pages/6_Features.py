"""Page 6: Sliding Windows, Feature Engineering & Causal Dictionary."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

from dashboard.loaders import (
    load_feature_index,
    load_feature_table,
)
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from dashboard.components.figures import build_feature_histogram
from dashboard.components.theme import apply_space_weather_theme, render_source_badge
from solar_flare.paths import project_root

st.set_page_config(page_title="Features | SOLARIS-A1", page_icon="🧬", layout="wide")
apply_space_weather_theme()
render_sidebar_disclaimer()

col_t, col_b = st.columns([3, 1])
with col_t:
    st.title("Causal Feature Engineering & Sliding Windows")
    st.caption("Stage 8 causal feature extraction across continuous observation segments and leakage safeguards")
with col_b:
    render_source_badge("HISTORICAL")

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# 1. Critical Methodological Safeguard (Progressive Disclosure)
with st.expander("Methodological Safeguard: Zero Temporal Leakage Rules (W = 60s, S = 10s)", expanded=False):
    st.markdown(
        """
        <div class="scientific-safeguard-card">
            <div class="safeguard-title">CRITICAL METHODOLOGICAL SAFEGUARD — ZERO TEMPORAL LEAKAGE</div>
            <p class="safeguard-text">
                Sliding windows with <strong>window duration W = 60 seconds</strong> and <strong>stride S = 10 seconds</strong> share <strong>83.3% of raw observations</strong> with adjacent windows.
                <strong>Random row-level splitting is strictly prohibited</strong>, as it leaks identical temporal fluctuations across training and test sets.
                All partitioning in SOLARIS-A1 is strictly chronological with temporal embargo buffers between splits.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 2. Engineered Numerical Features Distribution (Visual Inspection First)
st.subheader("1. Engineered Numerical Feature Distributions")
st.caption("Distribution of causal physical features extracted from Level-1 soft X-ray telemetry.")

feat_res = load_feature_table()

FEATURE_METADATA = {
    "peak_to_baseline_ratio": ("Dimensionless", "Ratio of maximum count rate in 60s window to local quiet-Sun baseline flux."),
    "max": ("counts / s", "Peak observed count rate across the 60-second observation window."),
    "mean": ("counts / s", "Average detector count rate across the observation window."),
    "std": ("counts / s", "Sample standard deviation of count rates within the window."),
    "median": ("counts / s", "Median detector count rate across the window."),
    "min": ("counts / s", "Minimum count rate observed in the window."),
    "temporal_slope": ("counts / s²", "Linear slope of flux over the full 60-second window duration."),
    "rolling_trend": ("counts / s²", "Impulsive linear slope computed over the trailing 15 seconds of the window."),
    "mean_abs_first_difference": ("counts / s", "Mean step-to-step absolute difference between adjacent 1.0s bins."),
    "max_abs_first_difference": ("counts / s", "Maximum impulsive single-step change between adjacent 1.0s bins."),
    "iqr": ("counts / s", "Interquartile range (75th percentile minus 25th percentile)."),
    "robust_variability": ("counts / s", "Normalized Median Absolute Deviation (MAD) robust variability scale."),
    "coverage_fraction": ("Ratio [0–1]", "Fraction of valid finite samples within the 60-second window."),
    "baseline_value": ("counts / s", "Estimated local background quiet-Sun flux rate."),
}

if feat_res.status == "MISSING":
    st.info("No feature table found. Run Stage 8 feature extraction to generate feature records.")
elif feat_res.status == "ERROR":
    render_status_banner("ERROR", feat_res.message, "Feature Table")
elif feat_res.status == "EMPTY":
    st.info("Feature table is empty.")
else:
    df_feat = feat_res.data.copy()

    # Strictly filter for genuine numerical columns, excluding identifiers and strings
    EXCLUDED_METADATA = {"window_id", "segment_id", "timestamp", "epoch", "file_stem", "status"}
    numeric_df = df_feat.select_dtypes(include=[np.number])
    valid_features = [c for c in numeric_df.columns if c.lower() not in EXCLUDED_METADATA]

    if valid_features:
        # Determine meaningful default feature (never a filename or identifier)
        default_idx = 0
        preferred_defaults = ["peak_to_baseline_ratio", "max", "mean", "temporal_slope"]
        for pref in preferred_defaults:
            if pref in valid_features:
                default_idx = valid_features.index(pref)
                break

        c_sel, c_bins = st.columns([2, 1])
        with c_sel:
            selected_feat = st.selectbox(
                "Select Numerical Feature to Inspect",
                valid_features,
                index=default_idx,
            )
        with c_bins:
            nbins = st.slider("Histogram Bins", min_value=10, max_value=80, value=35)

        # Feature explanation callout
        unit_str, desc_str = FEATURE_METADATA.get(selected_feat, ("Metric", "Extracted mathematical time-series feature."))
        st.markdown(
            f"""
            <div style="background:#0E1526; border:1px solid #1E293B; border-left:3px solid #F59E0B; padding:8px 14px; border-radius:6px; margin-bottom:12px;">
                <strong style="color:#FBBF24;">{selected_feat}</strong> &bull; <span style="color:#94A3B8;">Units: <code>{unit_str}</code></span>
                <div style="color:#CBD5E1; font-size:0.85rem; margin-top:2px;">{desc_str}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        fig_hist = build_feature_histogram(df_feat, selected_feat, nbins=nbins)
        st.plotly_chart(fig_hist, use_container_width=True)

        # Summary statistics
        f_vals = df_feat[selected_feat].dropna()
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Evaluated Windows", f"{len(f_vals):,}")
        s2.metric("Mean Value", f"{f_vals.mean():.3f} {unit_str}")
        s3.metric("Median Value", f"{f_vals.median():.3f} {unit_str}")
        s4.metric("Maximum Value", f"{f_vals.max():.3f} {unit_str}")
    else:
        st.warning("No valid numerical features found in feature artifact.")

st.markdown("---")

# 3. Sliding Window Index Browser (In Expandable Section)
st.subheader("2. Sliding Window Index Browser")
idx_res = load_feature_index()

if idx_res.is_ok and isinstance(idx_res.data, pd.DataFrame):
    df_idx = idx_res.data
    st.markdown(f"**Total Generated Observation Windows:** {len(df_idx):,} windows (W = 60s, S = 10s)")
    with st.expander("Browse Window Index Table (First 200 Windows)", expanded=False):
        st.dataframe(df_idx.head(200), use_container_width=True)
else:
    st.info("Window index table not available.")

# 4. Feature Dictionary Specification
root = project_root()
dict_file = root / "docs" / "11_feature_dictionary.md"
if dict_file.is_file():
    with st.expander("View Full Causal Feature Dictionary Specification (docs/11_feature_dictionary.md)", expanded=False):
        st.markdown(dict_file.read_text(encoding="utf-8"))
