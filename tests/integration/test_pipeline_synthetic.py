"""Integration test: End-to-end synthetic pipeline execution (Stage 14).

Generates synthetic LC and GTI FITS fixtures named SYNTHETIC_* using astropy.io.fits
strictly in tmp_path. Executes:
1. FITS Inspection
2. Quality Assessment
3. Preprocessing & Continuous Segmentation (development mode)
4. Sliding Windows & Causal Feature Engineering
5. Dataset Export under synthetic APPROVED policy
Asserts that each stage produces the expected artifacts and sample reconciliation holds.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from astropy.io import fits

from solar_flare.inspection.fits_inspect import list_hdus, describe_columns, summarise_numeric_columns
from solar_flare.quality.checks import check_non_finite, check_negative_values, check_duplicate_timestamps
from solar_flare.quality.gti_coverage import load_gti_intervals, compute_coverage
from solar_flare.preprocessing.filters import exclude_non_finite, exclude_negative
from solar_flare.preprocessing.gti_apply import apply_gti
from solar_flare.preprocessing.segmentation import segment_continuous
from solar_flare.preprocessing.audit import ProcessingAudit
from solar_flare.features.windows import generate_windows
from solar_flare.features.registry import compute_features
from solar_flare.features.baseline import causal_baseline
from solar_flare.export.export import export_dataset


def create_synthetic_pipeline_fixtures(base_dir: Path) -> tuple[Path, Path]:
    """Create SYNTHETIC_LC.fits and SYNTHETIC_GTI.fits in base_dir."""
    n_rows = 300
    times = np.arange(n_rows, dtype=np.float64)  # 1-second cadence: 0..299
    counts = np.full(n_rows, 50.0)

    # Inject known variations: a few NaNs, a few zeros
    counts[10] = np.nan
    counts[11] = np.nan
    counts[25] = 0.0

    # 1. Light Curve FITS
    primary_lc = fits.PrimaryHDU()
    primary_lc.header["TELESCOP"] = "SYNTHETIC_TEL"
    primary_lc.header["INSTRUME"] = "SYNTHETIC_INST"
    primary_lc.header["OBS_ID"] = "SYNTHETIC_OBS_001"

    col_t = fits.Column(name="TIME", format="D", unit="s", array=times)
    col_c = fits.Column(name="COUNTS", format="D", unit="count", array=counts)
    tb_lc = fits.BinTableHDU.from_columns([col_t, col_c], name="RATE")
    tb_lc.header["TIMESYS"] = "UTC"
    tb_lc.header["TSTART"] = 0.0
    tb_lc.header["TSTOP"] = float(times[-1])
    tb_lc.header["MJDREFI"] = 40587

    lc_path = base_dir / "SYNTHETIC_LC.fits"
    fits.HDUList([primary_lc, tb_lc]).writeto(str(lc_path), overwrite=True)

    # 2. GTI FITS: two intervals [0.0, 120.0] and [140.0, 280.0] (with a gap of 20 s)
    primary_gti = fits.PrimaryHDU()
    gti_starts = np.array([0.0, 140.0], dtype=np.float64)
    gti_stops = np.array([120.0, 280.0], dtype=np.float64)
    col_gstart = fits.Column(name="START", format="D", array=gti_starts)
    col_gstop = fits.Column(name="STOP", format="D", array=gti_stops)
    tb_gti = fits.BinTableHDU.from_columns([col_gstart, col_gstop], name="GTI")

    gti_path = base_dir / "SYNTHETIC_GTI.fits"
    fits.HDUList([primary_gti, tb_gti]).writeto(str(gti_path), overwrite=True)

    return lc_path, gti_path


def test_synthetic_end_to_end_pipeline(tmp_path: Path):
    """Run full synthetic pipeline and assert artifacts and sample reconciliation."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True)

    lc_path, gti_path = create_synthetic_pipeline_fixtures(data_dir)

    # ---------------------------------------------------------
    # STAGE 3: Inspection
    # ---------------------------------------------------------
    hdus = list_hdus(lc_path)
    assert "RATE" in [h["name"] for h in hdus]
    rate_desc = describe_columns(lc_path, "RATE")
    col_names = [c["name"] for c in rate_desc]
    assert "TIME" in col_names
    assert "COUNTS" in col_names
    stats = summarise_numeric_columns(lc_path, "RATE")
    assert "COUNTS" in stats
    assert stats["COUNTS"]["nan_count"] == 2

    # ---------------------------------------------------------
    # STAGE 4: Quality Assessment
    # ---------------------------------------------------------
    with fits.open(lc_path) as hdul:
        tb_data = hdul["RATE"].data
        df_raw = pd.DataFrame({
            "TIME": np.array(tb_data["TIME"], dtype=np.float64),
            "COUNTS": np.array(tb_data["COUNTS"], dtype=np.float64),
        })

    nan_res = check_non_finite(df_raw["COUNTS"].values)
    assert nan_res["counts"]["n_nan"] == 2
    assert nan_res["counts"]["n_pos_inf"] == 0

    neg_res = check_negative_values(df_raw["COUNTS"].values)
    assert neg_res["counts"]["n_negative"] == 0

    dup_res = check_duplicate_timestamps(df_raw["TIME"].values)
    assert dup_res["counts"]["n_duplicates"] == 0

    gti_res = load_gti_intervals(gti_path)
    assert gti_res["n_intervals"] == 2
    gti_intervals = gti_res["intervals"]
    assert len(gti_intervals) == 2
    cov = compute_coverage(df_raw["TIME"].values, gti_res)
    assert cov["n_samples_inside_gti"] > 0
    assert cov["gti_covered_fraction"] < 1.0  # Due to the gap between 120 and 140

    # ---------------------------------------------------------
    # STAGE 7: Preprocessing & Continuous Segmentation
    # ---------------------------------------------------------
    audit = ProcessingAudit(
        file_stem="SYNTHETIC_LC",
        original_sample_count=len(df_raw),
        source_file_sha256_before="mock_sha",
        parameters={},
        is_final_run=False,
    )

    # 1. Non-finite filtering
    finite_df, nan_excl = exclude_non_finite(df_raw, value_col="COUNTS", time_col="TIME")
    audit.add_exclusions(nan_excl)
    assert len(nan_excl) == 2

    # 2. Negative filtering
    nonneg_df, neg_excl = exclude_negative(finite_df, value_col="COUNTS", time_col="TIME")
    audit.add_exclusions(neg_excl)
    assert len(neg_excl) == 0

    # 3. GTI application
    gti_applied_df, gti_excl = apply_gti(
        nonneg_df,
        time_col="TIME",
        gti_intervals=gti_intervals,
        boundary="START_INCLUSIVE_STOP_EXCLUSIVE",
    )
    audit.add_exclusions(gti_excl)
    assert len(gti_excl) > 0

    # 4. Continuous segmentation (gap threshold = 3.0 s, min_len = 20 s)
    segments, seg_excl = segment_continuous(
        gti_applied_df,
        time_col="TIME",
        max_gap_seconds=3.0,
        min_segment_seconds=20.0,
        stem="SYNTHETIC_LC",
    )
    audit.add_exclusions(seg_excl)
    assert len(segments) >= 2

    # Total samples retained across all segments
    n_retained = sum(len(s.dataframe) for s in segments)
    audit.set_retained(n_retained, segments)

    # CRITICAL: Verify exact sample reconciliation
    assert audit.reconcile()
    assert audit.original_sample_count == n_retained + len(audit.get_consolidated_exclusion_log())

    # ---------------------------------------------------------
    # STAGE 8: Sliding Windows and Causal Features
    # ---------------------------------------------------------
    all_window_indices = []
    all_feature_rows = []

    for seg_idx, seg in enumerate(segments):
        win_idx_df, _ = generate_windows(
            seg.dataframe,
            segment_id=seg.segment_id,
            window_seconds=30.0,
            stride_seconds=10.0,
            time_col="TIME",
            value_col="COUNTS",
        )
        if not win_idx_df.empty:
            times_seg = seg.dataframe["TIME"].to_numpy(dtype=np.float64)
            counts_seg = seg.dataframe["COUNTS"].to_numpy(dtype=np.float64)

            for _, w_row in win_idx_df.iterrows():
                w_start = float(w_row["window_start"])
                s_idx = int(w_row["start_index"])
                e_idx = int(w_row["end_index"]) + 1

                w_times = times_seg[s_idx:e_idx]
                w_vals = counts_seg[s_idx:e_idx]

                base_val, _ = causal_baseline(
                    segment_df=seg.dataframe,
                    window_start=w_start,
                    lookback_seconds=60.0,
                    time_col="TIME",
                    value_col="COUNTS",
                    min_samples=5,
                    is_final=False,
                )

                feat_vals, _ = compute_features(
                    window_values=w_vals,
                    window_times=w_times,
                    baseline_value=base_val,
                    n_expected_samples=30,
                )
                row_dict = {"window_id": w_row["window_id"]}
                row_dict.update(feat_vals)
                all_feature_rows.append(row_dict)

            all_window_indices.append(win_idx_df)

    assert len(all_window_indices) > 0
    full_win_idx = pd.concat(all_window_indices, ignore_index=True)
    full_features = pd.DataFrame(all_feature_rows)
    assert len(full_win_idx) == len(full_features)
    assert "mean" in full_features.columns
    assert "median" in full_features.columns
    assert "std" in full_features.columns

    # ---------------------------------------------------------
    # STAGE 9: Label Integration & Dataset Export
    # ---------------------------------------------------------
    # Synthetic approved labels
    n_windows = len(full_win_idx)
    labels = [1 if i % 4 == 0 else 0 for i in range(n_windows)]
    reasons = ["SYNTHETIC_FLARE" if lab == 1 else "SYNTHETIC_QUIET" for lab in labels]

    labels_df = pd.DataFrame({
        "window_id": full_win_idx["window_id"],
        "label_detection": pd.Series(labels, dtype="Int8"),
        "label_reason": reasons,
    })

    export_out = results_dir / "datasets"
    export_dir = export_dataset(
        task="detection",
        features_df=full_features,
        labels_df=labels_df,
        window_index_df=full_win_idx,
        out_root=export_out,
        config_snapshot={"window_seconds": 30.0, "stride_seconds": 10.0},
        policy_text="Status: APPROVED by Synthetic Researcher, date 2026-10-21",
        event_count=sum(labels),
        min_events_required=2,
    )

    assert export_dir.is_dir()
    assert (export_dir / "X_features.csv").is_file()
    assert (export_dir / "y_labels.csv").is_file()
    assert (export_dir / "metadata.csv").is_file()
    assert (export_dir / "exclusions.csv").is_file()
    assert (export_dir / "config_snapshot.yaml").is_file()

    # Verify X_features contains no labels or timestamps
    X = pd.read_csv(export_dir / "X_features.csv")
    assert "window_id" not in X.columns
    assert "label" not in X.columns
    assert "TIME" not in X.columns
    assert len(X) == n_windows
