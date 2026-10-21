"""Integration test: Synthetic pipeline reproducibility check (Stage 14).

Runs the synthetic pipeline twice in separate temporary directories with identical
configuration. Compares hashes of deterministic artifacts (CSV, JSON, YAML) and
reports any differences.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from astropy.io import fits

from solar_flare.preprocessing.filters import exclude_non_finite, exclude_negative
from solar_flare.preprocessing.gti_apply import apply_gti
from solar_flare.preprocessing.segmentation import segment_continuous
from solar_flare.preprocessing.audit import ProcessingAudit
from solar_flare.features.windows import generate_windows
from solar_flare.features.baseline import causal_baseline
from solar_flare.features.registry import compute_features
from solar_flare.export.export import export_dataset


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_pipeline_instance(base_dir: Path) -> dict[str, Path]:
    """Execute synthetic pipeline in base_dir and return dict of generated artifact paths."""
    data_dir = base_dir / "data"
    results_dir = base_dir / "results"
    data_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)

    # 1. Generate identical synthetic input data
    n_rows = 200
    times = np.arange(n_rows, dtype=np.float64)
    counts = np.full(n_rows, 42.0)
    counts[5] = np.nan
    counts[15] = 100.0

    primary = fits.PrimaryHDU()
    col_t = fits.Column(name="TIME", format="D", unit="s", array=times)
    col_c = fits.Column(name="COUNTS", format="D", unit="count", array=counts)
    tb = fits.BinTableHDU.from_columns([col_t, col_c], name="RATE")
    lc_path = data_dir / "SYNTHETIC_LC.fits"
    fits.HDUList([primary, tb]).writeto(str(lc_path), overwrite=True)

    gti_intervals = [{"start": 0.0, "stop": 180.0}]

    # 2. Preprocess
    df_raw = pd.DataFrame({"TIME": times, "COUNTS": counts})
    audit = ProcessingAudit(
        file_stem="SYNTHETIC_LC",
        original_sample_count=len(df_raw),
        source_file_sha256_before=compute_sha256(lc_path),
        parameters={},
        is_final_run=False,
    )

    finite_df, nan_excl = exclude_non_finite(df_raw, value_col="COUNTS", time_col="TIME")
    audit.add_exclusions(nan_excl)

    nonneg_df, neg_excl = exclude_negative(finite_df, value_col="COUNTS", time_col="TIME")
    audit.add_exclusions(neg_excl)

    gti_df, gti_excl = apply_gti(nonneg_df, time_col="TIME", gti_intervals=gti_intervals)
    audit.add_exclusions(gti_excl)

    segments, seg_excl = segment_continuous(
        gti_df, time_col="TIME", max_gap_seconds=3.0, min_segment_seconds=20.0, stem="SYNTHETIC_LC"
    )
    audit.add_exclusions(seg_excl)

    n_retained = sum(len(s.dataframe) for s in segments)
    audit.set_retained(n_retained, segments)
    assert audit.reconcile()

    # Save segment CSV
    seg_dir = results_dir / "segments"
    seg_dir.mkdir(parents=True)
    seg_path = seg_dir / "segment_001.csv"
    segments[0].dataframe.to_csv(seg_path, index=False)

    # 3. Features
    win_idx_df, _ = generate_windows(
        segments[0].dataframe,
        segment_id="SEG_01",
        window_seconds=30.0,
        stride_seconds=10.0,
    )
    w_idx_path = results_dir / "window_index.csv"
    win_idx_df.to_csv(w_idx_path, index=False)

    times_seg = segments[0].dataframe["TIME"].to_numpy(dtype=np.float64)
    counts_seg = segments[0].dataframe["COUNTS"].to_numpy(dtype=np.float64)
    all_feature_rows = []

    for _, w_row in win_idx_df.iterrows():
        w_start = float(w_row["window_start"])
        s_idx = int(w_row["start_index"])
        e_idx = int(w_row["end_index"]) + 1

        base_val, _ = causal_baseline(
            segment_df=segments[0].dataframe,
            window_start=w_start,
            lookback_seconds=60.0,
            min_samples=5,
            is_final=False,
        )

        feat_vals, _ = compute_features(
            window_values=counts_seg[s_idx:e_idx],
            window_times=times_seg[s_idx:e_idx],
            baseline_value=base_val,
            n_expected_samples=30,
        )
        row = {"window_id": w_row["window_id"]}
        row.update(feat_vals)
        all_feature_rows.append(row)

    feat_df = pd.DataFrame(all_feature_rows)
    feat_path = results_dir / "window_features.csv"
    feat_df.to_csv(feat_path, index=False)

    # 4. Export
    labels_df = pd.DataFrame({
        "window_id": win_idx_df["window_id"],
        "label_detection": pd.Series([0] * len(win_idx_df), dtype="Int8"),
        "label_reason": ["QUIET"] * len(win_idx_df),
    })

    export_out = results_dir / "datasets"
    export_dir = export_dataset(
        task="detection",
        features_df=feat_df,
        labels_df=labels_df,
        window_index_df=win_idx_df,
        out_root=export_out,
        config_snapshot={"window_seconds": 30.0, "stride_seconds": 10.0},
        policy_text="Status: APPROVED by Synthetic Researcher, date 2026-10-21",
        event_count=0,
        min_events_required=1,
    )

    return {
        "segment_csv": seg_path,
        "window_index_csv": w_idx_path,
        "features_csv": feat_path,
        "X_features_csv": export_dir / "X_features.csv",
        "y_labels_csv": export_dir / "y_labels.csv",
        "metadata_csv": export_dir / "metadata.csv",
        "exclusions_csv": export_dir / "exclusions.csv",
        "config_snapshot_yaml": export_dir / "config_snapshot.yaml",
    }


def test_synthetic_reproducibility_identical_hashes(tmp_path: Path):
    """Run pipeline twice in separate temp dirs; verify all deterministic artifacts match bit-for-bit."""
    dir1 = tmp_path / "run_1"
    dir2 = tmp_path / "run_2"

    artifacts1 = run_pipeline_instance(dir1)
    artifacts2 = run_pipeline_instance(dir2)

    assert set(artifacts1.keys()) == set(artifacts2.keys())

    differences = []
    matches = []

    for key, path1 in artifacts1.items():
        path2 = artifacts2[key]
        assert path1.is_file(), f"Missing artifact in run 1: {path1}"
        assert path2.is_file(), f"Missing artifact in run 2: {path2}"

        hash1 = compute_sha256(path1)
        hash2 = compute_sha256(path2)

        if hash1 == hash2:
            matches.append(key)
        else:
            differences.append((key, hash1, hash2))

    # All deterministic artifacts MUST match 100%
    assert not differences, f"Reproducibility divergence detected in deterministic artifacts: {differences}"
    assert len(matches) == len(artifacts1)
    assert "X_features_csv" in matches
    assert "y_labels_csv" in matches
    assert "metadata_csv" in matches
    assert "config_snapshot_yaml" in matches
