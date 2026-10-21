"""Visualization tools for Exploratory Data Analysis in SOLARIS-A1 (Stage 5).

Generates publication-quality diagnostic figures at 150 dpi (PNG and PDF):
- plot_light_curve: Complete full-day time series with GTI, gaps, candidates, and sample classes.
- plot_count_distribution: Linear and logarithmic count histograms.
- plot_coverage_timeline: Multi-track coverage timeline showing samples, GTI, and gaps.
- plot_burst_gallery: Small-multiples gallery of candidate transient bursts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_light_curve(
    times: np.ndarray,
    values: np.ndarray,
    gti: Optional[Union[Dict[str, Any], List[Dict[str, float]]]] = None,
    candidates: Optional[Union[pd.DataFrame, List[Dict[str, Any]]]] = None,
    gaps: Optional[List[Dict[str, Any]]] = None,
    baseline: Optional[np.ndarray] = None,
    output_path: Optional[Path] = None,
    title: str = "Aditya-L1 SoLEXS Light Curve (Exploratory Overview)",
) -> plt.Figure:
    """Plot full light curve with GTI, gaps, candidate bursts, zeros, and non-finites."""
    fig, ax = plt.subplots(figsize=(14, 5.5), dpi=150)
    t_arr = np.asarray(times, dtype=np.float64)
    v_arr = np.asarray(values, dtype=np.float64)
    n = len(t_arr)

    t0 = float(t_arr[0]) if n > 0 else 0.0
    rel_h = (t_arr - t0) / 3600.0 if n > 0 else np.array([])

    finite_mask = np.isfinite(v_arr)
    nan_mask = np.isnan(v_arr)
    zero_mask = finite_mask & (v_arr == 0.0)
    pos_mask = finite_mask & (v_arr > 0.0)

    # Plot continuous finite series
    if np.any(pos_mask):
        ax.plot(
            rel_h[pos_mask],
            v_arr[pos_mask],
            color="#2563eb",
            linewidth=0.6,
            alpha=0.75,
            label="Observed Counts (>0)",
        )

    # Plot baseline if provided
    if baseline is not None and len(baseline) == n:
        ax.plot(
            rel_h[finite_mask],
            baseline[finite_mask],
            color="#0f172a",
            linewidth=1.2,
            linestyle="--",
            label="Running Median Baseline",
        )

    # Plot zero counts
    if np.any(zero_mask):
        ax.scatter(
            rel_h[zero_mask],
            np.zeros(int(zero_mask.sum())),
            s=12,
            color="#10b981",
            marker="o",
            alpha=0.8,
            label=f"Zero Counts ({int(zero_mask.sum()):,})",
        )

    # Plot NaNs along baseline
    if np.any(nan_mask):
        ax.scatter(
            rel_h[nan_mask],
            np.zeros(int(nan_mask.sum())),
            s=16,
            color="#ef4444",
            marker="x",
            linewidth=0.9,
            label=f"NaN Samples ({int(nan_mask.sum()):,})",
        )

    # GTI Intervals shading
    gti_list: List[Dict[str, float]] = []
    if isinstance(gti, dict):
        gti_list = gti.get("intervals", [])
    elif isinstance(gti, list):
        gti_list = gti

    gti_plotted = False
    for inv in gti_list:
        s = (inv["start"] - t0) / 3600.0
        e = (inv["stop"] - t0) / 3600.0
        lbl = "GTI (Good Time Interval)" if not gti_plotted else None
        ax.axvspan(s, e, color="#10b981", alpha=0.15, label=lbl)
        gti_plotted = True

    # Cadence gaps shading
    gap_plotted = False
    if gaps:
        for gp in gaps:
            s = (gp["start_time"] - t0) / 3600.0
            e = (gp["end_time"] - t0) / 3600.0
            lbl = "Cadence Gap" if not gap_plotted else None
            ax.axvspan(s, e, color="#dc2626", alpha=0.35, label=lbl)
            gap_plotted = True

    # Candidate intervals shading
    cand_df = candidates if isinstance(candidates, pd.DataFrame) else (pd.DataFrame(candidates) if candidates else None)
    cand_plotted = False
    if cand_df is not None and not cand_df.empty:
        for _, row in cand_df.iterrows():
            cs = (row["start"] - t0) / 3600.0
            ce = (row["end"] - t0) / 3600.0
            lbl = "candidate (unverified)" if not cand_plotted else None
            ax.axvspan(cs, ce, color="#f59e0b", alpha=0.38, label=lbl)
            cand_plotted = True

    ax.set_xlabel(f"Elapsed Time (hours from t0 = {t0:.1f} s)")
    ax.set_ylabel("Raw Counts")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right", framealpha=0.92, fontsize=8.5)
    fig.tight_layout()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_p, dpi=150)
        # Also save PDF as required
        fig.savefig(out_p.with_suffix(".pdf"))

    return fig


def plot_count_distribution(
    values: np.ndarray,
    output_path: Optional[Path] = None,
    title: str = "Count Distribution (Linear & Log Scales)",
) -> plt.Figure:
    """Plot linear and log histograms of count distribution."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), dpi=150)
    arr = np.asarray(values, dtype=np.float64)

    finite_mask = np.isfinite(arr)
    f_vals = arr[finite_mask]
    n_nan = int(np.isnan(arr).sum())
    n_zeros = int((f_vals == 0.0).sum()) if len(f_vals) > 0 else 0
    pos_vals = f_vals[f_vals > 0.0] if len(f_vals) > 0 else np.array([])

    stats_str = (
        f"Total: {len(arr):,}\n"
        f"NaNs: {n_nan:,} ({n_nan/max(1, len(arr))*100:.2f}%)\n"
        f"Zeros: {n_zeros:,}\n"
        f"Positive: {len(pos_vals):,}"
    )

    if len(pos_vals) > 0:
        ax1.hist(pos_vals, bins=50, color="#059669", edgecolor="#064e3b", alpha=0.85)
        ax2.hist(pos_vals, bins=50, color="#2563eb", edgecolor="#1e3a8a", alpha=0.85, log=True)

    ax1.set_xlabel("Count Value (> 0)")
    ax1.set_ylabel("Frequency (Linear)")
    ax1.set_title("Linear Histogram", fontsize=11, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.5)
    ax1.text(0.95, 0.95, stats_str, transform=ax1.transAxes, ha="right", va="top",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#f8fafc", edgecolor="#cbd5e1"), fontsize=9)

    ax2.set_xlabel("Count Value (> 0)")
    ax2.set_ylabel("Frequency (Log Scale)")
    ax2.set_title("Logarithmic Histogram", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.5)

    fig.suptitle(title, fontsize=12, fontweight="bold", y=1.02)
    fig.tight_layout()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_p, dpi=150, bbox_inches="tight")

    return fig


def plot_coverage_timeline(
    gti: Optional[Union[Dict[str, Any], List[Dict[str, float]]]],
    times: np.ndarray,
    gaps: Optional[List[Dict[str, Any]]] = None,
    output_path: Optional[Path] = None,
    title: str = "Observation Coverage Timeline (Samples, GTI, and Gaps)",
) -> plt.Figure:
    """Plot multi-track horizontal timeline of observation samples, GTI, and gaps."""
    fig, ax = plt.subplots(figsize=(13, 3.2), dpi=150)
    t_arr = np.asarray(times, dtype=np.float64)
    n = len(t_arr)

    t0 = float(t_arr[0]) if n > 0 else 0.0
    t_end = float(t_arr[-1]) if n > 0 else 1.0
    span_h = (t_end - t0) / 3600.0

    # Track 1: Light-curve sample presence (y=2)
    if n > 0:
        rel_h = (t_arr - t0) / 3600.0
        ax.scatter(rel_h, np.full(n, 2.0), s=1.5, color="#2563eb", alpha=0.6, label="Sample Presence")

    # Track 2: GTI Intervals (y=1)
    gti_list: List[Dict[str, float]] = []
    if isinstance(gti, dict):
        gti_list = gti.get("intervals", [])
    elif isinstance(gti, list):
        gti_list = gti

    for inv in gti_list:
        s = (inv["start"] - t0) / 3600.0
        e = (inv["stop"] - t0) / 3600.0
        ax.barh(1.0, e - s, left=s, height=0.35, color="#10b981", alpha=0.85, edgecolor="#047857")

    # Track 3: Gaps (y=0)
    if gaps:
        for gp in gaps:
            s = (gp["start_time"] - t0) / 3600.0
            e = (gp["end_time"] - t0) / 3600.0
            ax.barh(0.0, max(0.01, e - s), left=s, height=0.35, color="#ef4444", alpha=0.85, edgecolor="#b91c1c")

    ax.set_yticks([0.0, 1.0, 2.0])
    ax.set_yticklabels(["Cadence Gaps", "GTI Intervals", "Observation Samples"])
    ax.set_ylim(-0.6, 2.6)
    ax.set_xlim(0, max(1.0, span_h))
    ax.set_xlabel(f"Elapsed Time (hours from t0 = {t0:.1f} s)")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.grid(True, axis="x", linestyle=":", alpha=0.6)
    fig.tight_layout()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_p, dpi=150)

    return fig


def plot_burst_gallery(
    times: np.ndarray,
    values: np.ndarray,
    candidates: Union[pd.DataFrame, List[Dict[str, Any]]],
    max_panels: int = 9,
    padding_seconds: float = 60.0,
    output_path: Optional[Path] = None,
    title: str = "Candidate Transient Bursts Gallery (EXPLORATORY — UNVERIFIED)",
) -> plt.Figure:
    """Plot small-multiples gallery of candidate transient bursts."""
    cand_df = candidates if isinstance(candidates, pd.DataFrame) else pd.DataFrame(candidates)
    n_cands = len(cand_df) if cand_df is not None else 0

    if n_cands == 0:
        fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
        ax.text(
            0.5,
            0.5,
            "No candidate transient bursts detected above threshold.\n(Status: CANDIDATE — UNVERIFIED)",
            ha="center",
            va="center",
            fontsize=12,
            color="#475569",
        )
        ax.set_axis_off()
        fig.suptitle(title, fontsize=12, fontweight="bold")
        fig.tight_layout()
        if output_path:
            fig.savefig(output_path, dpi=150)
        return fig

    n_show = min(n_cands, max_panels)
    cols = 3 if n_show >= 3 else n_show
    rows = int(np.ceil(n_show / cols))

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4.2, rows * 3.2), dpi=150, squeeze=False)
    t_arr = np.asarray(times, dtype=np.float64)
    v_arr = np.asarray(values, dtype=np.float64)

    for i in range(rows * cols):
        r, c = divmod(i, cols)
        ax = axes[r, c]
        if i < n_show:
            row = cand_df.iloc[i]
            c_start = float(row["start"])
            c_end = float(row["end"])
            p_time = float(row["peak_time"])
            p_val = float(row["peak_value"])
            c_id = row["candidate_id"]

            win_s = c_start - padding_seconds
            win_e = c_end + padding_seconds
            mask = (t_arr >= win_s) & (t_arr <= win_e)

            sub_t = t_arr[mask]
            sub_v = v_arr[mask]
            rel_t = sub_t - c_start

            ax.plot(rel_t, sub_v, color="#2563eb", linewidth=1.0)
            ax.axvspan(0.0, c_end - c_start, color="#f59e0b", alpha=0.3, label="Candidate Span")
            ax.scatter([p_time - c_start], [p_val], color="#dc2626", s=25, zorder=5, label=f"Peak: {p_val:.1f}")

            ax.set_title(f"{c_id} (Dur: {row['duration']:.1f}s | Ratio: {row['peak_to_baseline_ratio']:.1f}x)", fontsize=9.5, fontweight="bold")
            ax.set_xlabel("Time from Start (s)", fontsize=8)
            ax.set_ylabel("Counts", fontsize=8)
            ax.grid(True, linestyle=":", alpha=0.5)
            ax.legend(fontsize=7, loc="upper right")
        else:
            ax.set_axis_off()

    fig.suptitle(f"{title}\nShowing {n_show} of {n_cands} candidates — CANDIDATE: UNVERIFIED", fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_p, dpi=150, bbox_inches="tight")

    return fig
