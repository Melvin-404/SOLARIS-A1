"""Page 4: Interactive Light-Curve Viewer with GTI Shading & Flagged Samples."""

from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

from dashboard.loaders import (
    load_inventory,
    load_light_curve,
    load_column_roles,
)
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from dashboard.components.figures import build_light_curve_figure
from solar_flare.paths import project_root

st.set_page_config(page_title="Light Curves | SOLARIS-A1", page_icon="📈", layout="wide")
render_sidebar_disclaimer()

st.title("📈 Interactive Light-Curve Exploration")
st.caption("Level-1 light curves, Good Time Intervals (GTI), non-finite sample segregation, and display downsampling")

# 1. Column Role Status Banner
roles_res = load_column_roles()
if roles_res.status == "PROVISIONAL":
    render_status_banner("PROVISIONAL", "Column roles are PROVISIONAL pending Gate G1/G2 confirmation.", "Column Roles")
else:
    render_status_banner("OK", "Column roles are formally CONFIRMED by human researcher.", "Column Roles")

st.markdown("---")

# 2. File Selector
inv_res = load_inventory()
lc_stems = ["AL1_SOLEXS_20261018_SDD2_L1"]

if inv_res.is_ok and isinstance(inv_res.data, pd.DataFrame):
    df_inv = inv_res.data
    if "product_type" in df_inv.columns and "file_name" in df_inv.columns:
        lc_files = df_inv[df_inv["product_type"] == "LIGHTCURVE"]["file_name"].tolist()
        stems = [f.replace(".lc.gz", "").replace(".lc", "") for f in lc_files]
        if stems:
            lc_stems = stems

col_sel1, col_sel2 = st.columns([2, 1])
with col_sel1:
    selected_stem = st.selectbox("Select Light-Curve File", lc_stems)

# Load data
lc_res = load_light_curve(selected_stem)

if lc_res.status == "MISSING":
    render_status_banner("MISSING", lc_res.message, "Light Curve")
    st.stop()
elif lc_res.status == "ERROR":
    render_status_banner("ERROR", lc_res.message, "Light Curve")
    st.stop()
elif lc_res.status == "EMPTY":
    render_status_banner("EMPTY", lc_res.message, "Light Curve")
    st.stop()

df_lc = lc_res.data
t_min = float(df_lc["time"].min())
t_max = float(df_lc["time"].max())

# 3. Interactive Visualization Controls
col_c1, col_c2, col_c3 = st.columns([2, 1, 1])

with col_c1:
    time_range = st.slider(
        "Select Time Window (seconds)",
        min_value=t_min,
        max_value=t_max,
        value=(t_min, t_max),
        step=1.0,
    )

with col_c2:
    log_scale = st.checkbox("Logarithmic Count Scale", value=False)

with col_c3:
    show_flagged = st.checkbox("Show Segregated Samples (0 & NaN)", value=True)

# Filter by time range
mask = (df_lc["time"] >= time_range[0]) & (df_lc["time"] <= time_range[1])
filtered_lc = df_lc[mask].reset_index(drop=True)

# Load GTI intervals if available
root = project_root()
gti_file = root / "data" / "raw" / f"{selected_stem}.gti.gz"
if not gti_file.is_file():
    gti_file = root / "data" / "raw" / f"{selected_stem}.gti"

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

# 4. Build and Render Plotly Figure
fig, downsampled = build_light_curve_figure(
    df=filtered_lc,
    time_col="time",
    count_col="counts",
    gti_intervals=gti_intervals,
    log_scale=log_scale,
    show_flagged=show_flagged,
    max_display_points=12000,
)

if downsampled:
    st.info(
        "ℹ️ **Display Downsampling Notice:** Rendering downsampled view to preserve browser interactivity. "
        "Downsampling is strictly display-only and is never applied to scientific computation."
    )

st.plotly_chart(fig, use_container_width=True)

# Summary statistics
st.markdown("### Window Statistics")
col_s1, col_s2, col_s3, col_s4 = st.columns(4)
col_s1.metric("Samples in View", len(filtered_lc))
col_s2.metric("Mean Count Rate", f"{filtered_lc['counts'].mean():.2f}" if len(filtered_lc) > 0 else "0.0")
col_s3.metric("Max Count Rate", f"{filtered_lc['counts'].max():.2f}" if len(filtered_lc) > 0 else "0.0")
col_s4.metric("Zero Count Samples", int((filtered_lc["counts"] == 0).sum()))
