"""SOLARIS-A1: Solar Research & Flare Detection Platform.

An AI-assisted solar research platform exploring Aditya-L1 SoLEXS X-ray observations,
verified solar flare events, and machine-learning-based flare detection.
"""

from __future__ import annotations

from pathlib import Path
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ensure repository root and src are on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from dashboard.loaders import (
    load_light_curve,
    load_policy_status,
    load_approved_events,
    format_approved_event_record,
)
from dashboard.components.banner import render_sidebar_disclaimer
from dashboard.components.theme import (
    apply_space_weather_theme,
    get_solar_hero_image_b64,
    get_solar_hero_image_url,
    get_solar_hero_video_b64,
    get_solar_hero_video_url,
    render_source_badge,
)
from solar_flare.inference.pipeline import get_default_pipeline
from solar_flare.paths import project_root

# Streamlit Page Configuration
st.set_page_config(
    page_title="SOLARIS-A1 | Solar Flare Research Platform",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_space_weather_theme()

# ==============================================================================
# 1. SEAMLESS OBSERVATORY HERO SECTION
# ==============================================================================

col_hero_text, col_hero_sun = st.columns([1.18, 0.82], gap="large")

with col_hero_text:
    hero_text_html = """<div class="hero-left-content">
        <div class="hero-eyebrow">ADITYA-L1 · SOLAR X-RAY RESEARCH</div>
        <div class="hero-main-title">SOLARIS-A1</div>
        <div class="hero-headline">Exploring the Sun. Understanding Solar Flares.</div>
        <p class="hero-summary">
            AI-assisted analysis of Aditya-L1 SoLEXS soft X-ray observations, verified solar flare events, and benchmark detection models.
        </p>
        <div class="hero-button-spacer"></div>
    </div>"""
    st.markdown(hero_text_html, unsafe_allow_html=True)

    # Primary Actions: Prominently placed directly below description with 24px comfortable spacing
    act_c1, act_c2 = st.columns([1, 1], gap="medium")
    with act_c1:
        st.page_link(
            "pages/4_Light_Curves.py",
            label="Explore Observations",
            icon="📈",
            use_container_width=True,
        )
    with act_c2:
        st.page_link(
            "pages/7_Model_Results.py",
            label="View Model Results",
            icon="🤖",
            use_container_width=True,
        )

with col_hero_sun:
    video_b64 = get_solar_hero_video_b64()
    video_url = get_solar_hero_video_url()

    sources_html = ""
    if video_b64:
        sources_html += f'<source src="data:video/mp4;base64,{video_b64}" type="video/mp4">'
    if video_url:
        sources_html += f'<source src="{video_url}" type="video/mp4">'

    if sources_html:
        media_html = f"""<video class="hero-sun-video" autoplay loop muted playsinline preload="auto" disablepictureinpicture>
            {sources_html}
        </video>"""
    else:
        sun_b64 = get_solar_hero_image_b64()
        sun_img_url = get_solar_hero_image_url()
        fallback_src = f"data:image/png;base64,{sun_b64}" if sun_b64 else (sun_img_url or "")
        media_html = f'<img src="{fallback_src}" class="hero-sun-video" alt="Authentic Solar Observation" />'

    hero_sun_html = f"""
    <!-- SOLARIS-A1 Cinematic Solar Illumination & Animated Sun -->
    <div class="hero-sun-wrapper">
        <div class="hero-sun-glow-ambient"></div>
        <div class="hero-sun-glow-core"></div>
        {media_html}
    </div>
    """
    st.markdown(hero_sun_html, unsafe_allow_html=True)

# Compact Metadata Row: Positioned seamlessly below the hero composition
metadata_strip_html = """<div class="hero-metadata-strip">
    <span class="meta-item"><span class="meta-dot">●</span> <strong>Observatory:</strong> Aditya-L1 SoLEXS (1.0–22.0 keV)</span>
    <span class="meta-sep">/</span>
    <span class="meta-item"><span class="meta-dot">●</span> <strong>Telemetry Archive:</strong> ISRO PRADAN Level-1</span>
    <span class="meta-sep">/</span>
    <span class="meta-item"><span class="meta-dot">●</span> <strong>Ground Truth:</strong> NOAA SWPC Solar Event Reports</span>
</div>"""
st.markdown(metadata_strip_html, unsafe_allow_html=True)

# ==============================================================================
# 2. CORE SCIENTIFIC OBSERVATION & MODEL OVERVIEW
# ==============================================================================

# Top-Line Supported Scientific Status Row
c_obs, c_duty, c_events, c_model = st.columns(4)

with c_obs:
    st.metric(
        "Observation Date",
        "2026-10-18",
        "86,400s · 1.0s Cadence",
    )

with c_duty:
    st.metric(
        "GTI Duty Cycle",
        "94.24%",
        "8 Valid Science Intervals",
    )

with c_events:
    st.metric(
        "Verified Flare Events",
        "2 Pilot Events",
        "119 Approved in Catalog",
    )

with c_model:
    st.metric(
        "ML Research Scope",
        "Task A (60s Window)",
        "In-Window Detection Only",
    )

st.markdown("---")

# ==============================================================================
# 3. OBSERVATION LIGHT CURVE & VERIFIED EVENT CONTEXT
# ==============================================================================

col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("Solar Soft X-ray Observation Profile (2026-10-18)")
    st.caption("Aditya-L1 SoLEXS SDD2 detector count rate across full 24-hour observation orbit with verified NOAA flares highlighted.")

    # Load authentic light curve data
    lc_res = load_light_curve("AL1_SOLEXS_20261018_SDD2_L1")
    if lc_res.is_ok and isinstance(lc_res.data, pd.DataFrame) and not lc_res.data.empty:
        df_lc = lc_res.data
        times = df_lc["time"].values
        counts = df_lc["counts"].values

        # Subsample for compact overview display
        step = max(1, len(times) // 2500)
        disp_times = times[::step]
        disp_counts = counts[::step]

        # Convert MET seconds to hours for intuitive overview
        t0 = times[0]
        disp_hours = (disp_times - t0) / 3600.0

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=disp_hours,
                y=disp_counts,
                customdata=disp_times,
                mode="lines",
                name="SoLEXS SDD2",
                line=dict(color="#F59E0B", width=1.5),
                hovertemplate="<b>Orbit Elapsed:</b> %{x:.2f} hrs<br><b>Mission MET:</b> %{customdata:.1f} s<br><b>Flux Rate:</b> %{y:.1f} counts/s<extra></extra>",
            )
        )

        # Highlight Event 1 (~10:50 UTC, ~10.8 hrs)
        fig.add_vrect(
            x0=10.7,
            x1=11.1,
            fillcolor="rgba(56, 189, 248, 0.2)",
            line=dict(color="#38BDF8", width=1),
            annotation_text="Event 1 (C2.8 @ 10:50 UTC)",
            annotation_position="top",
            annotation=dict(font_size=12, font_color="#38BDF8"),
        )

        # Highlight Event 2 (~19:17 UTC, ~19.3 hrs)
        fig.add_vrect(
            x0=19.1,
            x1=19.5,
            fillcolor="rgba(234, 88, 12, 0.25)",
            line=dict(color="#EA580C", width=1),
            annotation_text="Event 2 (M1.1 @ 19:17 UTC)",
            annotation_position="top",
            annotation=dict(font_size=12, font_color="#FB923C"),
        )

        fig.update_layout(
            xaxis=dict(
                title=dict(text="Elapsed Observation Time (Hours from 00:00:00 UTC)", font=dict(size=13, color="#CBD5E1")),
                tickfont=dict(size=11, color="#94A3B8"),
                gridcolor="#1E293B",
            ),
            yaxis=dict(
                title=dict(text="Count Rate (counts/s)", font=dict(size=13, color="#CBD5E1")),
                tickfont=dict(size=11, color="#94A3B8"),
                gridcolor="#1E293B",
            ),
            template="plotly_dark",
            paper_bgcolor="#0E1526",
            plot_bgcolor="#070B14",
            margin=dict(l=45, r=20, t=25, b=45),
            height=410,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Primary light curve telemetry artifact is loading.")

with col_right:
    st.subheader("Verified Observation Events (Gate G3)")
    st.caption("NOAA SWPC verified solar flare events aligned with 2026-10-18 observation orbit.")

    # Load approved events catalog
    ev_res = load_approved_events()
    if ev_res.is_ok and isinstance(ev_res.data, pd.DataFrame):
        df_approved = ev_res.data
        # Filter for active observation cohort (2026-10-18 pilot events)
        pilot_mask = df_approved["event_id"].str.startswith("EVT_20261018")
        df_pilot = df_approved[pilot_mask]

        if not df_pilot.empty:
            for _, row in df_pilot.iterrows():
                rec = format_approved_event_record(row)
                fclass = rec["classification"]
                badge_class = "badge-verified"
                p_utc = rec["peak_time_utc"]
                dur = rec["duration"]
                notes = rec["notes"]
                eid = rec["event_id"]
                authority = rec["source_id"]

                st.markdown(
                    f"""
                    <div style="background:#0E1526; border:1px solid #1E293B; border-left:4px solid #38BDF8; padding:14px 18px; border-radius:8px; margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:#F8FAFC; font-size:1.06rem;">Flare {fclass}</strong>
                            <span class="{badge_class}">NOAA Verified</span>
                        </div>
                        <div style="color:#CBD5E1; font-size:0.90rem; margin-top:5px; line-height:1.45;">
                            <span>● <strong>Peak:</strong> <code>{p_utc}</code></span> &bull; <span>Duration: {dur}</span>
                        </div>
                        <div style="color:#94A3B8; font-size:0.80rem; margin-top:4px; font-family:monospace;">
                            Authority: {authority} &bull; ID: {eid}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Prominent link to full catalog on Events page
        st.page_link(
            "pages/5_Events.py",
            label="View Full Catalog (119 Approved Events) →",
            icon="⚡",
            use_container_width=True,
        )
    else:
        st.info("Approved event records catalog not found at data/manifests/event_records_approved.csv.")

st.markdown("---")

# ==============================================================================
# 4. RESEARCH SCOPE & METHODOLOGICAL SAFEGUARDS (PROGRESSIVE DISCLOSURE)
# ==============================================================================

with st.expander("Research Scope & Methodological Disclaimers", expanded=False):
    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.markdown(
            """
            <div class="scientific-card-accent">
                <h4 style="color:#FBBF24; margin-top:0;">Task A: Current-Window Flare Detection</h4>
                <p style="color:#CBD5E1; font-size:0.88rem; line-height:1.5;">
                    SOLARIS-A1's primary machine learning models evaluate whether solar flaring activity occurs within a
                    <strong>60-second observation window</strong> [t &minus; 60s, t].
                </p>
                <ul style="color:#94A3B8; font-size:0.82rem; padding-left:18px; margin-bottom:0;">
                    <li><strong>Causal Feature Inputs:</strong> 18 strictly causal soft X-ray features (mean, peak, variability, slopes).</li>
                    <li><strong>Strict Leakage Prohibition:</strong> Chronological data splits ensure zero future-to-past temporal leakage.</li>
                    <li><strong>Evaluated Champions:</strong> XGBoost, Random Forest, and Logistic Regression baseline.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with info_col2:
        st.markdown(
            """
            <div class="scientific-card">
                <h4 style="color:#38BDF8; margin-top:0;">Important Scientific Limitations</h4>
                <p style="color:#CBD5E1; font-size:0.88rem; line-height:1.5;">
                    To maintain scientific credibility, all evaluations operate under strict research constraints:
                </p>
                <ul style="color:#94A3B8; font-size:0.82rem; padding-left:18px; margin-bottom:0;">
                    <li><strong>Detection vs. Forecasting:</strong> Current models perform in-window detection, <em>not</em> advance pre-flare forecasting.</li>
                    <li><strong>Binary Detection:</strong> Evaluates flare presence vs. quiet Sun; does not classify GOES X-ray class.</li>
                    <li><strong>Research Benchmark Only:</strong> Retrospective offline evaluation; <strong>not certified for operational space-weather alerting</strong>.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Sidebar Model Status Card
try:
    pipe = get_default_pipeline()
    v_info = pipe.version_info
    m_name = v_info["model_name"].upper()
    st.sidebar.markdown(
        f"""
        <div class="sidebar-model-panel">
            <div class="sidebar-panel-header">
                <span class="sidebar-panel-indicator">●</span>
                <span class="sidebar-panel-title">{m_name}</span>
                <span class="sidebar-panel-badge">Active</span>
            </div>
            <div class="sidebar-panel-body">
                <div class="sidebar-panel-row">
                    <span>Profile</span>
                    <code>{v_info['profile_id']}</code>
                </div>
                <div class="sidebar-panel-row">
                    <span>Cohort</span>
                    <span>{v_info['dataset_cohort']}</span>
                </div>
            </div>
            <div class="sidebar-panel-footer">Research Baseline (Decision D-15)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
except Exception:
    st.sidebar.markdown(
        """
        <div class="sidebar-model-panel">
            <div class="sidebar-panel-header">
                <span style="color:#64748B;">●</span>
                <span class="sidebar-panel-title">Model Profile</span>
                <span class="sidebar-panel-badge" style="color:#64748B; border-color:#334155;">Offline</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

render_sidebar_disclaimer()
