"""Page 1: Project Overview, Scientific Mission & Observation Architecture."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from dashboard.loaders import (
    load_inventory,
    load_open_questions,
    load_light_curve,
)
from dashboard.components.banner import render_sidebar_disclaimer
from dashboard.components.figures import build_light_curve_figure
from dashboard.components.theme import apply_space_weather_theme, render_source_badge
from solar_flare.paths import project_root
from solar_flare.status import pipeline_status
from solar_flare.inference.pipeline import get_default_pipeline

st.set_page_config(page_title="Overview | SOLARIS-A1", page_icon="🔭", layout="wide")
apply_space_weather_theme()
render_sidebar_disclaimer()

# Header
col_t, col_b = st.columns([3, 1])
with col_t:
    st.title("Project Overview & Scientific Mission")
    st.caption("Aditya-L1 SoLEXS Soft X-Ray Flare Detection Research Platform")
with col_b:
    render_source_badge("HISTORICAL")

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# 1. Mission Architecture & What SOLARIS-A1 Does
st.subheader("1. What SOLARIS-A1 Does")

st.markdown(
    """
    **SOLARIS-A1** is a machine learning research platform designed to process, analyze, and detect solar flares in soft X-ray telemetry from the **Solar Low Energy X-ray Spectrometer (SoLEXS)** aboard India's flagship solar observatory, **Aditya-L1**.

    Stationed at the Sun-Earth Lagrange Point 1 (L1), approximately 1.5 million kilometers from Earth, SoLEXS measures full-disk solar soft X-ray irradiance in the **1.0 to 22.0 keV** energy range using high-spectral-resolution Silicon Drift Detectors (SDD).
    """
)

col_obj, col_scope = st.columns(2)

with col_obj:
    st.markdown(
        """
        <div class="flare-card" style="min-height: 140px;">
            <h4 style="margin: 0 0 6px 0; color: #F8FAFC;">Scientific Objective</h4>
            <p style="margin: 0; font-size: 0.88rem; color: #94A3B8;">
                Develop an automated, causally sound machine learning pipeline capable of detecting solar flares within short 60-second observation windows from raw Level-1 X-ray count rate telemetry, while strictly accounting for non-solar instrumental artifacts and telemetry gaps.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_scope:
    st.markdown(
        """
        <div class="flare-card" style="min-height: 140px;">
            <h4 style="margin: 0 0 6px 0; color: #F8FAFC;">Task A Research Scope</h4>
            <p style="margin: 0; font-size: 0.88rem; color: #94A3B8;">
                <strong>In-Window Detection:</strong> SOLARIS-A1 currently implements <strong>Task A (In-Window Detection)</strong>, classifying whether an active solar flare is occurring during a specific 60-second observation window. It is <em>not</em> an operational predictive forecasting warning system (pre-flare warning remains future Task B research).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# 2. Pilot Observation Telemetry Overview
st.subheader("2. Observation Light Curve & Verified Solar Flares")

stem = "AL1_SOLEXS_20261018_SDD2_L1"
lc_res = load_light_curve(stem)

if lc_res.is_ok and isinstance(lc_res.data, pd.DataFrame):
    df_lc = lc_res.data

    # Load GTI intervals
    root = project_root()
    gti_file = root / "data" / "raw" / f"{stem}.gti.gz"
    if not gti_file.is_file():
        gti_file = root / "data" / "raw" / f"{stem}.gti"

    gti_intervals = []
    if gti_file.is_file():
        try:
            from astropy.io import fits
            with fits.open(gti_file) as hdul:
                for h in hdul:
                    if h.data is not None and "START" in h.data.names and "STOP" in h.data.names:
                        starts = h.data["START"]
                        stops = h.data["STOP"]
                        for s, e in zip(starts, stops):
                            gti_intervals.append((float(s), float(e)))
                        break
        except Exception:
            pass

    # Confirmed NOAA flares for pilot date
    verified_events = [
        {"start": 1792320570.0, "end": 1792320720.0, "event_id": "Event 1", "class": "C2.8 @ 10:50 UTC"},
        {"start": 1792351020.0, "end": 1792351200.0, "event_id": "Event 2", "class": "M1.1 @ 19:17 UTC"},
    ]

    fig, downsampled = build_light_curve_figure(
        df=df_lc,
        time_col="time",
        count_col="counts",
        gti_intervals=gti_intervals,
        verified_events=verified_events,
        max_display_points=8000,
        time_axis_mode="elapsed_hours",
    )
    st.plotly_chart(fig, use_container_width=True)
    if downsampled:
        st.caption("ℹ️ *Display Downsampling Active: Rendering a smoothed preview for interactive responsiveness (display-only; not used in model feature extraction).*")

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# 3. Ground Truth Verification Table
st.subheader("3. Verified Observation Events (Gate G3)")

events_data = [
    {
        "Event ID": "AL1_EVT_20261018_001",
        "Onset Time (UTC)": "2026-10-18 10:49:30",
        "Peak Time (UTC)": "2026-10-18 10:50:42",
        "End Time (UTC)": "2026-10-18 10:52:00",
        "Duration": "150 s",
        "NOAA Classification": "C2.8",
        "Status": "Approved (Gate G3 Passed)",
    },
    {
        "Event ID": "AL1_EVT_20261018_002",
        "Onset Time (UTC)": "2026-10-18 19:17:00",
        "Peak Time (UTC)": "2026-10-18 19:18:15",
        "End Time (UTC)": "2026-10-18 19:20:00",
        "Duration": "180 s",
        "NOAA Classification": "M1.1",
        "Status": "Approved (Gate G3 Passed)",
    },
]
df_events = pd.DataFrame(events_data)
st.dataframe(df_events, use_container_width=True, hide_index=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# 4. Machine Learning Model Status & Limitations
st.subheader("4. Machine Learning Model Status & Limitations")

col_m1, col_m2 = st.columns(2)

with col_m1:
    st.markdown(
        """
        <div class="flare-card" style="min-height: 170px;">
            <h4 style="margin: 0 0 6px 0; color: #F8FAFC;">Production Model Baseline</h4>
            <p style="margin: 0; font-size: 0.88rem; color: #94A3B8;">
                <strong>Active Model:</strong> XGBoost Classifier (Trained under PROTO_STAGE10_EXPANDED_002)<br>
                <strong>Input Features:</strong> 19 causal summary statistics computed strictly within each 60s sliding window.<br>
                <strong>Test Performance:</strong> Precision = 0.771, Recall = 0.783, ROC-AUC = 0.941.<br>
                <strong>Validation:</strong> Evaluated on chronologically segregated, held-out test windows.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m2:
    st.markdown(
        """
        <div class="flare-card" style="min-height: 170px;">
            <h4 style="margin: 0 0 6px 0; color: #F8FAFC;">Research Safeguards & Limitations</h4>
            <p style="margin: 0; font-size: 0.88rem; color: #94A3B8;">
                <strong>Zero Temporal Leakage:</strong> Strict chronological window partitioning prevents future information leakage.<br>
                <strong>GTI Confinement:</strong> Non-science telemetry gaps are masked; features are extracted only within continuous GTI spans.<br>
                <strong>Operational Boundary:</strong> In-window detection only; not certified for life-critical spacecraft safety operations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
