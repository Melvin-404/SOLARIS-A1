"""Page 10: Upload Dataset & Predict — Single-Day SoLEXS Solar Flare Detection.

Allows users to upload a single day's Aditya-L1 SoLEXS observation dataset (FITS or CSV),
with optional Good Time Interval (GTI) files, validates the telemetry quality without
interpolating across telemetry gaps, computes the exact 19 causal features, and executes
inference using the existing frozen trained model.

STRICT CONSTRAINTS:
1. Zero training or fine-tuning: Never invokes fit(), train(), or retrain().
2. Zero model mutation: Model weights and artifacts remain strictly untouched.
3. No interpolation: Telemetry gaps are never bridged or synthetic data substituted.
4. Distinguishes Task A (in-situ flare detection) from Task B (advance flare forecasting).
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.banner import render_sidebar_disclaimer
from dashboard.components.figures import build_light_curve_figure
from dashboard.components.theme import apply_space_weather_theme, render_source_badge
from solar_flare.inference.pipeline import (
    DEFAULT_PROFILE_ID,
    EXPERIMENT_PROFILES,
    InferencePipeline,
    classify_risk,
    get_default_pipeline,
    get_pipeline,
)
from solar_flare.inference.upload_service import (
    UploadValidationError,
    execute_dataset_inference,
    extract_zip_observation,
    inspect_uploaded_zip,
    parse_uploaded_gti,
    parse_uploaded_lightcurve,
    process_uploaded_zip,
    validate_uploaded_telemetry,
)
from solar_flare.paths import project_root

# Page Configuration
st.set_page_config(
    page_title="Upload & Predict | SOLARIS-A1",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_space_weather_theme()
render_sidebar_disclaimer()

# Header
col_title, col_badge = st.columns([3, 1])
with col_title:
    st.title("Upload Dataset & Predict")
    st.caption("Upload a single-day Aditya-L1 SoLEXS observation and detect solar flare activity using the existing trained model.")

with col_badge:
    render_source_badge("USER UPLOAD")

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Prominent Scientific Scope Advisory
# -----------------------------------------------------------------------------
st.info(
    "**SCIENTIFIC NOTICE — TASK A (FLARE DETECTION)**: This interface analyzes in-window soft X-ray "
    "telemetry to detect active solar flare signatures occurring within 60-second observation intervals. "
    "It **does NOT forecast future solar flares** hours in advance (Task B). All predictions are generated "
    "by the existing frozen model without any fine-tuning or retraining."
)

# -----------------------------------------------------------------------------
# Sidebar: Model Registry & Inference Configuration
# -----------------------------------------------------------------------------
st.sidebar.markdown("### Model Configuration")

profile_options = {
    "pilot_20261018": "● [DEFAULT] October 2026 Pilot Baseline",
    "expanded_july2024": "● [BENCHMARK] July 2024 Expanded Benchmark",
}

selected_profile_key = st.sidebar.selectbox(
    "Experiment Profile",
    options=list(profile_options.keys()),
    index=0,
    format_func=lambda k: profile_options[k],
    help="Select the experiment profile whose frozen trained model will evaluate the uploaded dataset.",
)

selected_model_name = st.sidebar.selectbox(
    "Model Family",
    options=["xgboost", "random_forest", "logistic_regression"],
    index=0,
    format_func=lambda name: {
        "xgboost": "XGBoost Classifier (Primary)",
        "random_forest": "Random Forest Classifier",
        "logistic_regression": "Logistic Regression (Linear)",
    }.get(name, name),
    help="Select the model architecture. XGBoost is the primary recommended model.",
)

decision_threshold = st.sidebar.slider(
    "Decision Threshold",
    min_value=0.10,
    max_value=0.90,
    value=0.50,
    step=0.05,
    help="Probability cut-off for binary flare detection. Scores >= threshold classify as Flare Detected.",
)

stride_seconds_val = st.sidebar.selectbox(
    "Sliding Window Stride",
    options=[10.0, 30.0, 60.0],
    index=1,
    format_func=lambda s: f"{int(s)}s stride ({'fine resolution' if s==10 else 'standard balanced' if s==30 else 'non-overlapping'})",
    help="Time step between consecutive 60-second sliding windows. 30s is the standard evaluation stride.",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Demo Telemetry")
st.sidebar.caption("Load authentic Aditya-L1 SoLEXS raw observation files directly from the repository.")

demo_dataset_selected = st.sidebar.selectbox(
    "Select Demo Dataset",
    options=[
        "None (Upload my own)",
        "2024-07-13 Benchmark (ZIP Package: LC + GTI)",
        "2026-10-18 Pilot (FITS .lc.gz + GTI)",
        "2024-07-01 Benchmark (FITS .lc.gz + GTI)",
    ],
    index=0,
)

# Initialize Session State
if "uploaded_lc_df" not in st.session_state:
    st.session_state["uploaded_lc_df"] = None
if "uploaded_lc_meta" not in st.session_state:
    st.session_state["uploaded_lc_meta"] = None
if "uploaded_gti_list" not in st.session_state:
    st.session_state["uploaded_gti_list"] = None
if "uploaded_quality_audit" not in st.session_state:
    st.session_state["uploaded_quality_audit"] = None
if "inference_results" not in st.session_state:
    st.session_state["inference_results"] = None
if "active_source_name" not in st.session_state:
    st.session_state["active_source_name"] = None
if "zip_inspection" not in st.session_state:
    st.session_state["zip_inspection"] = None


# Helper to load demo files
def _load_demo(date_str: str) -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]], Optional[List[Tuple[float, float]]], Optional[str]]:
    raw_dir = project_root() / "data" / "raw"
    if date_str == "2024-07-13-zip":
        lc_path = raw_dir / "AL1_SOLEXS_20240713_SDD2_L1.lc.gz"
        gti_path = raw_dir / "AL1_SOLEXS_20240713_SDD2_L1.gti.gz"
        if not lc_path.exists() or not gti_path.exists():
            st.error("Demo files missing in data/raw")
            return None, None, None, None

        # Build in-memory zip
        import zipfile
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(lc_path.name, lc_path.read_bytes())
            zf.writestr(gti_path.name, gti_path.read_bytes())
        zip_bytes = zip_buf.getvalue()

        df, meta, gtis, insp = process_uploaded_zip(zip_bytes, "demo_solexs_20240713_package.zip")
        st.session_state["zip_inspection"] = insp
        return df, meta, gtis, "demo_solexs_20240713_package.zip"

    elif date_str == "2026-10-18":
        lc_path = raw_dir / "AL1_SOLEXS_20261018_SDD2_L1.lc.gz"
        gti_path = raw_dir / "AL1_SOLEXS_20261018_SDD2_L1.gti.gz"
        source_name = "AL1_SOLEXS_20261018_SDD2_L1.lc.gz"
    else:
        lc_path = raw_dir / "AL1_SOLEXS_20240701_SDD2_L1.lc.gz"
        gti_path = raw_dir / "AL1_SOLEXS_20240701_SDD2_L1.gti.gz"
        source_name = "AL1_SOLEXS_20240701_SDD2_L1.lc.gz"

    if not lc_path.exists():
        st.error(f"Demo file not found at {lc_path}")
        return None, None, None, None

    with open(lc_path, "rb") as f:
        df, meta = parse_uploaded_lightcurve(f.read(), lc_path.name)

    gtis = None
    if gti_path.exists():
        with open(gti_path, "rb") as f:
            gtis, _ = parse_uploaded_gti(f.read(), gti_path.name)

    return df, meta, gtis, source_name


# Handle Demo Dataset Trigger
if demo_dataset_selected != "None (Upload my own)":
    demo_key = "2024-07-13-zip" if "ZIP Package" in demo_dataset_selected else ("2026-10-18" if "2026-10-18" in demo_dataset_selected else "2024-07-01")
    if st.session_state.get("last_demo_date") != demo_key:
        d_df, d_meta, d_gtis, d_src = _load_demo(demo_key)
        if d_df is not None:
            st.session_state["uploaded_lc_df"] = d_df
            st.session_state["uploaded_lc_meta"] = d_meta
            st.session_state["uploaded_gti_list"] = d_gtis
            st.session_state["uploaded_quality_audit"] = validate_uploaded_telemetry(d_df, d_gtis)
            st.session_state["active_source_name"] = d_src
            st.session_state["last_demo_date"] = demo_key
            st.session_state["inference_results"] = None  # Reset prediction on file change
else:
    if st.session_state.get("last_demo_date") is not None:
        st.session_state["last_demo_date"] = None

# =============================================================================
# 1. Upload Interface
# =============================================================================
st.subheader("1. Telemetry Upload")
st.markdown(
    "Upload a single day's Aditya-L1 SoLEXS Level-1 observation. "
    "You can upload a **Complete Observation ZIP Package (`.zip`)** containing matching light-curve and GTI files, "
    "or upload **Individual Files** (`.lc`, `.lc.gz`, `.fits`, `.fits.gz`, `.csv`)."
)

upload_mode = st.radio(
    "Select Telemetry Upload Method",
    [
        "📦 Complete ZIP Archive (.zip)",
        "📄 Separate Telemetry Files (.lc, .fits, .csv)",
    ],
    horizontal=True,
    help="Upload either a single .zip archive containing observation files, or upload separate light-curve and GTI files.",
)

if upload_mode == "📦 Complete ZIP Archive (.zip)":
    uploaded_zip = st.file_uploader(
        "Upload Observation ZIP Archive (Required)",
        type=["zip"],
        help="Single-day SoLEXS ZIP package containing light curve (e.g. AL1_SOLEXS_20240713_SDD2_L1.lc.gz) and optional matching GTI file. Extracted strictly in-memory.",
        key="uploader_zip",
    )

    if uploaded_zip is not None:
        try:
            zip_bytes = uploaded_zip.getvalue()
            inspection = inspect_uploaded_zip(zip_bytes, uploaded_zip.name)
            st.session_state["zip_inspection"] = inspection

            obs_dict = inspection["observations"]
            chosen_obs_key = None

            # Requirement 7: Multiple observation days in ZIP
            if inspection["has_multiple_observations"]:
                st.warning(
                    f"Archive contains {len(obs_dict)} distinct observation days. "
                    "Please select which observation to analyze:"
                )
                chosen_obs_key = st.selectbox(
                    "Select Observation Day from Archive",
                    options=list(obs_dict.keys()),
                    format_func=lambda k: f"{obs_dict[k]['display_label']} — [{'GTI included' if obs_dict[k]['has_gti'] else 'No GTI'}]",
                    key="zip_obs_selector",
                )
            else:
                chosen_obs_key = list(obs_dict.keys())[0]

            matched_info = obs_dict[chosen_obs_key]

            # Display ZIP Contents card (Requirement 13)
            gti_label = f"<code>{matched_info['gti_filename']}</code> ({matched_info['gti_size_bytes']/1024:.1f} KB)" if matched_info["has_gti"] else "None (Full Observation Assumed)"
            st.markdown(
                f"""
                <div class="flare-card" style="margin-bottom: 14px; border-left: 4px solid #38BDF8;">
                    <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 14px;">
                        <div>
                            <span style="font-size: 0.78rem; font-weight: 700; color: #38BDF8; letter-spacing: 0.05em; text-transform: uppercase;">Archive Package</span>
                            <div style="font-size: 1.05rem; font-weight: 600; color: #F8FAFC; margin-top: 2px;"><code>{uploaded_zip.name}</code> ({len(zip_bytes)/1024:.1f} KB)</div>
                        </div>
                        <div>
                            <span style="font-size: 0.78rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; text-transform: uppercase;">Observation Date</span>
                            <div style="font-size: 1.00rem; font-weight: 600; color: #FBBF24; margin-top: 2px;">{matched_info['observation_date']}</div>
                        </div>
                        <div>
                            <span style="font-size: 0.78rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; text-transform: uppercase;">Matched Light Curve</span>
                            <div style="font-size: 0.95rem; font-weight: 500; color: #E2E8F0; margin-top: 2px;"><code>{matched_info['lc_filename']}</code> ({matched_info['lc_size_bytes']/1024:.1f} KB)</div>
                        </div>
                        <div>
                            <span style="font-size: 0.78rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; text-transform: uppercase;">Matched GTI File</span>
                            <div style="font-size: 0.95rem; font-weight: 500; color: #10B981; margin-top: 2px;">{gti_label}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if inspection["warnings"]:
                for w in inspection["warnings"]:
                    st.info(f"ℹ️ {w}")

            # Process chosen observation entirely in memory (Zero disk write)
            df_parsed, meta_parsed, gti_list, _ = process_uploaded_zip(
                zip_bytes,
                uploaded_zip.name,
                observation_key=chosen_obs_key,
            )

            quality_audit = validate_uploaded_telemetry(df_parsed, gti_list)

            st.session_state["uploaded_lc_df"] = df_parsed
            st.session_state["uploaded_lc_meta"] = meta_parsed
            st.session_state["uploaded_gti_list"] = gti_list
            st.session_state["uploaded_quality_audit"] = quality_audit
            st.session_state["active_source_name"] = f"{uploaded_zip.name} :: {matched_info['lc_filename']}"

        except UploadValidationError as e:
            st.error(f"**ZIP Archive Validation Error**: {str(e)}")
            st.session_state["uploaded_lc_df"] = None
            st.session_state["uploaded_quality_audit"] = None
        except Exception as e:
            st.error(f"**Unexpected Processing Error**: {str(e)}")
            st.session_state["uploaded_lc_df"] = None
            st.session_state["uploaded_quality_audit"] = None

else:
    # Individual Files pathway (preserved)
    col_up_lc, col_up_gti = st.columns(2)

    with col_up_lc:
        uploaded_lc = st.file_uploader(
            "Upload Light Curve File (Required)",
            type=["lc", "fits", "csv", "gz", "zip"],
            help="Single-day SoLEXS observation file (FITS, CSV, or ZIP). Gzip-compressed files and ZIP archives are automatically parsed in memory.",
            key="uploader_lc",
        )

    with col_up_gti:
        uploaded_gti = st.file_uploader(
            "Upload Good Time Interval (GTI) File (Optional)",
            type=["gti", "fits", "csv", "gz"],
            help="Optional GTI file defining valid science intervals (START and STOP times in MET seconds).",
            key="uploader_gti",
        )

    # Process User Uploads
    if uploaded_lc is not None:
        try:
            lc_bytes = uploaded_lc.getvalue()
            if uploaded_lc.name.lower().endswith(".zip"):
                df_parsed, meta_parsed, gti_list, _ = process_uploaded_zip(lc_bytes, uploaded_lc.name)
            else:
                df_parsed, meta_parsed = parse_uploaded_lightcurve(lc_bytes, uploaded_lc.name)
                gti_list = None
                if uploaded_gti is not None:
                    gti_bytes = uploaded_gti.getvalue()
                    gti_list, _ = parse_uploaded_gti(gti_bytes, uploaded_gti.name)

            quality_audit = validate_uploaded_telemetry(df_parsed, gti_list)

            # Store in state
            st.session_state["uploaded_lc_df"] = df_parsed
            st.session_state["uploaded_lc_meta"] = meta_parsed
            st.session_state["uploaded_gti_list"] = gti_list
            st.session_state["uploaded_quality_audit"] = quality_audit
            st.session_state["active_source_name"] = uploaded_lc.name

        except UploadValidationError as e:
            st.error(f"**Upload Validation Error**: {str(e)}")
            st.session_state["uploaded_lc_df"] = None
            st.session_state["uploaded_quality_audit"] = None
        except Exception as e:
            st.error(f"**Unexpected Processing Error**: {str(e)}")
            st.session_state["uploaded_lc_df"] = None
            st.session_state["uploaded_quality_audit"] = None

# =============================================================================
# 2. File Metadata & Validation Status Display
# =============================================================================
df_current = st.session_state["uploaded_lc_df"]
meta_current = st.session_state["uploaded_lc_meta"]
gtis_current = st.session_state["uploaded_gti_list"]
audit_current = st.session_state["uploaded_quality_audit"]
source_name = st.session_state["active_source_name"] or "No file uploaded"

if df_current is not None and meta_current is not None and audit_current is not None:
    st.markdown('<hr class="header-divider">', unsafe_allow_html=True)
    st.subheader("2. Telemetry Metadata & Quality Validation Audit")

    # Metadata Summary Bar
    m_date = meta_current.get("detected_date") or "Unknown Date"
    m_fmt = meta_current.get("format") or "Unknown Format"
    m_cols = ", ".join(meta_current.get("original_columns", ["time", "counts"]))
    m_recs = f"{len(df_current):,}"
    m_dur_hrs = f"{audit_current.get('duration_seconds', 0.0) / 3600.0:.2f} hrs"
    m_status = audit_current.get("status", "UNKNOWN")
    m_status_color = "#10B981" if m_status == "PASSED" else "#F59E0B" if m_status == "PASSED_WITH_WARNINGS" else "#EF4444"

    st.markdown(
        f"""
        <div class="flare-card" style="margin-bottom: 16px;">
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 14px;">
                <div>
                    <span style="font-size: 0.78rem; font-weight: 700; color: #38BDF8; letter-spacing: 0.05em; text-transform: uppercase;">Observation Source</span>
                    <div style="font-size: 1.05rem; font-weight: 600; color: #F8FAFC; margin-top: 2px;"><code>{source_name}</code></div>
                </div>
                <div>
                    <span style="font-size: 0.78rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; text-transform: uppercase;">Observation Date</span>
                    <div style="font-size: 1.00rem; font-weight: 600; color: #FBBF24; margin-top: 2px;">{m_date}</div>
                </div>
                <div>
                    <span style="font-size: 0.78rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; text-transform: uppercase;">Records / Cadence</span>
                    <div style="font-size: 1.00rem; font-weight: 500; color: #E2E8F0; margin-top: 2px;">{m_recs} ({audit_current.get('cadence_median', 1.0):.1f}s)</div>
                </div>
                <div>
                    <span style="font-size: 0.78rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; text-transform: uppercase;">Time Coverage</span>
                    <div style="font-size: 1.00rem; font-weight: 500; color: #E2E8F0; margin-top: 2px;">{m_dur_hrs}</div>
                </div>
                <div>
                    <span style="font-size: 0.78rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; text-transform: uppercase;">Validation Status</span>
                    <div style="font-size: 1.00rem; font-weight: 700; color: {m_status_color}; margin-top: 2px;">{m_status}</div>
                </div>
            </div>
            <div style="margin-top: 10px; font-size: 0.82rem; color: #94A3B8; border-top: 1px solid #1E293B; padding-top: 8px;">
                <b>Detected Format:</b> {m_fmt} &nbsp;|&nbsp; <b>Parsed Columns:</b> <code>{m_cols}</code> &nbsp;|&nbsp; <b>GTI Intervals:</b> {len(gtis_current) if gtis_current else 'None (Full Coverage Assumed)'}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Detailed Quality Metrics
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    with q_col1:
        st.metric("Total Records", f"{audit_current['n_records']:,}")
    with q_col2:
        nan_pct = audit_current["non_finite_pct"]
        st.metric("NaN / Missing Values", f"{audit_current['n_non_finite']:,} ({nan_pct:.2f}%)")
    with q_col3:
        neg_pct = audit_current["negative_pct"]
        st.metric("Negative Values", f"{audit_current['n_negative']:,} ({neg_pct:.2f}%)")
    with q_col4:
        gaps_cnt = audit_current["n_telemetry_gaps"]
        st.metric("Telemetry Gaps (>3s)", f"{gaps_cnt} gaps")

    # Display Quality Warnings if any
    if audit_current.get("warnings"):
        with st.expander("Quality & Data Integrity Advisories", expanded=True):
            for w in audit_current["warnings"]:
                st.warning(f"⚠️ {w}")
            st.caption("Telemetry gaps and invalid samples are strictly dropped during segmentation; they are NEVER interpolated.")

    # -------------------------------------------------------------------------
    # 3. Prediction Execution Button
    # -------------------------------------------------------------------------
    st.markdown('<hr class="header-divider">', unsafe_allow_html=True)
    st.subheader("3. Model Inference Execution")

    run_col1, run_col2 = st.columns([1, 3])
    with run_col1:
        run_prediction = st.button("🚀 Run Flare Prediction", type="primary", use_container_width=True)

    with run_col2:
        st.caption(
            f"Using **{selected_model_name.upper()}** from **{selected_profile_key}** with decision threshold **{decision_threshold:.2f}** "
            f"and sliding window stride **{int(stride_seconds_val)}s**. Zero retraining or model modifications will occur."
        )

    if run_prediction:
        with st.spinner("Executing causally sound feature generation and model inference..."):
            try:
                # Load existing frozen model pipeline
                pipeline = get_pipeline(
                    selected_profile_key,
                    model_name=selected_model_name,
                )

                # Execute end-to-end dataset inference
                inference_out = execute_dataset_inference(
                    df=df_current,
                    gti_intervals=gtis_current,
                    pipeline=pipeline,
                    threshold=decision_threshold,
                    window_seconds=60.0,
                    stride_seconds=stride_seconds_val,
                    max_gap_seconds=3.0,
                    min_segment_seconds=60.0,
                )

                st.session_state["inference_results"] = inference_out
                st.success("✅ Inference completed successfully!")

            except UploadValidationError as e:
                st.error(f"Inference Incompatibility: {str(e)}")
            except Exception as e:
                st.error(f"Inference Pipeline Error: {str(e)}")

# =============================================================================
# 4. Results & Visualizations
# =============================================================================
results_payload = st.session_state.get("inference_results")

if results_payload is not None:
    res_summary = results_payload["summary"]
    res_df = results_payload["results_df"]
    feat_df = results_payload["features_df"]
    candidate_episodes = results_payload["candidate_episodes"]
    exclusions = results_payload["exclusions"]

    st.markdown('<hr class="header-divider">', unsafe_allow_html=True)
    st.subheader("4. Solar Flare Detection Results")

    # Metric Banner
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Windows Evaluated", f"{res_summary['total_windows_evaluated']:,}")
    with col_m2:
        n_flaring = res_summary["flaring_windows_detected"]
        pct_flaring = (n_flaring / max(1, res_summary['total_windows_evaluated'])) * 100.0
        st.metric("Flare Windows Detected", f"{n_flaring:,} ({pct_flaring:.1f}%)")
    with col_m3:
        st.metric("Candidate Flare Episodes", f"{len(candidate_episodes)}")
    with col_m4:
        max_prob = res_df["flare_probability"].max() if not res_df.empty else 0.0
        peak_risk = classify_risk(max_prob)
        st.metric("Peak Probability / Risk", f"{max_prob:.4f}", delta=peak_risk)

    # -------------------------------------------------------------------------
    # Observation Light Curve with Flare Overlays
    # -------------------------------------------------------------------------
    st.markdown("#### A. Observed X-Ray Light Curve & Candidate Flare Intervals")

    # Prepare candidate interval tuples for build_light_curve_figure: (start, stop, label)
    cand_tuples = [
        (float(ep["start_sec"]), float(ep["end_sec"]), f"{ep['episode_id']} ({ep['risk_level']})")
        for ep in candidate_episodes
    ]

    fig_lc, _ = build_light_curve_figure(
        df=df_current,
        time_col="time",
        count_col="counts",
        gti_intervals=gtis_current,
        candidate_intervals=cand_tuples if cand_tuples else None,
        log_scale=False,
        show_flagged=True,
        time_axis_mode="elapsed_hours",
    )
    fig_lc.update_layout(height=420, margin=dict(l=40, r=40, t=30, b=40))
    st.plotly_chart(fig_lc, use_container_width=True)

    # -------------------------------------------------------------------------
    # Detection Probability Timeline
    # -------------------------------------------------------------------------
    st.markdown("#### B. Model Flare Probability Timeline")

    t0 = float(df_current["time"].iloc[0])
    times_hr = (res_df["window_end"].values - t0) / 3600.0
    probs = res_df["flare_probability"].values
    detected_mask = res_df["flare_detected"].values

    fig_prob = go.Figure()

    # Threshold horizontal reference line
    fig_prob.add_shape(
        type="line",
        x0=times_hr.min() if len(times_hr) > 0 else 0,
        x1=times_hr.max() if len(times_hr) > 0 else 1,
        y0=decision_threshold,
        y1=decision_threshold,
        line=dict(color="#EF4444", width=1.5, dash="dash"),
    )
    fig_prob.add_annotation(
        x=times_hr.min() if len(times_hr) > 0 else 0,
        y=decision_threshold,
        text=f"Decision Threshold ({decision_threshold:.2f})",
        showarrow=False,
        yshift=10,
        font=dict(color="#EF4444", size=10),
    )

    # Non-flaring windows trace
    if np.any(~detected_mask):
        fig_prob.add_trace(
            go.Scatter(
                x=times_hr[~detected_mask],
                y=probs[~detected_mask],
                customdata=res_df.loc[~detected_mask, "window_end"].values,
                mode="markers",
                name="Nominal / Quiet Window",
                marker=dict(color="#38BDF8", size=5, opacity=0.7),
                hovertemplate="<b>Orbit:</b> %{x:.2f}h<br><b>MET:</b> %{customdata:.1f}s<br><b>Flare Prob:</b> %{y:.4f}<extra></extra>",
            )
        )

    # Flaring windows trace
    if np.any(detected_mask):
        fig_prob.add_trace(
            go.Scatter(
                x=times_hr[detected_mask],
                y=probs[detected_mask],
                customdata=res_df.loc[detected_mask, "window_end"].values,
                mode="markers",
                name="Flare Detected Window",
                marker=dict(color="#F59E0B", size=8, symbol="diamond", line=dict(color="#EF4444", width=1)),
                hovertemplate="<b>Orbit:</b> %{x:.2f}h<br><b>MET:</b> %{customdata:.1f}s<br><b>Flare Prob:</b> %{y:.4f} (FLARE)<extra></extra>",
            )
        )

    fig_prob.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0E1526",
        plot_bgcolor="#070B14",
        height=320,
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(title="Elapsed Observation Time (Hours from Start)", gridcolor="#1E293B", color="#CBD5E1"),
        yaxis=dict(title="Flare Probability", range=[-0.05, 1.05], gridcolor="#1E293B", color="#CBD5E1"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
    )
    st.plotly_chart(fig_prob, use_container_width=True)

    # -------------------------------------------------------------------------
    # Candidate Flare Episodes Table
    # -------------------------------------------------------------------------
    st.markdown("#### C. Detected Candidate Flare Episodes")
    if candidate_episodes:
        episodes_df = pd.DataFrame(candidate_episodes)
        st.dataframe(
            episodes_df.style.format({
                "start_sec": "{:.1f}",
                "end_sec": "{:.1f}",
                "duration_sec": "{:.0f}s",
                "peak_probability": "{:.4f}",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No contiguous candidate flare episodes met or exceeded the decision threshold during this observation.")

    # -------------------------------------------------------------------------
    # Detailed Window Inference Table & Filter
    # -------------------------------------------------------------------------
    st.markdown("#### D. Sliding Window Predictions Table")

    filter_choice = st.radio(
        "Filter Window Table",
        options=["All Windows", "Flaring Windows Only", "Nominal Windows Only"],
        horizontal=True,
    )

    if filter_choice == "Flaring Windows Only":
        display_res_df = res_df[res_df["flare_detected"]].copy()
    elif filter_choice == "Nominal Windows Only":
        display_res_df = res_df[~res_df["flare_detected"]].copy()
    else:
        display_res_df = res_df.copy()

    st.dataframe(
        display_res_df[[
            "window_id",
            "window_start",
            "window_end",
            "utc_time",
            "flare_probability",
            "flare_detected",
            "risk_level",
            "mean_count_rate",
            "peak_count_rate",
            "baseline_flux",
        ]].head(2000),
        use_container_width=True,
        hide_index=True,
    )

    # -------------------------------------------------------------------------
    # Download Results CSV
    # -------------------------------------------------------------------------
    st.markdown("#### E. Export Prediction Results")
    csv_bytes = res_df.to_csv(index=False).encode("utf-8")
    export_filename = f"solexs_flare_predictions_{m_date.replace('-', '')}.csv"

    st.download_button(
        label=f"📥 Download Full Prediction Results CSV ({len(res_df):,} records)",
        data=csv_bytes,
        file_name=export_filename,
        mime="text/csv",
        type="secondary",
    )

    # -------------------------------------------------------------------------
    # Scientific Integrity & Exclusions Audit Log
    # -------------------------------------------------------------------------
    with st.expander("Data Quality & Exclusions Audit Log", expanded=False):
        st.markdown(
            f"""
            - **Non-Finite Dropped:** {exclusions['n_nan_dropped']} samples
            - **Negative Counts Dropped:** {exclusions['n_negative_dropped']} samples
            - **Outside GTI Dropped:** {exclusions['n_outside_gti_dropped']} samples
            - **Short Segments Dropped (<60s):** {exclusions['n_short_segment_samples_dropped']} samples
            - **Continuous Science Segments Formed:** {len(results_payload['segments'])}
            - **Telemetry Gap Bridging:** STRICTLY FORBIDDEN (No interpolation performed)
            - **Model Used:** `{res_summary['model_name']}` from `{res_summary['profile_id']}`
            - **Execution Timestamp (UTC):** `{res_summary['execution_timestamp_utc']}`
            """
        )

else:
    if df_current is None:
        st.info("👆 Please upload a supported SoLEXS observation file (or select a demo dataset in the sidebar) to begin.")
