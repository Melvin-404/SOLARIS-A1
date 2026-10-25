"""Page 5: Verified Ground-Truth Flare Events vs. Exploratory Candidate Bursts."""

from __future__ import annotations

import math
from pathlib import Path
import pandas as pd
import streamlit as st

from dashboard.loaders import (
    load_eda_candidates,
    load_policy_status,
    load_light_curve,
    load_approved_events,
    format_approved_event_record,
)
from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from dashboard.components.figures import build_light_curve_figure
from dashboard.components.theme import apply_space_weather_theme, render_source_badge
from solar_flare.paths import project_root

st.set_page_config(page_title="Events | SOLARIS-A1", page_icon="⚡", layout="wide")
apply_space_weather_theme()
render_sidebar_disclaimer()

col_t, col_b = st.columns([3, 1])
with col_t:
    st.title("Solar Flare Events: Verified Catalog vs. Exploratory Candidates")
    st.caption("Rigorous scientific separation between official NOAA SWPC ground-truth events and unverified heuristic burst candidates")
with col_b:
    render_source_badge("HISTORICAL")

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# ==============================================================================
# SECTION 1: OFFICIALLY VERIFIED GROUND-TRUTH EVENTS (GATE G3)
# ==============================================================================
st.subheader("1. Officially Verified Solar Flare Ground Truth (Gate G3)")
st.caption("Approved by Solar Physics Research Group (Dr. Melvin) based on independent NOAA SWPC Solar Event Reports.")

approved_res = load_approved_events()
policy_res = load_policy_status()
is_policy_approved = policy_res.data.get("approved", True) if policy_res.is_ok else True

if not approved_res.is_ok or approved_res.data is None or approved_res.data.empty:
    st.warning("Approved event records catalog not found at data/manifests/event_records_approved.csv.")
else:
    df_raw = approved_res.data
    total_approved = len(df_raw)

    st.markdown(
        f"""
        <div style="background-color: rgba(16, 185, 129, 0.08); border-left: 3px solid #10B981; padding: 8px 14px; border-radius: 4px; margin-bottom: 12px;">
            <strong style="color: #34D399;">Formally Approved Master Ground Truth (Decision D-14):</strong>
            <span style="color: #CBD5E1; font-size: 0.88rem;">
                Total of <strong>{total_approved} verified solar flare events</strong> representing the authoritative ground truth for all training, validation, and single-shot test evaluation.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Format all records through standardized parser
    formatted_records = [format_approved_event_record(row) for _, row in df_raw.iterrows()]
    df_events = pd.DataFrame(formatted_records)

    # 1. Top-Line Catalog Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Approved Events", f"{total_approved} Events", "Gate G3 Attested")
    with m2:
        pilot_cnt = sum(1 for r in formatted_records if r["cohort"] == "October 2026 Pilot")
        st.metric("October 2026 Pilot", f"{pilot_cnt} Events", "Active Orbit SDD2")
    with m3:
        july_cnt = sum(1 for r in formatted_records if r["cohort"] == "July 2024 Benchmark")
        st.metric("July 2024 Multi-Orbit", f"{july_cnt} Events", "44.77 Science Hours")
    with m4:
        x_cnt = sum(1 for r in formatted_records if r["flare_group"] == "X-Class")
        m_cnt = sum(1 for r in formatted_records if r["flare_group"] == "M-Class")
        st.metric("High-Intensity Flares", f"{x_cnt} X-Class | {m_cnt} M-Class", "NOAA GOES Verified")

    # 2. Interactive Filter Controls
    st.markdown("#### Search and Filter Approved Event Catalog")
    f_col1, f_col2, f_col3, f_col4 = st.columns([1.2, 1, 1.2, 1.6])

    with f_col1:
        cohort_options = ["All Cohorts (119)", "October 2026 Pilot (2)", "July 2024 Benchmark (117)"]
        sel_cohort = st.selectbox("Filter by Cohort", cohort_options, index=0)

    with f_col2:
        class_options = ["All Classes", "X-Class", "M-Class", "C-Class"]
        sel_class = st.selectbox("Filter by Flare Class", class_options, index=0)

    with f_col3:
        unique_dates = sorted(list({r["observation_date"] for r in formatted_records if r["observation_date"] != "Unavailable"}))
        date_options = ["All Dates"] + unique_dates
        sel_date = st.selectbox("Filter by Observation Date", date_options, index=0)

    with f_col4:
        search_query = st.text_input("Search (Notes, Region, Event ID, Class)", value="", placeholder="e.g. AR3738, X1.2, EVT_20261018")

    # Apply Filters
    filtered_events = formatted_records

    if "October 2026" in sel_cohort:
        filtered_events = [r for r in filtered_events if r["cohort"] == "October 2026 Pilot"]
    elif "July 2024" in sel_cohort:
        filtered_events = [r for r in filtered_events if r["cohort"] == "July 2024 Benchmark"]

    if sel_class != "All Classes":
        filtered_events = [r for r in filtered_events if r["flare_group"] == sel_class]

    if sel_date != "All Dates":
        filtered_events = [r for r in filtered_events if r["observation_date"] == sel_date]

    if search_query.strip():
        q = search_query.strip().lower()
        filtered_events = [
            r for r in filtered_events
            if q in r["event_id"].lower()
            or q in r["classification"].lower()
            or q in r["notes"].lower()
            or q in r["source_id"].lower()
        ]

    n_filtered = len(filtered_events)

    # 3. Pagination Controls
    p_col1, p_col2 = st.columns([2, 1])
    with p_col1:
        st.markdown(f"**Showing {n_filtered} matching events** (out of {total_approved} total approved records)")
    with p_col2:
        page_size_options = [15, 25, 50, 100]
        sel_page_size = st.selectbox("Page Size", page_size_options, index=0, key="events_page_size")

    total_pages = max(1, math.ceil(n_filtered / sel_page_size))

    if total_pages > 1:
        cur_page = st.number_input(f"Page (1 to {total_pages})", min_value=1, max_value=total_pages, value=1, step=1)
    else:
        cur_page = 1

    start_idx = (cur_page - 1) * sel_page_size
    end_idx = min(start_idx + sel_page_size, n_filtered)
    page_events = filtered_events[start_idx:end_idx]

    # 4. Paginated Table Display
    # Columns prioritize scientific time, class, duration, and authority, keeping ID secondary
    table_rows = []
    for r in page_events:
        table_rows.append({
            "Peak Time (UTC)": r["peak_time_utc"],
            "Flare Class": r["classification"],
            "Cohort": r["cohort"],
            "Duration": r["duration"],
            "Authority": r["source_id"],
            "Scientific Notes": r["notes"][:65] + "..." if len(r["notes"]) > 65 else r["notes"],
            "Event ID": r["event_id"],
        })

    if table_rows:
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No approved events match the current filter criteria.")

    # 5. Expandable Event Details & Provenance Inspector (On Demand)
    event_choices = [f"{r['classification']} | {r['peak_time_utc']} | ID: {r['event_id']}" for r in filtered_events]

    if event_choices:
        sel_choice = st.selectbox("Select Event for Technical Provenance Inspection", event_choices, index=0)
        sel_idx = event_choices.index(sel_choice)
        sel_record = filtered_events[sel_idx]

        with st.expander(f"Technical Provenance: {sel_record['event_id']} (Flare {sel_record['classification']})", expanded=False):
            det_c1, det_c2, det_c3 = st.columns(3)
            with det_c1:
                st.markdown(f"**Event Identifier:** `{sel_record['event_id']}`")
                st.markdown(f"**Flare Classification:** `{sel_record['classification']}` ({sel_record['flare_group']})")
                st.markdown(f"**Observation Cohort:** {sel_record['cohort']}")
                st.markdown(f"**Observation Date:** `{sel_record['observation_date']}`")
            with det_c2:
                st.markdown(f"**Peak Timestamp:** `{sel_record['peak_time_utc']}`")
                st.markdown(f"**Onset Timestamp:** `{sel_record['onset_time_utc']}`")
                st.markdown(f"**End Timestamp:** `{sel_record['end_time_utc']}`")
                st.markdown(f"**Event Duration:** {sel_record['duration']}")
            with det_c3:
                st.markdown(f"**Catalog Source:** `{sel_record['source_id']}`")
                st.markdown(f"**Classification Method:** `{sel_record['classification_method']}`")
                st.markdown(f"**Timing Uncertainty:** `{sel_record['uncertainty_seconds']}`")
                st.markdown(f"**Peak Epoch Seconds:** `{sel_record['peak_time_epoch']}`")

            st.markdown(f"**Provenance Notes & Active Region:** {sel_record['notes'] or 'None recorded.'}")

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# ==============================================================================
# SECTION 2: EXPLORATORY CANDIDATE BURST INTERVALS (PROGRESSIVE DISCLOSURE)
# ==============================================================================
with st.expander("Exploratory Candidate Burst Intervals (Stage 5 EDA — Unverified)", expanded=False):
    st.markdown(
        """
        <div style="background-color: rgba(245, 158, 11, 0.08); border-left: 3px solid #F59E0B; padding: 8px 14px; border-radius: 4px; margin-bottom: 12px;">
            <strong style="color: #FBBF24;">CRITICAL SCIENTIFIC INTEGRITY RULE — HEURISTIC CANDIDATES ARE NOT GROUND TRUTH:</strong>
            <p style="margin: 4px 0 0 0; color: #CBD5E1; font-size: 0.85rem; line-height: 1.45;">
                The intervals below were flagged during exploratory data analysis using statistical intensity deviations above baseline.
                <strong>Creating training labels from heuristic threshold deviations and subsequently training or evaluating models against them is circular and strictly prohibited.</strong>
                These candidates are exploratory only.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    bursts_res = load_eda_candidates()

    if bursts_res.status == "MISSING":
        st.info("No candidate burst table found at results/eda/candidate_bursts.csv.")
    elif bursts_res.status == "ERROR":
        render_status_banner("ERROR", bursts_res.message, "Candidate Bursts")
    elif bursts_res.status == "EMPTY":
        st.info("Candidate bursts table is empty (zero bursts detected).")
    else:
        df_bursts = bursts_res.data.copy()
        st.markdown(f"**Exploratory Candidates Detected:** {len(df_bursts)} candidate intervals")
        st.dataframe(df_bursts, use_container_width=True)

        # Interactive Candidate Overlay on Light Curve
        st.markdown("#### Inspect Candidate Burst on Light Curve")

        start_col = "start" if "start" in df_bursts.columns else "start_time"
        end_col = "end" if "end" in df_bursts.columns else "end_time"

        cand_options = []
        for i, row in df_bursts.iterrows():
            cid = row.get("candidate_id", f"Burst #{i+1}")
            s_val = float(row.get(start_col, 0.0))
            e_val = float(row.get(end_col, 0.0))
            cand_options.append(f"{cid} (t = {s_val:.1f}s to {e_val:.1f}s)")

        sel_cand = st.selectbox("Select Candidate Interval to Zoom and Inspect", ["None"] + cand_options)

        if sel_cand != "None":
            idx = cand_options.index(sel_cand)
            row = df_bursts.iloc[idx]
            st_sec = float(row.get(start_col, 0.0))
            en_sec = float(row.get(end_col, 0.0))
            candidate_intervals_for_plot = [(st_sec, en_sec, "candidate (unverified)")]

            lc_res = load_light_curve("AL1_SOLEXS_20261018_SDD2_L1")
            if lc_res.is_ok and isinstance(lc_res.data, pd.DataFrame):
                df_lc = lc_res.data
                padding = 300.0  # 5 min before and after
                sub_lc = df_lc[(df_lc["time"] >= st_sec - padding) & (df_lc["time"] <= en_sec + padding)]

                fig, _ = build_light_curve_figure(
                    df=sub_lc,
                    time_col="time",
                    count_col="counts",
                    candidate_intervals=candidate_intervals_for_plot,
                    time_axis_mode="elapsed_hours",
                )
                st.plotly_chart(fig, use_container_width=True)
