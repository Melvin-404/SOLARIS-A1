"""Per-file quality report and figure generation for SOLARIS-A1 (Stage 4).

Generates quality.json, quality.md, and four diagnostic figures at 150 dpi:
- time_coverage.png: observation samples, GTI intervals, and cadence gaps.
- cadence_histogram.png: distribution of timestamp steps with median marked.
- count_distribution.png: linear and log histograms with zero and NaN counts annotated separately.
- flagged_samples.png: distinct visual segregation of valid, non-finite, zero, and candidate spikes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_time_coverage(
    times: np.ndarray,
    values: np.ndarray,
    gti_intervals: List[Dict[str, float]],
    cadence_gaps: List[Dict[str, Any]],
    output_path: Path,
    title: str = "Observation Time Coverage and GTI Intervals",
) -> None:
    """Plot observation time coverage with GTI intervals and cadence gaps."""
    fig, ax = plt.subplots(figsize=(12, 4.5), dpi=150)
    t_arr = np.asarray(times, dtype=np.float64)
    v_arr = np.asarray(values, dtype=np.float64)

    t0 = float(t_arr[0]) if len(t_arr) > 0 else 0.0
    rel_times_h = (t_arr - t0) / 3600.0

    # Finite sample counts
    finite_mask = np.isfinite(v_arr)
    ax.plot(
        rel_times_h[finite_mask],
        v_arr[finite_mask],
        color="#2b5c8f",
        linewidth=0.6,
        alpha=0.8,
        label="Observed Counts",
    )

    # Shaded GTI intervals
    gti_plotted = False
    for inv in gti_intervals:
        g_s = (inv["start"] - t0) / 3600.0
        g_e = (inv["stop"] - t0) / 3600.0
        lbl = "GTI (Good Time Interval)" if not gti_plotted else None
        ax.axvspan(g_s, g_e, color="#2ca02c", alpha=0.18, label=lbl)
        gti_plotted = True

    # Shaded cadence gaps
    gap_plotted = False
    for gap in cadence_gaps:
        gap_s = (gap["start_time"] - t0) / 3600.0
        gap_e = (gap["end_time"] - t0) / 3600.0
        lbl = "Cadence Gap" if not gap_plotted else None
        ax.axvspan(gap_s, gap_e, color="#d62728", alpha=0.35, label=lbl)
        gap_plotted = True

    ax.set_xlabel(f"Elapsed Time (hours from t0 = {t0:.1f} s)")
    ax.set_ylabel("Raw Counts")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_cadence_histogram(
    times: np.ndarray,
    cadence_stats: Dict[str, Any],
    output_path: Path,
    title: str = "Empirical Sampling Cadence Distribution",
) -> None:
    """Plot histogram of positive timestamp differences with median marked."""
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    t_arr = np.asarray(times, dtype=np.float64)

    if len(t_arr) > 1:
        diffs = np.diff(t_arr)
        pos_diffs = diffs[diffs > 0]
    else:
        pos_diffs = np.array([])

    med = cadence_stats.get("cadence_median", 1.0) or 1.0

    if len(pos_diffs) > 0:
        # Limit display range around nominal cadence to capture jitter
        p99 = np.percentile(pos_diffs, 99.5)
        display_diffs = pos_diffs[pos_diffs <= max(p99, med * 3.0)]
        ax.hist(display_diffs, bins=50, color="#4682b4", edgecolor="#1c3d5a", alpha=0.85)
        ax.axvline(
            med,
            color="#d62728",
            linestyle="--",
            linewidth=1.8,
            label=f"Median Cadence = {med:.4f} s",
        )
    else:
        ax.text(0.5, 0.5, "No positive timestamp differences", ha="center", va="center")

    ax.set_xlabel("Time Difference Delta t (s)")
    ax.set_ylabel("Frequency")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_count_distribution(
    values: np.ndarray,
    output_path: Path,
    title: str = "Raw Count Distribution (Zero and NaN Segregated)",
) -> None:
    """Plot linear and log histograms of counts with zero and NaN annotated separately."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=150)
    arr = np.asarray(values, dtype=np.float64)

    n_nan = int(np.isnan(arr).sum())
    finite_mask = np.isfinite(arr)
    finite_vals = arr[finite_mask]
    n_zeros = int((finite_vals == 0.0).sum()) if len(finite_vals) > 0 else 0
    non_zero_vals = finite_vals[finite_vals > 0.0] if len(finite_vals) > 0 else np.array([])

    annotation_text = (
        f"Total Samples: {len(arr):,}\n"
        f"NaN Samples: {n_nan:,} ({n_nan / max(1, len(arr)) * 100:.2f}%)\n"
        f"Zero Counts: {n_zeros:,} ({n_zeros / max(1, len(arr)) * 100:.2f}%)\n"
        f"Positive Samples: {len(non_zero_vals):,}"
    )

    # Linear subplot
    if len(non_zero_vals) > 0:
        ax1.hist(non_zero_vals, bins=50, color="#2e7d32", edgecolor="#1b5e20", alpha=0.8)
    ax1.set_xlabel("Count Value (counts > 0)")
    ax1.set_ylabel("Frequency (Linear)")
    ax1.set_title("Linear Scale (Positive Counts)", fontsize=11, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.5)
    ax1.text(
        0.95,
        0.95,
        annotation_text,
        transform=ax1.transAxes,
        ha="right",
        va="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#ced4da"),
        fontsize=9,
    )

    # Log subplot
    if len(non_zero_vals) > 0:
        ax2.hist(non_zero_vals, bins=50, color="#1565c0", edgecolor="#0d47a1", alpha=0.8, log=True)
    ax2.set_xlabel("Count Value (counts > 0)")
    ax2.set_ylabel("Frequency (Log Scale)")
    ax2.set_title("Logarithmic Scale (Positive Counts)", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.5)

    fig.suptitle(title, fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_flagged_samples(
    times: np.ndarray,
    values: np.ndarray,
    spike_indices: List[int],
    output_path: Path,
    title: str = "Light Curve Sample Quality Classification",
) -> None:
    """Plot light curve with non-finite, negative, zero, and candidate spikes visually segregated."""
    fig, ax = plt.subplots(figsize=(13, 5), dpi=150)
    t_arr = np.asarray(times, dtype=np.float64)
    v_arr = np.asarray(values, dtype=np.float64)
    total = len(t_arr)

    t0 = float(t_arr[0]) if total > 0 else 0.0
    rel_times_h = (t_arr - t0) / 3600.0

    finite_mask = np.isfinite(v_arr)
    nan_mask = np.isnan(v_arr)
    inf_mask = np.isinf(v_arr)
    negative_mask = finite_mask & (v_arr < 0.0)
    zero_mask = finite_mask & (v_arr == 0.0)
    valid_positive_mask = finite_mask & (v_arr > 0.0)

    # Plot valid positive series
    ax.scatter(
        rel_times_h[valid_positive_mask],
        v_arr[valid_positive_mask],
        s=4,
        color="#3b82f6",
        alpha=0.6,
        label="Finite Positive Counts",
    )

    # Plot zeros
    if np.any(zero_mask):
        ax.scatter(
            rel_times_h[zero_mask],
            np.zeros(np.sum(zero_mask)),
            s=12,
            color="#10b981",
            alpha=0.7,
            marker="o",
            label=f"Zero Counts ({int(zero_mask.sum()):,})",
        )

    # Plot non-finite (NaN / Inf) at baseline y=0 with distinct red 'x'
    if np.any(nan_mask):
        ax.scatter(
            rel_times_h[nan_mask],
            np.zeros(np.sum(nan_mask)),
            s=18,
            color="#ef4444",
            marker="x",
            linewidth=1.0,
            label=f"NaN Samples ({int(nan_mask.sum()):,})",
        )
    if np.any(inf_mask):
        ax.scatter(
            rel_times_h[inf_mask],
            np.zeros(np.sum(inf_mask)),
            s=22,
            color="#b91c1c",
            marker="^",
            label=f"+/-Inf Samples ({int(inf_mask.sum()):,})",
        )

    # Plot negative values if any
    if np.any(negative_mask):
        ax.scatter(
            rel_times_h[negative_mask],
            v_arr[negative_mask],
            s=24,
            color="#8b5cf6",
            marker="v",
            label=f"Negative Values ({int(negative_mask.sum()):,})",
        )

    # Plot candidate spikes
    if spike_indices:
        spk_idx = [i for i in spike_indices if i < total]
        if spk_idx:
            ax.scatter(
                rel_times_h[spk_idx],
                v_arr[spk_idx],
                s=28,
                facecolors="none",
                edgecolors="#f59e0b",
                linewidth=1.2,
                label=f"Candidate Spikes ({len(spk_idx):,}) — not verified events",
            )

    ax.set_xlabel(f"Elapsed Time (hours from t0 = {t0:.1f} s)")
    ax.set_ylabel("Raw Counts")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right", framealpha=0.92, fontsize=9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def generate_file_report(
    file_stem: str,
    output_dir: Path,
    checks_results: Dict[str, Any],
    cadence_results: Dict[str, Any],
    gti_results: Dict[str, Any],
    role_status: str = "PROVISIONAL",
) -> None:
    """Write quality.json and quality.md for a single paired dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)

    report_payload = {
        "file_stem": file_stem,
        "role_status": role_status,
        "overall_status": "PROVISIONAL pending G1",
        "cadence_analysis": cadence_results,
        "gti_coverage": gti_results,
        "checks": checks_results,
    }

    # Write quality.json
    json_path = output_dir / "quality.json"
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(report_payload, jf, indent=2)

    # Write quality.md
    md_path = output_dir / "quality.md"
    lines = [
        f"# Data Quality Report: `{file_stem}`",
        "",
        "> **PROVISIONAL STATUS NOTICE (Gate G1 / G2 Pending):**",
        "> All column roles, time systems, and quality thresholds in this report are strictly **PROVISIONAL**.",
        "> Column roles require confirmation by the student researcher at Gate G1.",
        "> Quality thresholds require confirmation at Gate G2. No data has been modified, filtered, or interpolated.",
        "",
        "---",
        "",
        "## Summary Overview",
        "",
        f"- **File Stem:** `{file_stem}`",
        f"- **Role Confirmation Status:** `{role_status}`",
        f"- **Stage 4 Assessment Status:** `PROVISIONAL pending G1`",
        f"- **Sampling Cadence (Median):** `{cadence_results.get('cadence_median', 'N/A')} s`",
        f"- **Cadence Gaps Detected:** `{cadence_results.get('n_cadence_gaps', 'N/A')}`",
        f"- **GTI Observation Status:** `{gti_results.get('gti_status', 'N/A')}`",
        f"- **GTI Covered Fraction:** `{gti_results.get('gti_covered_fraction', 0.0) * 100:.2f}%`",
        f"- **Samples Inside GTI:** `{gti_results.get('n_samples_inside_gti', 'N/A'):,}`",
        f"- **Samples Outside GTI:** `{gti_results.get('n_samples_outside_gti', 'N/A'):,}`",
        "",
        "---",
        "",
        "## Quality Checks Table",
        "",
        "| Check Name | Status | Key Metric / Count | Details |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for check_key, res in checks_results.items():
        cname = res.get("name", check_key)
        cstatus = res.get("status", "UNKNOWN")
        counts = res.get("counts", {})
        detail = res.get("detail", "")

        # Format concise metric
        if cname == "check_non_finite":
            metric = f"NaN: {counts.get('n_nan', 0)}, +inf: {counts.get('n_pos_inf', 0)}, -inf: {counts.get('n_neg_inf', 0)}"
            detail_str = str(detail)
        elif cname == "check_negative_values":
            metric = f"Negative: {counts.get('n_negative', 0)}"
            detail_str = detail.get("message", "") if isinstance(detail, dict) else str(detail)
        elif cname == "check_duplicate_timestamps":
            metric = f"Duplicates: {counts.get('n_duplicates', 0)}"
            detail_str = detail.get("message", "") if isinstance(detail, dict) else str(detail)
        elif cname == "check_time_ordering":
            metric = f"Backward steps: {counts.get('n_backward_steps', 0)}"
            detail_str = detail.get("message", "") if isinstance(detail, dict) else str(detail)
        elif cname == "check_zero_runs":
            metric = f"Zero count: {counts.get('n_zero_samples', 0)}, Zero runs: {counts.get('n_zero_runs', 0)}"
            detail_str = detail.get("message", "") if isinstance(detail, dict) else str(detail)
        elif cname == "check_quality_flags":
            metric = f"Total samples: {counts.get('total_samples', 0)}"
            detail_str = detail.get("interpretation_status", "") if isinstance(detail, dict) else str(detail)
        elif cname == "check_candidate_spikes":
            metric = f"Candidate spikes: {counts.get('n_candidate_spikes', 0)}"
            detail_str = "Labelled: candidate spike — not a verified event. Threshold: z > " + str(counts.get("z_threshold", 5.0))
        else:
            metric = str(counts)
            detail_str = str(detail)

        lines.append(f"| `{cname}` | **{cstatus}** | {metric} | {detail_str} |")

    lines.extend([
        "",
        "---",
        "",
        "## Diagnostic Figures Generated",
        "",
        "1. **Time Coverage & GTI Intervals:** [`time_coverage.png`](time_coverage.png)",
        "2. **Cadence Histogram:** [`cadence_histogram.png`](cadence_histogram.png)",
        "3. **Count Distribution (Linear & Log):** [`count_distribution.png`](count_distribution.png)",
        "4. **Classified & Flagged Samples:** [`flagged_samples.png`](flagged_samples.png)",
        "",
    ])

    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write("\n".join(lines))
