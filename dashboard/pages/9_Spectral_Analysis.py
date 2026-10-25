"""Page 9: Multi-Channel Energy Spectra & Spectral Hardness Analysis."""

from __future__ import annotations

from pathlib import Path
from astropy.io import fits
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from dashboard.components.theme import apply_space_weather_theme, render_source_badge
from solar_flare.paths import project_root

st.set_page_config(page_title="Spectral Analysis | SOLARIS-A1", page_icon="🌈", layout="wide")
apply_space_weather_theme()
render_sidebar_disclaimer()

col_t, col_b = st.columns([3, 1])
with col_t:
    st.title("Multi-Channel Soft X-Ray Spectral Analysis")
    st.caption("Aditya-L1 SoLEXS Level-1 Pulse Invariant (PI) 340-channel energy spectra (1.0 keV to 22.0 keV)")
with col_b:
    render_source_badge("HISTORICAL")

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

root = project_root()
pi_file = root / "data" / "raw" / "AL1_SOLEXS_20261018_SDD2_L1.pi.gz"

if not pi_file.is_file():
    st.error(f"Pulse Invariant spectral file not found at: {pi_file}")
    st.stop()

# 1. Flaring Epoch Spectrum Comparison (Visualization First)
try:
    with fits.open(pi_file) as hdul:
        hdr0 = hdul[0].header
        hdr1 = hdul[1].header
        n_rows = len(hdul[1].data)
except Exception as exc:
    st.error(f"Failed to read spectral FITS file: {exc}")
    st.stop()

preset_spec = st.selectbox(
    "Select Flaring Epoch to Compare Against Quiet-Sun Baseline (1.0 keV to 22.0 keV)",
    [
        "Event 2 Peak (Major Impulsive Flare @ 19:17:22 UTC)",
        "Event 1 Peak (Moderate Cluster @ 10:50:27 UTC)",
    ],
)

if "Event 2" in preset_spec:
    t_target = 1792351042.0
    label_target = "Event 2 Peak (19:17:22 UTC)"
else:
    t_target = 1792320627.0
    label_target = "Event 1 Peak (10:50:27 UTC)"

t_quiet = 1792300000.0
label_quiet = "Quiet-Sun Baseline (05:06:40 UTC)"

try:
    with fits.open(pi_file) as hdul:
        tstart_arr = hdul[1].data["TSTART"]
        counts_arr = hdul[1].data["COUNTS"]

        idx_flare = int(np.argmin(np.abs(tstart_arr - t_target)))
        idx_quiet = int(np.argmin(np.abs(tstart_arr - t_quiet)))

        flare_spec = counts_arr[idx_flare]
        quiet_spec = counts_arr[idx_quiet]
        channels = np.arange(len(flare_spec))

        # Approximate energy calibration (1.0 keV to 22.0 keV across 340 channels)
        approx_energy_kev = 1.0 + (channels / 340.0) * 21.0

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=approx_energy_kev,
                y=flare_spec,
                mode="lines",
                name=label_target,
                line=dict(color="#F59E0B", width=2.0),
                hovertemplate="<b>Energy:</b> %{x:.2f} keV<br><b>Counts:</b> %{y}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=approx_energy_kev,
                y=quiet_spec,
                mode="lines",
                name=label_quiet,
                line=dict(color="#38BDF8", width=1.5, dash="dash"),
                hovertemplate="<b>Energy:</b> %{x:.2f} keV<br><b>Counts:</b> %{y}<extra></extra>",
            )
        )

        fig.update_layout(
            xaxis=dict(
                title="Approximate Photon Energy (keV)",
                range=[1.0, 22.0],
                gridcolor="#1E293B",
                color="#CBD5E1",
            ),
            yaxis=dict(
                title="Pulse Invariant Counts (1.0s Integration)",
                gridcolor="#1E293B",
                color="#CBD5E1",
            ),
            hovermode="x unified",
            template="plotly_dark",
            paper_bgcolor="#0E1526",
            plot_bgcolor="#070B14",
            font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color="#CBD5E1"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=20, t=25, b=35),
            height=340,
        )

        st.plotly_chart(fig, use_container_width=True)

        # 2. Instrument Telemetry & Spectral Calibration (Progressive Disclosure)
        with st.expander("Instrument Specifications & 340-Channel Calibration Details", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total 1.0s Spectra", f"{n_rows:,}", "1-second cadenced bins")
            with c2:
                st.metric("Energy Channels", "340 Channels", "1.0 keV to 22.0 keV")
            with c3:
                st.metric("Active Detector", "SDD2", "Level-1 Pulse Invariant")
            with c4:
                st.metric("Spectral Band", "Soft X-ray", "Thermal & Bremsstrahlung")

            st.markdown(
                """
                <div class="scientific-card" style="margin-top:10px;">
                    <strong style="color:#FBBF24;">Astrophysical Context: Soft X-Ray Spectrum Hardening</strong>
                    <div style="color:#CBD5E1; font-size:0.85rem; line-height:1.5; margin-top:4px;">
                        During peak flaring, magnetic reconnection in the solar corona accelerates electrons that heat coronal plasma to tens of millions of Kelvin.
                        This produces intense soft X-ray thermal bremsstrahlung emission predominantly below 10 keV, accompanied by spectral hardening extending into higher energy channels.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

except Exception as exc:
    st.error(f"Error processing spectral data: {exc}")
