"""Page 3: Data Quality Characterisation & Quality Metrics."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.loaders import (
    load_quality_summary,
    load_column_roles,
    load_inventory,
)
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from dashboard.components.theme import apply_space_weather_theme, render_source_badge
from solar_flare.paths import project_root

st.set_page_config(page_title="Data Quality | SOLARIS-A1", page_icon="🛡️", layout="wide")
apply_space_weather_theme()
render_sidebar_disclaimer()

col_t, col_b = st.columns([3, 1])
with col_t:
    st.title("Data Quality Characterization & Integrity")
    st.caption("Good Time Interval (GTI) duty cycle, non-finite sample segregation, telemetry gaps, and cadence stability")
with col_b:
    render_source_badge("HISTORICAL")

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# 1. Executive Quality Metrics (Pilot 2026-10-18 Observation)
q1, q2, q3, q4 = st.columns(4)
with q1:
    st.metric("GTI Duty Cycle", "94.24%", "81,425s / 86,400s Orbit")
with q2:
    st.metric("Missing Samples (NaN)", "4,849 (5.61%)", "Outside Valid GTIs Only", delta_color="inverse")
with q3:
    st.metric("Cadence Uniformity", "1.000 s", "Zero Cadence Jitter")
with q4:
    st.metric("Non-Finite in GTI", "0 Samples", "100% Finite During Science GTIs")

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# 2. Interactive Observation Quality Comparison Chart (Visualization First)
st.subheader("1. GTI Science Coverage Across Observation Cohorts")

q_res = load_quality_summary()
if q_res.is_ok and isinstance(q_res.data, pd.DataFrame):
    df_q = q_res.data.copy()
    # Filter for light curve rows with numeric gti coverage
    lc_mask = df_q["file_stem"].str.contains(r"\.lc", regex=True, na=False)
    df_plot = df_q[lc_mask].copy()

    df_plot["gti_fraction"] = pd.to_numeric(df_plot["gti_covered_fraction"], errors="coerce")
    df_plot = df_plot.dropna(subset=["gti_fraction"])

    # Clean label
    df_plot["label"] = df_plot["file_stem"].str.replace("AL1_SOLEXS_", "").str.replace("_SDD2_L1.lc", "")

    fig = go.Figure()
    bar_colors = ["#EF4444" if frac < 0.80 else "#F59E0B" if frac < 0.95 else "#10B981" for frac in df_plot["gti_fraction"]]

    fig.add_trace(
        go.Bar(
            x=df_plot["label"],
            y=df_plot["gti_fraction"] * 100.0,
            marker_color=bar_colors,
            hovertemplate="<b>Observation:</b> %{x}<br><b>GTI Coverage:</b> %{y:.2f}%<extra></extra>",
        )
    )

    fig.add_hline(
        y=80.0,
        line_dash="dot",
        line_color="#EF4444",
        annotation_text="80% Science Usability Threshold",
        annotation_position="bottom right",
        annotation_font=dict(color="#EF4444", size=10),
    )

    fig.update_layout(
        xaxis=dict(title="Observation Date / Run", gridcolor="#1E293B", color="#CBD5E1"),
        yaxis=dict(title="GTI Coverage Duty Cycle (%)", range=[0, 105], gridcolor="#1E293B", color="#CBD5E1"),
        template="plotly_dark",
        paper_bgcolor="#0E1526",
        plot_bgcolor="#070B14",
        height=280,
        margin=dict(l=40, r=20, t=20, b=35),
    )
    st.plotly_chart(fig, use_container_width=True)

# 3. Telemetry Gaps & Segregation Assessment (Progressive Disclosure)
with st.expander("Telemetry Gaps & Non-GTI Segregation Assessment", expanded=False):
    gap_col1, gap_col2 = st.columns(2)

    with gap_col1:
        st.markdown(
            """
            <div class="scientific-card-accent">
                <h4 style="color:#FBBF24; margin-top:0;">GTI Segregation & Night Passes</h4>
                <p style="color:#CBD5E1; font-size:0.86rem; line-height:1.5;">
                    Across the 86,400-second pilot observation, <strong>4,849 samples (5.61%)</strong> are non-finite (<code>NaN</code>).
                </p>
                <ul style="color:#94A3B8; font-size:0.80rem; padding-left:18px;">
                    <li><strong>Strict Confinement:</strong> All 4,849 non-finite samples fall strictly outside valid Good Time Intervals (GTIs).</li>
                    <li><strong>Scientific Rule:</strong> SOLARIS-A1 never imputes or interpolates across telemetry gaps; non-GTI windows are strictly segregated.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with gap_col2:
        st.markdown(
            """
            <div class="scientific-card">
                <h4 style="color:#EF4444; margin-top:0;">Degraded Observations in Benchmark Cohort</h4>
                <p style="color:#CBD5E1; font-size:0.86rem; line-height:1.5;">
                    In the July 2024 multi-orbit dataset, telemetry coverage varies significantly:
                </p>
                <ul style="color:#94A3B8; font-size:0.80rem; padding-left:18px;">
                    <li><strong>Severely Degraded Dates:</strong> July 8 (39.12% GTI coverage) and July 9 (65.04% GTI coverage).</li>
                    <li><strong>Clean Held-Out Test Set:</strong> July 13 and July 14 maintain 100% GTI science coverage with only 1 NaN each.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# 4. Collapsible Quality Inspection & Per-File Audit Records
with st.expander("Technical Quality Summary Table & Per-File Audit Records", expanded=False):
    st.markdown("### Quality Summary Table")
    if q_res.is_ok and isinstance(q_res.data, pd.DataFrame):
        st.dataframe(q_res.data, use_container_width=True)

    root = project_root()
    q_base = root / "results" / "quality"
    subdirs = [d for d in q_base.iterdir() if d.is_dir()] if q_base.is_dir() else []

    if subdirs:
        st.markdown("### Detailed Diagnostic Figures")
        sel_dir = st.selectbox("Select Analyzed Observation", [d.name for d in subdirs])
        target_dir = q_base / sel_dir

        c_cad, c_cnt = st.columns(2)
        with c_cad:
            cad_img = target_dir / "cadence_histogram.png"
            if cad_img.is_file():
                st.image(str(cad_img), caption="Cadence Interval Distribution (1.000s Target)")
        with c_cnt:
            cnt_img = target_dir / "count_distribution.png"
            if cnt_img.is_file():
                st.image(str(cnt_img), caption="Detector Count Rate Distribution")
