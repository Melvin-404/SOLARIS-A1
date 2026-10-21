"""Page 5: Candidate Flare Bursts (EDA) vs. Verified Ground-Truth Events."""

from pathlib import Path
import pandas as pd
import streamlit as st

from dashboard.loaders import (
    load_eda_candidates,
    load_policy_status,
    load_light_curve,
)
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from dashboard.components.figures import build_light_curve_figure
from solar_flare.paths import project_root

st.set_page_config(page_title="Events | SOLARIS-A1", page_icon="⚡", layout="wide")
render_sidebar_disclaimer()

st.title("⚡ Candidate Burst Intervals & Ground-Truth Events")
st.caption("Heuristic burst candidates from Stage 5 EDA vs. Gate G3 approved solar flare ground truth")

# 1. Unverified Candidate Banner
render_status_banner(
    "UNVERIFIED",
    "Candidate bursts identified via heuristic baseline deviations are NOT verified solar flares. "
    "Creating labels from intensity heuristics and subsequently evaluating models against them is circular and prohibited.",
    "Stage 5 EDA",
)

st.markdown("---")

# 2. Candidate Burst Intervals Table
st.header("1. Exploratory Candidate Burst Intervals (Stage 5)")
bursts_res = load_eda_candidates()

candidate_intervals_for_plot = []
selected_cand_idx = None

if bursts_res.status == "MISSING":
    st.info("No candidate burst table found at results/eda/candidate_bursts.csv.")
elif bursts_res.status == "ERROR":
    render_status_banner("ERROR", bursts_res.message, "Candidate Bursts")
elif bursts_res.status == "EMPTY":
    st.info("Candidate bursts table is empty (zero bursts detected).")
else:
    df_bursts = bursts_res.data.copy()
    df_bursts["status"] = "CANDIDATE — UNVERIFIED"
    st.dataframe(df_bursts, use_container_width=True)

    # Allow selecting a candidate to overlay on light curve
    st.markdown("### Candidate Burst Overlay on Light Curve")
    cand_options = [f"Burst #{i}: t={row.get('start_time', 0.0):.1f} s to {row.get('end_time', 0.0):.1f} s" for i, row in df_bursts.iterrows()]
    sel_cand = st.selectbox("Select Candidate to Highlight", ["None"] + cand_options)

    if sel_cand != "None":
        idx = cand_options.index(sel_cand)
        row = df_bursts.iloc[idx]
        st_sec = float(row.get("start_time", 0.0))
        en_sec = float(row.get("end_time", 0.0))
        candidate_intervals_for_plot.append((st_sec, en_sec, "candidate (unverified)"))

        # Load light curve around the candidate
        lc_res = load_light_curve()
        if lc_res.is_ok and isinstance(lc_res.data, pd.DataFrame):
            df_lc = lc_res.data
            padding = 300.0  # 5 min before and after
            sub_lc = df_lc[(df_lc["time"] >= st_sec - padding) & (df_lc["time"] <= en_sec + padding)]

            fig, _ = build_light_curve_figure(
                df=sub_lc,
                time_col="time",
                count_col="counts",
                candidate_intervals=candidate_intervals_for_plot,
            )
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# 3. Verified Ground-Truth Events Section
st.header("2. Verified Ground-Truth Solar Flare Events (Gate G3)")

root = project_root()
approved_events_file = root / "data" / "manifests" / "event_records_approved.csv"
policy_res = load_policy_status()
is_policy_approved = policy_res.data.get("approved", False)

if approved_events_file.is_file() and is_policy_approved:
    try:
        df_events = pd.read_csv(approved_events_file)
        st.success("Formally approved ground-truth events loaded.")
        st.dataframe(df_events, use_container_width=True)
    except Exception as exc:
        render_status_banner("ERROR", f"Failed to parse approved events: {exc}", "Events")
else:
    st.info("ℹ️ **No approved event records available. Verified-event inspection is not yet possible.**")
    st.caption(
        "Gate G3 human approval of docs/08_labelling_policy.md and external catalogue confirmation "
        "is required before ground-truth solar flare event records can be displayed or evaluated."
    )
