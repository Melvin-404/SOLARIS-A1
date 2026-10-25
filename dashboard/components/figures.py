"""Interactive Plotly visualization builders for SOLARIS-A1 dashboard.

CRITICAL DISPLAY-ONLY CONSTRAINTS:
1. Downsampling is STRICTLY display-only: downsampling is applied solely to render smooth
   interactive charts in the browser and is never used for scientific computation.
2. Distinct Visual Layers:
   - GTI intervals rendered as shaded green/blue background rectangles.
   - Non-finite (NaN) and zero count samples rendered with distinct marker colors.
   - Verified NOAA catalog events rendered with prominent blue/cyan markers.
   - Candidate burst intervals rendered with distinct warning styles labelled 'candidate (unverified)'.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def build_light_curve_figure(
    df: pd.DataFrame,
    time_col: str = "time",
    count_col: str = "counts",
    gti_intervals: Optional[List[Tuple[float, float]]] = None,
    candidate_intervals: Optional[List[Tuple[float, float, str]]] = None,
    verified_events: Optional[List[Dict[str, Any]]] = None,
    log_scale: bool = False,
    show_flagged: bool = True,
    max_display_points: int = 15000,
    time_axis_mode: str = "elapsed_hours",
) -> Tuple[go.Figure, bool]:
    """Build interactive Plotly light-curve figure in space-weather dark theme.

    Parameters
    ----------
    df : pd.DataFrame
        Light curve telemetry data.
    time_col : str
        Column name for timestamp values (MET epoch seconds).
    count_col : str
        Column name for count rate values.
    gti_intervals : list of (start, stop), optional
        Valid science intervals to shade.
    candidate_intervals : list of (start, stop, label), optional
        Heuristic burst candidate intervals.
    verified_events : list of dict, optional
        NOAA confirmed ground truth events.
    log_scale : bool
        Whether to plot counts on logarithmic scale.
    show_flagged : bool
        Whether to highlight zero counts and NaNs.
    max_display_points : int
        Maximum points to display (subsampled for rendering speed).
    time_axis_mode : str
        "elapsed_hours" (default) for readable 0-24h orbit axis with exact MET in tooltips,
        or "met_seconds" for raw elapsed mission epoch seconds.
    """
    fig = go.Figure()

    if df.empty or time_col not in df.columns or count_col not in df.columns:
        fig.update_layout(
            title="No Light-Curve Data Available",
            xaxis_title="Time",
            yaxis_title="Count Rate",
            template="plotly_dark",
            paper_bgcolor="#0E1526",
            plot_bgcolor="#070B14",
        )
        return fig, False

    times = df[time_col].values.astype(float)
    counts = df[count_col].values.astype(float)
    n_points = len(times)

    # Determine time scaling: convert large raw epoch seconds to readable elapsed hours
    t0 = float(times[0]) if n_points > 0 else 0.0
    use_hours = (time_axis_mode == "elapsed_hours") and (t0 > 100000.0 or (times[-1] - t0) > 3600.0)

    def scale_t(t_val: float) -> float:
        return (t_val - t0) / 3600.0 if use_hours else t_val

    # 1. Shaded GTI Intervals (Good Time Intervals)
    if gti_intervals:
        for st_time, en_time in gti_intervals:
            fig.add_vrect(
                x0=scale_t(float(st_time)),
                x1=scale_t(float(en_time)),
                fillcolor="rgba(16, 185, 129, 0.08)",
                layer="below",
                line_width=0,
                annotation_text="GTI",
                annotation_position="top left",
                annotation=dict(font_size=10, font_color="#10B981"),
            )

    # 2. Verified NOAA Catalog Event Overlays
    if verified_events:
        for evt in verified_events:
            e_st = evt.get("start") or evt.get("start_time") or evt.get("onset_time") or evt.get("t_start")
            e_en = evt.get("end") or evt.get("end_time") or evt.get("t_end")
            e_label = evt.get("event_id") or evt.get("label", "Verified Flare")
            e_class = evt.get("class") or evt.get("classification") or evt.get("flare_class", "")
            disp_tag = f"{e_label} ({e_class})" if e_class else str(e_label)

            if e_st is not None and e_en is not None:
                fig.add_vrect(
                    x0=scale_t(float(e_st)),
                    x1=scale_t(float(e_en)),
                    fillcolor="rgba(56, 189, 248, 0.18)",
                    layer="below",
                    line=dict(color="#38BDF8", width=1.5),
                    annotation_text=disp_tag,
                    annotation_position="top",
                    annotation=dict(font_size=10, font_color="#38BDF8"),
                )

    # 3. Candidate Unverified Event Overlay
    if candidate_intervals:
        for c_start, c_end, c_label in candidate_intervals:
            fig.add_vrect(
                x0=scale_t(float(c_start)),
                x1=scale_t(float(c_end)),
                fillcolor="rgba(245, 158, 11, 0.15)",
                layer="below",
                line=dict(color="#F59E0B", width=1, dash="dash"),
                annotation_text="Candidate (Unverified)",
                annotation_position="top right",
                annotation=dict(font_size=9, font_color="#FBBF24"),
            )

    # 4. Display Downsampling
    downsampled = False
    if n_points > max_display_points:
        step = int(np.ceil(n_points / max_display_points))
        disp_times = times[::step]
        disp_counts = counts[::step]
        downsampled = True
    else:
        disp_times = times
        disp_counts = counts

    disp_x = scale_t(disp_times) if use_hours else disp_times

    # Primary Time Series Trace (Solar Gold)
    if use_hours:
        hover_template = (
            "<b>Elapsed Orbit:</b> %{x:.2f} hrs<br>"
            "<b>Mission Timestamp:</b> %{customdata:.1f} s<br>"
            "<b>Count Rate:</b> %{y:.2f} counts/s<extra></extra>"
        )
    else:
        hover_template = (
            "<b>Mission Time:</b> %{x:.1f} s<br>"
            "<b>Count Rate:</b> %{y:.2f} counts/s<extra></extra>"
        )

    fig.add_trace(
        go.Scatter(
            x=disp_x,
            y=disp_counts,
            customdata=disp_times,
            mode="lines",
            name="SoLEXS Count Rate",
            line=dict(color="#F59E0B", width=1.3),
            hovertemplate=hover_template,
        )
    )

    # 5. Non-finite / Zero Sample Markers
    if show_flagged:
        zero_mask = disp_counts == 0.0
        if np.any(zero_mask):
            fig.add_trace(
                go.Scatter(
                    x=disp_x[zero_mask],
                    y=disp_counts[zero_mask],
                    customdata=disp_times[zero_mask],
                    mode="markers",
                    name="Zero Counts",
                    marker=dict(color="#A855F7", size=4, symbol="circle-open"),
                    hovertemplate="<b>Zero Count:</b> %{customdata:.1f} s<extra></extra>",
                )
            )

        nan_mask = np.isnan(disp_counts)
        if np.any(nan_mask):
            fig.add_trace(
                go.Scatter(
                    x=disp_x[nan_mask],
                    y=np.zeros(np.sum(nan_mask)),
                    customdata=disp_times[nan_mask],
                    mode="markers",
                    name="Missing Samples (NaN)",
                    marker=dict(color="#EF4444", size=5, symbol="x"),
                    hovertemplate="<b>Missing / NaN:</b> %{customdata:.1f} s<extra></extra>",
                )
            )

    # Dark Space Observatory Theme Layout
    x_axis_title = (
        "Elapsed Observation Time (Hours from Orbit Start)"
        if use_hours
        else "Mission Elapsed Time (seconds)"
    )
    y_type = "log" if log_scale else "linear"
    fig.update_layout(
        xaxis=dict(
            title=x_axis_title,
            gridcolor="#1E293B",
            zerolinecolor="#1E293B",
            color="#CBD5E1",
        ),
        yaxis=dict(
            title="Detector Count Rate (counts/s)" + (" [log]" if log_scale else ""),
            type=y_type,
            gridcolor="#1E293B",
            zerolinecolor="#1E293B",
            color="#CBD5E1",
        ),
        hovermode="x unified",
        template="plotly_dark",
        paper_bgcolor="#0E1526",
        plot_bgcolor="#070B14",
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color="#CBD5E1"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        margin=dict(l=40, r=20, t=25, b=35),
        height=390,
    )

    return fig, downsampled


def build_feature_histogram(
    df: pd.DataFrame,
    feature_name: str,
    nbins: int = 30,
) -> go.Figure:
    """Build histogram distribution for an engineered feature in observatory dark theme."""
    fig = go.Figure()
    if df.empty or feature_name not in df.columns:
        fig.update_layout(
            title=f"Feature '{feature_name}' not available",
            template="plotly_dark",
            paper_bgcolor="#0E1526",
            plot_bgcolor="#070B14",
        )
        return fig

    values = df[feature_name].dropna().values
    fig.add_trace(
        go.Histogram(
            x=values,
            nbinsx=nbins,
            marker_color="#F59E0B",
            marker_line=dict(color="#D97706", width=0.8),
            opacity=0.85,
            hovertemplate=f"<b>{feature_name}:</b> %{{x}}<br><b>Window Count:</b> %{{y}}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=f"Distribution: {feature_name}", font=dict(color="#F8FAFC", size=13)),
        xaxis=dict(title=feature_name, gridcolor="#1E293B", color="#CBD5E1"),
        yaxis=dict(title="Observation Windows", gridcolor="#1E293B", color="#CBD5E1"),
        template="plotly_dark",
        paper_bgcolor="#0E1526",
        plot_bgcolor="#070B14",
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color="#CBD5E1"),
        margin=dict(l=35, r=25, t=35, b=30),
        height=310,
    )
    return fig
