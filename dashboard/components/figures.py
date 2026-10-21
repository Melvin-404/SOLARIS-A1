"""Interactive Plotly visualization builders for SOLARIS-A1 dashboard (Stage 12).

CRITICAL DISPLAY-ONLY CONSTRAINTS:
1. Downsampling is STRICTLY display-only: downsampling is applied solely to render smooth
   interactive charts in the browser and is never used for scientific computation.
2. Distinct Visual Layers:
   - GTI intervals rendered as shaded green/blue background rectangles.
   - Non-finite (NaN) and zero count samples rendered with distinct marker colors.
   - Candidate burst intervals rendered with distinct warning styles labelled 'candidate (unverified)'.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def build_light_curve_figure(
    df: pd.DataFrame,
    time_col: str = "time",
    count_col: str = "counts",
    gti_intervals: Optional[List[Tuple[float, float]]] = None,
    candidate_intervals: Optional[List[Tuple[float, float, str]]] = None,
    log_scale: bool = False,
    show_flagged: bool = True,
    max_display_points: int = 15000,
) -> Tuple[go.Figure, bool]:
    """Build interactive Plotly light-curve figure.

    Returns
    -------
    fig : go.Figure
    downsampled : bool
        Whether display downsampling was applied.
    """
    fig = go.Figure()

    if df.empty or time_col not in df.columns or count_col not in df.columns:
        fig.update_layout(
            title="No Light-Curve Data Available",
            xaxis_title="Time (s)",
            yaxis_title="Count Rate",
        )
        return fig, False

    times = df[time_col].values
    counts = df[count_col].values
    n_points = len(times)

    # 1. Shaded GTI Intervals
    if gti_intervals:
        for st_time, en_time in gti_intervals:
            fig.add_vrect(
                x0=st_time,
                x1=en_time,
                fillcolor="rgba(46, 204, 113, 0.12)",
                layer="below",
                line_width=0,
                annotation_text="GTI",
                annotation_position="top left",
            )

    # 2. Candidate Event Overlay
    if candidate_intervals:
        for c_start, c_end, c_label in candidate_intervals:
            fig.add_vrect(
                x0=c_start,
                x1=c_end,
                fillcolor="rgba(231, 76, 60, 0.2)",
                layer="below",
                line=dict(color="rgba(231, 76, 60, 0.6)", width=1, dash="dash"),
                annotation_text="Candidate (Unverified)",
                annotation_position="top right",
            )

    # 3. Downsampling for Display Only
    downsampled = False
    if n_points > max_display_points:
        step = int(np.ceil(n_points / max_display_points))
        disp_times = times[::step]
        disp_counts = counts[::step]
        downsampled = True
    else:
        disp_times = times
        disp_counts = counts

    # Primary time series line
    fig.add_trace(
        go.Scatter(
            x=disp_times,
            y=disp_counts,
            mode="lines",
            name="Light Curve",
            line=dict(color="#1f77b4", width=1.2),
            hovertemplate="<b>Time:</b> %{x:.2f} s<br><b>Counts:</b> %{y:.2f}<extra></extra>",
        )
    )

    # 4. Non-finite / Zero Sample Markers
    if show_flagged:
        zero_mask = disp_counts == 0.0
        if np.any(zero_mask):
            fig.add_trace(
                go.Scatter(
                    x=disp_times[zero_mask],
                    y=disp_counts[zero_mask],
                    mode="markers",
                    name="Zero Counts",
                    marker=dict(color="purple", size=4, symbol="circle-open"),
                    hovertemplate="<b>Zero Count at:</b> %{x:.2f} s<extra></extra>",
                )
            )

        nan_mask = np.isnan(disp_counts)
        if np.any(nan_mask):
            fig.add_trace(
                go.Scatter(
                    x=disp_times[nan_mask],
                    y=np.zeros(np.sum(nan_mask)),
                    mode="markers",
                    name="NaN Samples",
                    marker=dict(color="red", size=5, symbol="x"),
                    hovertemplate="<b>NaN (Missing) at:</b> %{x:.2f} s<extra></extra>",
                )
            )

    # Layout configuration
    y_type = "log" if log_scale else "linear"
    fig.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Count Rate" + (" (log scale)" if log_scale else ""),
        yaxis_type=y_type,
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=40, b=40),
    )

    return fig, downsampled


def build_feature_histogram(
    df: pd.DataFrame,
    feature_name: str,
    nbins: int = 30,
) -> go.Figure:
    """Build histogram distribution for an engineered feature."""
    fig = go.Figure()
    if df.empty or feature_name not in df.columns:
        fig.update_layout(title=f"Feature '{feature_name}' not available")
        return fig

    values = df[feature_name].dropna().values
    fig.add_trace(
        go.Histogram(
            x=values,
            nbinsx=nbins,
            marker_color="#2ca02c",
            opacity=0.75,
            hovertemplate="<b>Value:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        title=f"Distribution of {feature_name}",
        xaxis_title=feature_name,
        yaxis_title="Frequency",
        template="plotly_white",
        margin=dict(l=30, r=30, t=40, b=30),
    )
    return fig
