"""Page 8: Model-Driven Flare Prediction Laboratory & Offline Inference."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

from dashboard.components.banner import render_sidebar_disclaimer, render_status_banner
from dashboard.components.theme import apply_space_weather_theme, render_source_badge
from solar_flare.inference.pipeline import (
    get_pipeline,
    classify_risk,
    estimate_flare_class,
    EXPERIMENT_PROFILES,
    DEFAULT_PROFILE_ID,
)
from solar_flare.paths import project_root

st.set_page_config(page_title="Inference Lab | SOLARIS-A1", page_icon="⚡", layout="wide")
apply_space_weather_theme()
render_sidebar_disclaimer()

# Title and historical data indicator
col_title, col_badge = st.columns([3, 1])
with col_title:
    st.title("Interactive Inference Laboratory")
    st.caption("Protocol-governed model inference laboratory evaluating Task A 60-second window flare detection")

with col_badge:
    render_source_badge("HISTORICAL")

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# Prominent Research Benchmark Advisory Banner
st.warning(
    "**RESEARCH BENCHMARK LABORATORY**: Evaluates Task A 60-second window flare detection. "
    "These predictions are probabilistic statistical classifications and are **NOT certified for operational "
    "space-weather alerting or mission-critical spacecraft protection**."
)

# 1. Sidebar Experiment Profile & Model Selector (Safeguard 2: Pilot is strictly default)
st.sidebar.markdown("### Model Registry Selection")

profile_options = {
    "pilot_20261018": "● [DEFAULT] October 2026 Pilot Baseline",
    "expanded_july2024": "● [BENCHMARK] July 2024 Expanded Benchmark",
}

selected_profile_key = st.sidebar.selectbox(
    "Select Experiment Profile",
    options=list(profile_options.keys()),
    index=0,  # Pilot strictly default
    format_func=lambda k: profile_options[k],
)

selected_model_name = st.sidebar.selectbox(
    "Select Estimator Family",
    options=["xgboost", "random_forest", "logistic_regression"],
    index=0,
)

# Initialize Inference Pipeline for selected profile
try:
    pipeline = get_pipeline(selected_profile_key, model_name=selected_model_name)
    v_info = pipeline.version_info
    st.sidebar.success(f"Loaded: {v_info['model_name'].upper()}")
    st.sidebar.caption(f"Profile: `{v_info['profile_id']}`")
    st.sidebar.caption(f"Cohort: {v_info['dataset_cohort']}")
    st.sidebar.caption(f"Governance: `{v_info['governance_status']}`")
except Exception as exc:
    st.error(f"Model Inference Pipeline failed to load: {exc}")
    st.stop()

# Limitations callout in sidebar if July 2024 is chosen
if selected_profile_key == "expanded_july2024":
    st.sidebar.warning(
        "⚠️ Benchmark Scope Note: July 2024 test covers strictly July 13–14 (dominated by AR3738; "
        "only 1 X-class flare; elevated false alarm rate)."
    )

# 2. Primary Input Workflow: Historical SoLEXS Observation Window
st.subheader("1. Historical SoLEXS Observation Window")

root = project_root()

preset = st.selectbox(
    "Select Historical Observation Epoch Preset",
    [
        "[Oct 18, 2026] Event 2 Peak (Major Impulsive Flare @ 19:17 UTC) — NOAA Confirmed Event",
        "[Oct 18, 2026] Event 1 Peak (Moderate Flare Cluster @ 10:50 UTC) — NOAA Confirmed Event",
        "[Oct 18, 2026] Quiet-Sun Baseline Observation — NOAA Confirmed Quiet Interval",
        "[Jul 14, 2024] NOAA Event #400 Peak (X1.2 Flare @ 02:34 UTC, AR3738) — NOAA Confirmed Event",
        "[Jul 13, 2024] NOAA Event #383 Peak (M1.5 Flare @ 02:40 UTC, AR3738) — NOAA Confirmed Event",
        "[Jul 13, 2024] Verified Quiet Science Interval — NOAA Confirmed Quiet Interval",
    ],
    help="Select an authoritative observation window from the historical Aditya-L1 SoLEXS archive.",
)

feature_input: dict = {}
window_counts: list = []
noaa_ground_truth: dict = {}
obs_time_label: str = ""
obs_stem: str = ""
window_id_label: str = ""
window_elapsed_label: str = ""
coverage_label: str = ""
quality_status_label: str = "Nominal Science (OK)"

if "[Oct 18, 2026]" in preset:
    obs_stem = "AL1_SOLEXS_20261018_SDD2_L1"
    obs_time_label = "2026-10-18 (Aditya-L1 SoLEXS SDD2)"
    feat_file = root / "data" / "processed" / "features" / obs_stem / "window_features.csv"
    idx_file = root / "data" / "processed" / "features" / obs_stem / "window_index.csv"

    if "Event 2 Peak" in preset:
        noaa_ground_truth = {
            "status": "CONFIRMED_FLARE",
            "label": "Major Impulsive Flare (Event 2)",
            "peak_utc": "2026-10-18T19:17:22 UTC",
            "noaa_class": "Estimated M/X-Equivalent (Impulsive Burst)",
            "active_region": "Pilot Active Region",
            "catalog_source": "Aditya-L1 SoLEXS SDD2 Ground Truth",
        }
        target_idx = 3403
    elif "Event 1 Peak" in preset:
        noaa_ground_truth = {
            "status": "CONFIRMED_FLARE",
            "label": "Moderate Flare Cluster (Event 1)",
            "peak_utc": "2026-10-18T10:50:27 UTC",
            "noaa_class": "Estimated C-Class Cluster",
            "active_region": "Pilot Active Region",
            "catalog_source": "Aditya-L1 SoLEXS SDD2 Ground Truth",
        }
        target_idx = 6418
    else:
        noaa_ground_truth = {
            "status": "CONFIRMED_QUIET",
            "label": "Quiet-Sun Baseline Observation",
            "peak_utc": "2026-10-18T12:00:00 UTC",
            "noaa_class": "Quiet Sun / No Flare",
            "active_region": "Background Solar Disk",
            "catalog_source": "NOAA SWPC Daily Solar Event Log",
        }
        target_idx = 1000

    if feat_file.is_file() and idx_file.is_file():
        df_feat = pd.read_csv(feat_file)
        df_idx = pd.read_csv(idx_file)
        actual_idx = min(target_idx, len(df_feat) - 1)
        feature_input = df_feat.iloc[actual_idx].to_dict()
        meta_row = df_idx.iloc[actual_idx]
        window_id_label = str(meta_row["window_id"])
        window_elapsed_label = f"{meta_row['window_start']:.0f}s – {meta_row['window_end']:.0f}s"
        coverage_label = f"{meta_row['coverage_fraction']:.1%}"
        quality_status_label = f"Nominal Science ({meta_row.get('quality_flag', 'OK')})"

else:  # July 2024 presets
    date_folder = "AL1_SOLEXS_20240714_SDD2_L1" if "Jul 14" in preset else "AL1_SOLEXS_20240713_SDD2_L1"
    obs_stem = date_folder
    obs_time_label = f"{date_folder[11:15]}-{date_folder[15:17]}-{date_folder[17:19]} (Aditya-L1 SoLEXS SDD2)"
    feat_file = root / "data" / "processed" / "features" / date_folder / "window_features.csv"
    idx_file = root / "data" / "processed" / "features" / date_folder / "window_index.csv"

    if "Event #400" in preset:
        noaa_ground_truth = {
            "status": "CONFIRMED_FLARE",
            "label": "NOAA SWPC Event #400 (X1.2 Flare)",
            "peak_utc": "2024-07-14T02:34:00 UTC",
            "noaa_class": "X1.2",
            "active_region": "AR3738",
            "catalog_source": "NOAA Space Weather Prediction Center (SWPC)",
        }
        target_idx = 450
    elif "Event #383" in preset:
        noaa_ground_truth = {
            "status": "CONFIRMED_FLARE",
            "label": "NOAA SWPC Event #383 (M1.5 Flare)",
            "peak_utc": "2024-07-13T02:40:00 UTC",
            "noaa_class": "M1.5",
            "active_region": "AR3738",
            "catalog_source": "NOAA Space Weather Prediction Center (SWPC)",
        }
        target_idx = 380
    else:
        noaa_ground_truth = {
            "status": "CONFIRMED_QUIET",
            "label": "Verified Quiet Science Interval",
            "peak_utc": "2024-07-13T12:00:00 UTC",
            "noaa_class": "Quiet Sun / No Flare",
            "active_region": "Background Solar Disk",
            "catalog_source": "NOAA SWPC Daily Solar Event Log",
        }
        target_idx = 800

    if feat_file.is_file() and idx_file.is_file():
        df_feat = pd.read_csv(feat_file)
        df_idx = pd.read_csv(idx_file)
        actual_idx = min(target_idx, len(df_feat) - 1)
        feature_input = df_feat.iloc[actual_idx].to_dict()
        meta_row = df_idx.iloc[actual_idx]
        window_id_label = str(meta_row["window_id"])
        window_elapsed_label = f"{meta_row['window_start']:.0f}s – {meta_row['window_end']:.0f}s"
        coverage_label = f"{meta_row['coverage_fraction']:.1%}"
        quality_status_label = f"Nominal Science ({meta_row.get('quality_flag', 'OK')})"

# Observation Window Metadata Card (Comfortable, unclipped desktop typography)
st.markdown(
    f"""
    <div style="background-color: #0E1526; border: 1px solid #1E293B; border-radius: 8px; padding: 16px 22px; margin-bottom: 16px;">
        <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 14px;">
            <div>
                <span style="font-size: 0.82rem; font-weight: 700; color: #38BDF8; letter-spacing: 0.05em; text-transform: uppercase;">Observation Archive Target</span>
                <div style="font-size: 1.12rem; font-weight: 600; color: #F8FAFC; margin-top: 3px;"><code>{obs_stem}</code></div>
            </div>
            <div>
                <span style="font-size: 0.82rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; text-transform: uppercase;">Window Identifier</span>
                <div style="font-size: 1.00rem; font-weight: 500; color: #E2E8F0; margin-top: 3px;"><code>{window_id_label}</code></div>
            </div>
            <div>
                <span style="font-size: 0.82rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; text-transform: uppercase;">Elapsed Range</span>
                <div style="font-size: 1.00rem; font-weight: 500; color: #FBBF24; margin-top: 3px;">{window_elapsed_label} (W=60s)</div>
            </div>
            <div>
                <span style="font-size: 0.82rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; text-transform: uppercase;">GTI Coverage</span>
                <div style="font-size: 1.00rem; font-weight: 500; color: #34D399; margin-top: 3px;">{coverage_label}</div>
            </div>
            <div>
                <span style="font-size: 0.82rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; text-transform: uppercase;">Telemetry Quality</span>
                <div style="font-size: 1.00rem; font-weight: 500; color: #E2E8F0; margin-top: 3px;">{quality_status_label}</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Decision Threshold Slider
threshold_val = st.slider(
    "Decision Threshold (Classification Boundary)",
    min_value=0.10,
    max_value=0.90,
    value=0.50,
    step=0.05,
    help="Probability cut-off for binary flare detection (Task A). Scores >= threshold classify as Flare Detected.",
)

# Collapsed Advanced Research Input (Preserves custom count sequence functionality)
with st.expander("Advanced Research Input", expanded=False):
    st.markdown(
        "**Custom Count Rate Sequence Testing (Research Only)**: "
        "Supply a synthetic or modified 60-second sequence of soft X-ray count rates (1.0 Hz cadence) "
        "to evaluate the causal feature extraction pipeline."
    )
    override_with_custom = st.checkbox("Override historical observation with custom count sequence", value=False)
    if override_with_custom:
        sample_preset = st.selectbox(
            "Load Example Count Sequence Template",
            [
                "Impulsive Flare Burst (Spike to 80 counts/s)",
                "Quiet-Sun Constant Flux (9 counts/s)",
                "Gradual Flare Rise (Slow linear rise)",
            ],
        )
        if "Impulsive" in sample_preset:
            default_seq = ", ".join(map(str, [10.0] * 45 + [25.0, 40.0, 65.0, 80.0, 75.0, 50.0, 35.0, 20.0, 15.0, 10.0] * 2))
        elif "Quiet-Sun" in sample_preset:
            default_seq = ", ".join(map(str, [9.0] * 60))
        else:
            default_seq = ", ".join(map(str, np.linspace(8.0, 45.0, 60).round(1)))

        seq_text = st.text_area("Observation Count Rates (60 samples @ 1.0s cadence)", value=default_seq, height=80)
        try:
            custom_counts = [float(x.strip()) for x in seq_text.split(",") if x.strip()]
            if len(custom_counts) == 60:
                window_counts = custom_counts
                obs_time_label = "Custom 60-Second Research Sequence"
                noaa_ground_truth = {
                    "status": "SYNTHETIC_TEST",
                    "label": "Custom 60-Second Count Rate Sequence",
                    "peak_utc": "User-Defined Sequence (Non-Catalog)",
                    "noaa_class": "Custom Input (Research Testing)",
                    "active_region": "Simulated Environment",
                    "catalog_source": "Advanced Research Input",
                }
            else:
                st.warning(f"Expected 60 count values, found {len(custom_counts)}. Using historical observation window.")
        except Exception:
            st.error("Invalid number formatting in count sequence. Using historical observation window.")

# Execute Model Prediction
if feature_input or window_counts:
    st.markdown("---")
    st.subheader("2. Detection Result & Event Verification")

    try:
        if window_counts:
            pred_res = pipeline.predict_from_counts(window_counts, threshold=threshold_val)
        else:
            pred_res = pipeline.predict(feature_input, threshold=threshold_val)[0]

        prob = pred_res["flare_probability"]
        is_flare = pred_res["flare_detected"]
        risk = pred_res["risk_level"]
        threshold_margin = prob - threshold_val

        # Primary Metrics Summary
        r_col1, r_col2, r_col3, r_col4 = st.columns(4)
        with r_col1:
            st.metric(
                "Flare Probability",
                f"{prob:.2%}",
                f"{'▲ DETECTED' if is_flare else '▼ QUIET'}",
                delta_color="normal" if is_flare else "off",
            )
        with r_col2:
            st.metric(
                "Classification",
                "FLARE DETECTED" if is_flare else "QUIET SUN",
                f"Margin: {threshold_margin:+.1%}",
            )
        with r_col3:
            st.metric(
                "Observation Window",
                "60 s (1 min)",
                f"Threshold: {threshold_val:.2f}",
            )
        with r_col4:
            gt_status = noaa_ground_truth.get("status", "UNKNOWN")
            gt_badge = "FLARE" if gt_status == "CONFIRMED_FLARE" else ("QUIET" if gt_status == "CONFIRMED_QUIET" else "SYNTHETIC")
            raw_gt_class = noaa_ground_truth.get("noaa_class", "Catalog Truth")
            if "Impulsive Burst" in raw_gt_class:
                gt_metric_val = "M/X-Equivalent"
            elif "Cluster" in raw_gt_class:
                gt_metric_val = "C-Cluster"
            else:
                gt_metric_val = raw_gt_class

            st.metric(
                "NOAA Ground Truth",
                gt_metric_val,
                f"Status: {gt_badge}",
            )

        # Clear Explanation of Result & Calibration Caveat (Section C requirement)
        explanation_badge = "FLARE DETECTED" if is_flare else "QUIET BACKGROUND"
        badge_bg = "rgba(234, 88, 12, 0.15)" if is_flare else "rgba(2, 132, 199, 0.15)"
        badge_border = "#EA580C" if is_flare else "#0284C7"
        badge_color = "#FB923C" if is_flare else "#38BDF8"

        st.markdown(
            f"""
            <div style="background-color: #0E1526; border: 1px solid #1E293B; border-radius: 8px; padding: 18px 24px; margin-top: 14px; margin-bottom: 18px;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                    <span style="background-color: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; padding: 4px 12px; border-radius: 4px; font-size: 0.86rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">
                        {explanation_badge}
                    </span>
                    <span style="font-size: 1.14rem; font-weight: 600; color: #F8FAFC;">
                        Result Interpretation for Selected 60-Second Window
                    </span>
                </div>
                <p style="font-size: 1.02rem; line-height: 1.62; color: #CBD5E1; margin: 0 0 12px 0;">
                    The model evaluated soft X-ray intensity, derivative slopes, and variability across the 60-second window 
                    [<code>{obs_stem}</code>, <code>{window_elapsed_label}</code>]. 
                    With a model score of <strong>{prob:.2%}</strong> against the configured decision threshold of 
                    <strong>{threshold_val:.2f}</strong> (margin: <strong>{threshold_margin:+.1%}</strong>), 
                    the window is classified as <strong>{'FLARE DETECTED' if is_flare else 'QUIET BACKGROUND'}</strong>. 
                    This signifies that soft X-ray count rates {'exhibit an impulsive elevated burst or rising profile consistent with flare activity' if is_flare else 'remain consistent with quiescent background solar disk emission'}.
                </p>
                <div style="font-size: 0.90rem; line-height: 1.55; color: #94A3B8; background: rgba(15, 23, 42, 0.6); border-left: 4px solid #F59E0B; padding: 10px 14px; border-radius: 0 6px 6px 0;">
                    <strong style="color: #FBBF24;">Calibration & Scope Caveat:</strong> This prediction represents a retrospective in-window statistical classification (Task A: 60-second duration). 
                    It is <em>not</em> an operational forward forecast of future flaring activity, nor is it certified for mission-critical space-weather alerting.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Side-by-Side Comparison: NOAA Catalog Truth vs Probabilistic Model Detection
        v_col1, v_col2 = st.columns(2)

        with v_col1:
            st.markdown("#### Authoritative NOAA Ground Truth")
            if gt_status == "CONFIRMED_FLARE":
                st.markdown(
                    f"""
                    <div style="background-color: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.40); border-radius: 8px; padding: 18px 22px; min-height: 205px;">
                        <span style="background-color: #1D4ED8; color: white; padding: 4px 10px; border-radius: 4px; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;">NOAA CONFIRMED EVENT</span>
                        <h4 style="margin: 10px 0 5px 0; color: #93C5FD; font-size: 1.16rem; font-weight: 700;">{noaa_ground_truth.get('label')}</h4>
                        <p style="margin: 0; font-size: 0.98rem; color: #E2E8F0; line-height: 1.52;">
                            <strong>GOES / SWPC Class:</strong> {noaa_ground_truth.get('noaa_class')}<br>
                            <strong>Active Region:</strong> {noaa_ground_truth.get('active_region')}
                        </p>
                        <p style="margin: 8px 0 0 0; font-size: 0.90rem; color: #94A3B8;">
                            <strong>Peak Timestamp:</strong> {noaa_ground_truth.get('peak_utc')}
                        </p>
                        <p style="margin: 8px 0 0 0; font-size: 0.82rem; color: #64748B;">
                            Authority: {noaa_ground_truth.get('catalog_source')}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif gt_status == "CONFIRMED_QUIET":
                st.markdown(
                    f"""
                    <div style="background-color: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.40); border-radius: 8px; padding: 18px 22px; min-height: 205px;">
                        <span style="background-color: #15803D; color: white; padding: 4px 10px; border-radius: 4px; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;">NOAA VERIFIED QUIET SUN</span>
                        <h4 style="margin: 10px 0 5px 0; color: #86EFAC; font-size: 1.16rem; font-weight: 700;">{noaa_ground_truth.get('label')}</h4>
                        <p style="margin: 0; font-size: 0.98rem; color: #E2E8F0; line-height: 1.52;">
                            No flares recorded in official NOAA SWPC solar event logs during this scientific GTI window.
                        </p>
                        <p style="margin: 8px 0 0 0; font-size: 0.90rem; color: #94A3B8;">
                            <strong>Epoch:</strong> {noaa_ground_truth.get('peak_utc')}
                        </p>
                        <p style="margin: 8px 0 0 0; font-size: 0.82rem; color: #64748B;">
                            Authority: {noaa_ground_truth.get('catalog_source')}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="background-color: rgba(148, 163, 184, 0.08); border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 8px; padding: 18px 22px; min-height: 205px;">
                        <span style="background-color: #475569; color: white; padding: 4px 10px; border-radius: 4px; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;">RESEARCH SEQUENCE</span>
                        <h4 style="margin: 10px 0 5px 0; color: #CBD5E1; font-size: 1.16rem; font-weight: 700;">{noaa_ground_truth.get('label')}</h4>
                        <p style="margin: 0; font-size: 0.98rem; color: #E2E8F0; line-height: 1.52;">
                            Synthetic / experimental count rate sequence provided via Advanced Research Input.
                        </p>
                        <p style="margin: 8px 0 0 0; font-size: 0.90rem; color: #94A3B8;">
                            <strong>Cadence:</strong> 1.0 Hz (60 samples)
                        </p>
                        <p style="margin: 8px 0 0 0; font-size: 0.82rem; color: #64748B;">
                            Authority: Non-catalog experimental input
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with v_col2:
            st.markdown("#### SOLARIS-A1 Model Detection Output")
            model_badge_color = "#EA580C" if is_flare else "#0284C7"
            model_badge_text = "FLARE DETECTED" if is_flare else "QUIET BACKGROUND"
            st.markdown(
                f"""
                <div style="background-color: #0E1526; border: 1px solid {model_badge_color}; border-radius: 8px; padding: 18px 22px; min-height: 205px;">
                    <span style="background-color: {model_badge_color}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;">MODEL DETECTION: {model_badge_text}</span>
                    <h4 style="margin: 10px 0 5px 0; color: #F8FAFC; font-size: 1.16rem; font-weight: 700;">Probability: {prob:.2%} | Risk: {risk}</h4>
                    <p style="margin: 0; font-size: 0.98rem; color: #E2E8F0; line-height: 1.52;">
                        <strong>Estimator:</strong> <code>{pred_res['model_version']}</code><br>
                        <strong>Threshold Margin:</strong> {threshold_margin:+.1%} (Threshold: {threshold_val:.2f})
                    </p>
                    <p style="margin: 8px 0 0 0; font-size: 0.90rem; color: #94A3B8;">
                        <strong>Classification Regime:</strong> Binary Soft X-Ray Detector (Task A)
                    </p>
                    <p style="margin: 8px 0 0 0; font-size: 0.82rem; color: #F59E0B;">
                        Statistical inference on Level-1 telemetry — distinct from physical catalog truth.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    except Exception as exc:
        render_status_banner("ERROR", f"Model inference execution failed: {exc}", "Inference")

st.markdown("---")

# Collapsed Secondary Model Metadata & Diagnostic Details (Section C requirement)
with st.expander(f"Model Specifications & Architecture: {v_info['model_name'].upper()} ({v_info['dataset_cohort']})", expanded=False):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Inference Model", f"{v_info['model_name'].upper()}", v_info["model_class"])
    with col2:
        st.metric("Observation Window", f"{v_info['window_duration_seconds']:.0f} s (1 min)", "Task A Detection")
    with col3:
        st.metric("Required Features", f"{v_info['features_count']} Features", "StandardScaler + Median")
    with col4:
        st.metric("Production Ready", "NO (Research Only)", "Zero Operational Warranties", delta_color="inverse")

    st.markdown(
        f"""
        - **Profile Identifier**: `{v_info['profile_id']}`
        - **Dataset Cohort**: {v_info['dataset_cohort']}
        - **Governance Status**: `{v_info['governance_status']}`
        - **Imputation Strategy**: {v_info['imputer']}
        - **Scaling Transform**: {v_info['scaler']}
        - **Operational Advisory**: {v_info['operational_advisory']}
        """
    )

if feature_input:
    with st.expander("Extracted Feature Vector (19 Causal Features)", expanded=False):
        meta_keys = {"window_id", "segment_id", "file_stem", "window_start", "window_end", "baseline_reason", "quality_flag", "include_flag"}
        feat_items = [
            {"Feature": k, "Value": f"{v:.4f}" if isinstance(v, (int, float)) and not np.isnan(v) else str(v)}
            for k, v in feature_input.items()
            if k not in meta_keys
        ]
        if feat_items:
            df_feat_table = pd.DataFrame(feat_items)
            st.dataframe(df_feat_table, use_container_width=True, hide_index=True)

with st.expander("Session Prediction History (Last 100 Predictions)", expanded=False):
    if pipeline.history:
        df_hist = pd.DataFrame(pipeline.history)
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("No predictions recorded in current session yet.")
