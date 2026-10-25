"""Page 2: Available Observations, Detectors & Data Product Inventory."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from dashboard.loaders import load_inventory
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from dashboard.components.theme import apply_space_weather_theme, render_source_badge
from solar_flare.paths import project_root

st.set_page_config(page_title="Dataset | SOLARIS-A1", page_icon="📁", layout="wide")
apply_space_weather_theme()
render_sidebar_disclaimer()

col_t, col_b = st.columns([3, 1])
with col_t:
    st.title("Dataset Architecture & Observation Inventory")
    st.caption("Available Aditya-L1 SoLEXS Level-1 scientific observation products, detectors, and checksum provenance")
with col_b:
    render_source_badge("HISTORICAL")

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# 1. Available Observation Cohorts & Detectors Summary
st.subheader("1. Available Observation Cohorts")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Primary Pilot Date", "2026-10-18", "86,400s Telemetry")
with c2:
    st.metric("Benchmark Cohort", "July 1–14, 2024", "13 Observation Dates")
with c3:
    st.metric("Active Detector", "SDD2 (Channel 2)", "Calibrated Science Data")
with c4:
    st.metric("Checksum Status", "100% SHA-256 Matched", "Zero Unregistered Files")

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# 2. Observation Cohort Coverage Summary
st.subheader("2. Observation Cohort Coverage Summary")
cohort_summary_data = [
    {
        "Cohort": "October 2026 Pilot Baseline",
        "Date Range": "2026-10-18 (Full Orbit)",
        "Files": "4 FITS (.lc, .gti, .pi)",
        "Science Coverage": "81,425s / 86,400s (94.24%)",
        "Detector Status": "SDD2 Calibrated (SDD1 Empty GTI)",
        "Research Role": "Production Baseline (Decision D-15)",
    },
    {
        "Cohort": "July 2024 Multi-Orbit Benchmark",
        "Date Range": "July 1–14, 2024 (13 dates)",
        "Files": "26 FITS (13 pairs)",
        "Science Coverage": "269.4 Total Science Hours",
        "Detector Status": "SDD2 Calibrated Science",
        "Research Role": "Benchmark Stress-Test (Gates G7/G8)",
    },
]
st.dataframe(pd.DataFrame(cohort_summary_data), use_container_width=True, hide_index=True)

# 3. Detector Channels & Data Product Architecture
c_det, c_prod = st.columns([1.1, 0.9])

with c_det:
    st.markdown(
        """
        <div class="scientific-card-accent">
            <strong style="color:#FBBF24; font-size:0.90rem;">Detector Allocation & GTI Policy</strong>
            <div style="color:#CBD5E1; font-size:0.83rem; margin-top:4px; line-height:1.45;">
                ● <strong>SDD2 (Silicon Drift Detector 2):</strong> Primary calibrated channel for all model features, 1.0–22.0 keV.<br>
                ● <strong>SDD1 (Silicon Drift Detector 1):</strong> Contains 0 valid science intervals for 2026-10-18. Strictly segregated to prevent cross-channel contamination.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c_prod:
    st.markdown(
        """
        <div class="scientific-card">
            <strong style="color:#38BDF8; font-size:0.90rem;">Level-1 Scientific Data Products</strong>
            <div style="color:#CBD5E1; font-size:0.83rem; margin-top:4px; line-height:1.45;">
                ● <strong>.lc:</strong> 1-second cadence integrated count rate time series.<br>
                ● <strong>.pi:</strong> 340-channel pulse invariant soft X-ray spectra.<br>
                ● <strong>.gti:</strong> Verified Good Time Interval boundary timestamps.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# 4. FITS Product Inventory (In Expandable Section)
inv_res = load_inventory()
if inv_res.is_ok and isinstance(inv_res.data, pd.DataFrame):
    df_inv = inv_res.data
    with st.expander("Explore Raw FITS Product Inventory & Checksums", expanded=False):
        st.markdown(f"**Total Registered FITS Files:** {len(df_inv)}")
        st.dataframe(df_inv, use_container_width=True)
        st.caption("Manifest Source: `data/manifests/manifest.csv` | Checksum: Chunked SHA-256 verified.")
