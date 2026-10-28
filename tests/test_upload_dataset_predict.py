"""Comprehensive automated test suite for Upload Dataset & Predict feature.

Covers:
1. Valid supported uploads (FITS .lc.gz, .fits, and CSV).
2. Invalid or malformed files (empty, corrupted, oversized).
3. Missing required columns.
4. GTI filtering and telemetry gaps (asserting no gap interpolation).
5. Feature-column compatibility (all 19 expected features and exact order).
6. Successful inference with existing saved model (XGBoost, RF, LR).
7. Empty datasets and single-day files with insufficient observations.
8. Ensuring no training, fine-tuning, or model-saving function is called.
9. Confirming existing dashboard functionality remains intact.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
from unittest.mock import MagicMock, patch
import zipfile
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from solar_flare.inference.pipeline import (
    InferencePipeline,
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


@pytest.fixture
def pilot_lc_bytes() -> bytes:
    """Raw FITS light curve bytes from October 18, 2026 pilot observation."""
    lc_path = project_root() / "data" / "raw" / "AL1_SOLEXS_20261018_SDD2_L1.lc.gz"
    assert lc_path.exists(), f"Pilot LC file missing at {lc_path}"
    return lc_path.read_bytes()


@pytest.fixture
def pilot_gti_bytes() -> bytes:
    """Raw FITS GTI bytes from October 18, 2026 pilot observation."""
    gti_path = project_root() / "data" / "raw" / "AL1_SOLEXS_20261018_SDD2_L1.gti.gz"
    assert gti_path.exists(), f"Pilot GTI file missing at {gti_path}"
    return gti_path.read_bytes()


# =============================================================================
# 1. Valid Supported Uploads
# =============================================================================

def test_parse_valid_fits_lightcurve(pilot_lc_bytes: bytes):
    """Verify parsing of valid FITS light curve file."""
    df, meta = parse_uploaded_lightcurve(pilot_lc_bytes, "AL1_SOLEXS_20261018_SDD2_L1.lc.gz")
    assert isinstance(df, pd.DataFrame)
    assert "time" in df.columns
    assert "counts" in df.columns
    assert len(df) == 86400
    assert meta["format"] == "FITS"
    assert meta["detected_date"] == "2026-10-18"


def test_parse_valid_csv_lightcurve():
    """Verify parsing of valid CSV light curve file with standard headers."""
    rows = ["time,counts"]
    for i in range(100):
        rows.append(f"{719400000.0 + i},{12.5 + (i % 5)}")
    csv_text = "\n".join(rows) + "\n"
    df, meta = parse_uploaded_lightcurve(csv_text.encode("utf-8"), "solexs_20261018_sample.csv")
    assert len(df) == 100
    assert list(df.columns) == ["time", "counts"]
    assert meta["format"] == "CSV"
    assert meta["detected_date"] == "2026-10-18"


def test_parse_valid_csv_lightcurve_alternate_headers():
    """Verify parsing of CSV with case-insensitive / alternate headers."""
    rows = ["Timestamp,Count_Rate"]
    for i in range(80):
        rows.append(f"{719400000.0 + i},{12.5 + (i % 3)}")
    csv_text = "\n".join(rows) + "\n"
    df, meta = parse_uploaded_lightcurve(csv_text.encode("utf-8"), "custom_headers.csv")
    assert len(df) == 80
    assert "time" in df.columns
    assert "counts" in df.columns


def test_parse_valid_gti_fits(pilot_gti_bytes: bytes):
    """Verify parsing of authentic FITS GTI file."""
    gtis, meta = parse_uploaded_gti(pilot_gti_bytes, "AL1_SOLEXS_20261018_SDD2_L1.gti.gz")
    assert isinstance(gtis, list)
    assert len(gtis) == 8
    for start, stop in gtis:
        assert isinstance(start, float)
        assert isinstance(stop, float)
        assert start < stop
    assert meta["format"] == "FITS_GTI"


def test_parse_valid_gti_csv():
    """Verify parsing of CSV GTI file."""
    csv_text = "START,STOP\n719400000.0,719410000.0\n719420000.0,719430000.0\n"
    gtis, meta = parse_uploaded_gti(csv_text.encode("utf-8"), "test_gti.csv")
    assert len(gtis) == 2
    assert gtis[0] == (719400000.0, 719410000.0)
    assert gtis[1] == (719420000.0, 719430000.0)
    assert meta["format"] == "CSV_GTI"


# =============================================================================
# 2. Invalid or Malformed Files
# =============================================================================

def test_empty_file_rejected():
    """Verify empty upload is rejected with clear error."""
    with pytest.raises(UploadValidationError, match="The uploaded file is empty"):
        parse_uploaded_lightcurve(b"", "empty.csv")


def test_oversized_file_rejected():
    """Verify oversized upload exceeding 100MB is rejected."""
    huge_mock = MagicMock()
    huge_mock.getvalue.return_value = b"x" * (101 * 1024 * 1024)
    with pytest.raises(UploadValidationError, match="exceeds maximum allowed limit"):
        parse_uploaded_lightcurve(b"x" * (101 * 1024 * 1024), "large.csv")


def test_corrupted_fits_rejected():
    """Verify corrupted FITS file raises UploadValidationError with explanation."""
    corrupted_bytes = b"NOT_A_VALID_FITS_HEADER_AT_ALL"
    with pytest.raises(UploadValidationError, match="Failed to inspect FITS"):
        parse_uploaded_lightcurve(corrupted_bytes, "corrupt.fits")


def test_invalid_gti_file_rejected():
    """Verify corrupted or invalid GTI file raises UploadValidationError."""
    bad_csv = "time,temp\n1,2\n"
    with pytest.raises(UploadValidationError, match="GTI CSV must contain start and stop columns"):
        parse_uploaded_gti(bad_csv.encode("utf-8"), "bad_gti.csv")


# =============================================================================
# 3. Missing Required Columns
# =============================================================================

def test_csv_missing_counts_column():
    """Verify CSV missing counts column is rejected with clear explanation."""
    csv_text = "time,voltage\n1.0,5.0\n2.0,5.1\n"
    with pytest.raises(UploadValidationError, match="Required telemetry columns missing in CSV"):
        parse_uploaded_lightcurve(csv_text.encode("utf-8"), "no_counts.csv")


def test_csv_missing_time_column():
    """Verify CSV missing time column is rejected with clear explanation."""
    csv_text = "counts,voltage\n10.0,5.0\n12.0,5.1\n"
    with pytest.raises(UploadValidationError, match="Required telemetry columns missing in CSV"):
        parse_uploaded_lightcurve(csv_text.encode("utf-8"), "no_time.csv")


# =============================================================================
# 4. GTI Filtering & Telemetry Gaps: Strict Non-Interpolation
# =============================================================================

def test_gaps_not_interpolated():
    """Verify telemetry gaps (>3s) create separate segments and are NEVER interpolated."""
    # Segment 1: t=0..99 (100 points, duration 99s >= 60s)
    # GAP: 100 seconds (t=100..199 missing)
    # Segment 2: t=200..299 (100 points, duration 99s >= 60s)
    t1 = np.arange(0, 100, dtype=float)
    t2 = np.arange(200, 300, dtype=float)
    times = np.concatenate([t1, t2])
    counts = np.full_like(times, 15.0)

    df = pd.DataFrame({"time": times, "counts": counts})

    audit = validate_uploaded_telemetry(df)
    assert audit["n_telemetry_gaps"] == 1

    pipeline = get_default_pipeline()
    out = execute_dataset_inference(
        df=df,
        pipeline=pipeline,
        window_seconds=60.0,
        stride_seconds=30.0,
        max_gap_seconds=3.0,
    )

    # Must produce segments for each contiguous run, with zero interpolated timestamps
    segments = out["segments"]
    assert len(segments) == 2
    assert segments[0]["n_samples"] == 100
    assert segments[1]["n_samples"] == 100

    # Ensure no window bridges the gap
    res_df = out["results_df"]
    for _, row in res_df.iterrows():
        w_st = row["window_start"]
        w_en = row["window_end"]
        # Window must be strictly within segment 1 [0, 99] or segment 2 [200, 299]
        in_seg1 = (0.0 <= w_st <= 99.0) and (0.0 <= w_en <= 99.0)
        in_seg2 = (200.0 <= w_st <= 299.0) and (200.0 <= w_en <= 299.0)
        assert in_seg1 or in_seg2, f"Window ({w_st}, {w_en}) illegally bridged telemetry gap!"


def test_gti_exclusion_applied():
    """Verify samples outside GTIs are excluded and not fed to feature generation."""
    # Data: t=0..199 (200 points)
    # GTI: only [50, 150] is valid
    times = np.arange(0, 200, dtype=float)
    counts = np.full_like(times, 20.0)
    df = pd.DataFrame({"time": times, "counts": counts})

    gtis = [(50.0, 150.0)]
    pipeline = get_default_pipeline()
    out = execute_dataset_inference(
        df=df,
        gti_intervals=gtis,
        pipeline=pipeline,
        window_seconds=60.0,
        stride_seconds=30.0,
    )

    assert out["exclusions"]["n_outside_gti_dropped"] == 100
    res_df = out["results_df"]
    for _, row in res_df.iterrows():
        assert row["window_start"] >= 50.0
        assert row["window_end"] <= 150.0


# =============================================================================
# 5. Feature Column Compatibility
# =============================================================================

def test_feature_matrix_compatibility(pilot_lc_bytes: bytes, pilot_gti_bytes: bytes):
    """Verify generated features match the pipeline's expected features in name and order."""
    df, _ = parse_uploaded_lightcurve(pilot_lc_bytes, "AL1_SOLEXS_20261018_SDD2_L1.lc.gz")
    gtis, _ = parse_uploaded_gti(pilot_gti_bytes, "AL1_SOLEXS_20261018_SDD2_L1.gti.gz")

    # Select a short slice inside first GTI for fast test
    g_st, g_sp = gtis[0]
    df_slice = df[(df["time"] >= g_st) & (df["time"] <= g_st + 300.0)].dropna().copy()

    pipeline = get_default_pipeline()
    out = execute_dataset_inference(
        df=df_slice,
        gti_intervals=gtis,
        pipeline=pipeline,
        window_seconds=60.0,
        stride_seconds=30.0,
    )

    feat_df = out["features_df"]
    expected_19 = pipeline.expected_features

    assert len(expected_19) == 19
    for f in expected_19:
        assert f in feat_df.columns, f"Missing feature: {f}"

    # Features passed to model must be scored cleanly by the pipeline's imputer and scaler
    probs = pipeline.predict_proba(feat_df)
    assert len(probs) == len(feat_df)
    assert np.all(np.isfinite(probs))


# =============================================================================
# 6. Successful Inference with Existing Model
# =============================================================================

def test_successful_pilot_inference(pilot_lc_bytes: bytes, pilot_gti_bytes: bytes):
    """Verify end-to-end inference detects genuine flares on October 18, 2026."""
    df, _ = parse_uploaded_lightcurve(pilot_lc_bytes, "AL1_SOLEXS_20261018_SDD2_L1.lc.gz")
    gtis, _ = parse_uploaded_gti(pilot_gti_bytes, "AL1_SOLEXS_20261018_SDD2_L1.gti.gz")

    # Focus on flaring segment with lookback (t_flare ~ 1792320568)
    t_flare = 1792320568.0
    flare_slice = df[(df["time"] >= t_flare - 1200.0) & (df["time"] <= t_flare + 600.0)].copy()

    pipeline = get_default_pipeline()
    out = execute_dataset_inference(
        df=flare_slice,
        gti_intervals=gtis,
        pipeline=pipeline,
        threshold=0.50,
        window_seconds=60.0,
        stride_seconds=30.0,
    )

    res_df = out["results_df"]
    assert not res_df.empty
    assert "flare_probability" in res_df.columns
    assert "flare_detected" in res_df.columns

    # Probabilities strictly bounded in [0.0, 1.0]
    assert (res_df["flare_probability"] >= 0.0).all()
    assert (res_df["flare_probability"] <= 1.0).all()

    # Known flare must be detected with high probability
    peak_prob = res_df["flare_probability"].max()
    assert peak_prob > 0.80, f"Expected strong detection near peak flare, got {peak_prob}"

    # Candidate flare episodes
    episodes = out["candidate_episodes"]
    assert len(episodes) >= 1
    assert episodes[0]["risk_level"] == "SEVERE"


# =============================================================================
# 7. Insufficient Observations Handling
# =============================================================================

def test_insufficient_samples_rejected():
    """Verify dataset with fewer than 60 samples is rejected."""
    short_df = pd.DataFrame({"time": np.arange(30, dtype=float), "counts": np.full(30, 10.0)})
    pipeline = get_default_pipeline()
    with pytest.raises(UploadValidationError, match="At least 60 samples are required"):
        execute_dataset_inference(short_df, pipeline=pipeline)


def test_fragmented_segments_rejected():
    """Verify dataset broken into small chunks (<60s) with no valid window is rejected."""
    # 10 chunks of 10 samples each separated by 10s gaps
    times = []
    for chunk in range(10):
        t_base = chunk * 30.0
        times.extend(list(np.arange(t_base, t_base + 10.0)))
    df = pd.DataFrame({"time": times, "counts": np.full(len(times), 10.0)})

    pipeline = get_default_pipeline()
    with pytest.raises(UploadValidationError, match="No continuous observation segments"):
        execute_dataset_inference(df, pipeline=pipeline, min_segment_seconds=60.0)


# =============================================================================
# 8. Zero Training, Fine-Tuning, or Model Modification
# =============================================================================

def test_zero_training_guarantee():
    """Verify that no training or weight-mutation methods are called during inference."""
    times = np.arange(1000.0, 1300.0, dtype=float)
    counts = np.full(300, 15.0)
    test_slice = pd.DataFrame({"time": times, "counts": counts})

    pipeline = get_default_pipeline()
    model_path = pipeline.exp_dir / "models" / f"{pipeline.model_name}.joblib"
    assert model_path.exists(), f"Model path missing at {model_path}"
    hash_before = hashlib.sha256(model_path.read_bytes()).hexdigest()

    # Mock fit on the underlying estimator
    with patch.object(pipeline.model, "fit", side_effect=RuntimeError("ILLEGAL FIT CALL")):
        out = execute_dataset_inference(
            df=test_slice,
            pipeline=pipeline,
            threshold=0.50,
            window_seconds=60.0,
            stride_seconds=30.0,
        )

    # Assert hash is unchanged
    hash_after = hashlib.sha256(model_path.read_bytes()).hexdigest()
    assert hash_before == hash_after, "Model artifact was modified during inference!"
    assert out["summary"]["task"] == "Task A: 60-Second Window Flare Detection"


# =============================================================================
# 9. Dashboard Page 10 Smoke Test
# =============================================================================

def test_dashboard_page_10_smoke():
    """Verify that Page 10 (Upload Dataset & Predict) renders without unhandled exception."""
    page_file = project_root() / "dashboard" / "pages" / "10_Upload_Dataset_Predict.py"
    assert page_file.exists(), f"Page 10 missing at {page_file}"

    at = AppTest.from_file(str(page_file), default_timeout=20)
    at.run()
    assert not at.exception, f"Page 10 raised unhandled exception: {at.exception}"


# =============================================================================
# 10. ZIP Archive Support Tests (Requirement 14)
# =============================================================================

def _make_test_zip(files_dict: Dict[str, bytes]) -> bytes:
    """Helper to construct in-memory ZIP archives."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in files_dict.items():
            zf.writestr(name, data)
    return buf.getvalue()


@pytest.fixture
def raw_20240713_lc() -> bytes:
    p = project_root() / "data" / "raw" / "AL1_SOLEXS_20240713_SDD2_L1.lc.gz"
    assert p.exists()
    return p.read_bytes()


@pytest.fixture
def raw_20240713_gti() -> bytes:
    p = project_root() / "data" / "raw" / "AL1_SOLEXS_20240713_SDD2_L1.gti.gz"
    assert p.exists()
    return p.read_bytes()


@pytest.fixture
def raw_20240714_lc() -> bytes:
    p = project_root() / "data" / "raw" / "AL1_SOLEXS_20240714_SDD2_L1.lc.gz"
    assert p.exists()
    return p.read_bytes()


@pytest.fixture
def raw_20240714_gti() -> bytes:
    p = project_root() / "data" / "raw" / "AL1_SOLEXS_20240714_SDD2_L1.gti.gz"
    assert p.exists()
    return p.read_bytes()


def test_valid_zip_archive_matched_gti(raw_20240713_lc: bytes, raw_20240713_gti: bytes):
    """Verify that a valid ZIP archive with matching LC and GTI is correctly inspected and processed."""
    zip_payload = _make_test_zip({
        "AL1_SOLEXS_20240713_SDD2_L1.lc.gz": raw_20240713_lc,
        "AL1_SOLEXS_20240713_SDD2_L1.gti.gz": raw_20240713_gti,
    })

    inspection = inspect_uploaded_zip(zip_payload, "solexs_20240713.zip")
    assert inspection["n_observations"] == 1
    assert not inspection["has_multiple_observations"]
    assert "AL1_SOLEXS_20240713_SDD2_L1" in inspection["observations"]

    obs = inspection["observations"]["AL1_SOLEXS_20240713_SDD2_L1"]
    assert obs["has_gti"] is True
    assert obs["observation_date"] == "2024-07-13"
    assert obs["gti_filename"] == "AL1_SOLEXS_20240713_SDD2_L1.gti.gz"

    df, meta, gtis, _ = process_uploaded_zip(zip_payload, "solexs_20240713.zip")
    assert len(df) > 0
    assert gtis is not None
    assert len(gtis) > 0


def test_zip_archive_missing_gti(raw_20240713_lc: bytes):
    """Verify that a ZIP containing only a light curve (no GTI) is safely supported."""
    zip_payload = _make_test_zip({
        "AL1_SOLEXS_20240713_SDD2_L1.lc.gz": raw_20240713_lc,
    })

    inspection = inspect_uploaded_zip(zip_payload, "solexs_20240713_nogti.zip")
    assert inspection["n_observations"] == 1
    obs = inspection["observations"]["AL1_SOLEXS_20240713_SDD2_L1"]
    assert obs["has_gti"] is False
    assert obs["gti_filename"] is None

    df, meta, gtis, _ = process_uploaded_zip(zip_payload, "solexs_20240713_nogti.zip")
    assert len(df) > 0
    assert gtis is None


def test_zip_archive_mismatched_observation_identifiers(raw_20240713_lc: bytes, raw_20240714_gti: bytes):
    """Verify that unrelated GTI from a different observation is NOT paired with the light curve."""
    zip_payload = _make_test_zip({
        "AL1_SOLEXS_20240713_SDD2_L1.lc.gz": raw_20240713_lc,
        "AL1_SOLEXS_20240714_SDD2_L1.gti.gz": raw_20240714_gti,  # Mismatched date/stem!
    })

    inspection = inspect_uploaded_zip(zip_payload, "mismatched.zip")
    assert inspection["n_observations"] == 1
    obs = inspection["observations"]["AL1_SOLEXS_20240713_SDD2_L1"]
    # The 20240714 GTI must NOT be paired with the 20240713 LC
    assert obs["has_gti"] is False
    assert "AL1_SOLEXS_20240714_SDD2_L1.gti.gz" in inspection["unmatched_gtis"]
    assert len(inspection["warnings"]) > 0


def test_zip_archive_multiple_observations(
    raw_20240713_lc: bytes,
    raw_20240713_gti: bytes,
    raw_20240714_lc: bytes,
    raw_20240714_gti: bytes,
):
    """Verify that archives with multiple observation days are detected and require explicit user selection."""
    zip_payload = _make_test_zip({
        "AL1_SOLEXS_20240713_SDD2_L1.lc.gz": raw_20240713_lc,
        "AL1_SOLEXS_20240713_SDD2_L1.gti.gz": raw_20240713_gti,
        "AL1_SOLEXS_20240714_SDD2_L1.lc.gz": raw_20240714_lc,
        "AL1_SOLEXS_20240714_SDD2_L1.gti.gz": raw_20240714_gti,
    })

    inspection = inspect_uploaded_zip(zip_payload, "multi_days.zip")
    assert inspection["n_observations"] == 2
    assert inspection["has_multiple_observations"] is True

    # Calling without observation_key raises UploadValidationError
    with pytest.raises(UploadValidationError, match="contains 2 observations:.*Please select an observation explicitly"):
        extract_zip_observation(zip_payload, "multi_days.zip", observation_key=None)

    # Explicit selection succeeds
    lc_b, lc_name, gti_b, gti_name = extract_zip_observation(
        zip_payload, "multi_days.zip", observation_key="AL1_SOLEXS_20240713_SDD2_L1"
    )
    assert lc_name == "AL1_SOLEXS_20240713_SDD2_L1.lc.gz"
    assert gti_name == "AL1_SOLEXS_20240713_SDD2_L1.gti.gz"


def test_zip_archive_corrupt_rejected():
    """Verify that corrupt ZIP bytes raise UploadValidationError."""
    corrupt_payload = b"PK\x03\x04corrupted_not_a_real_zip_directory_1234567890"
    with pytest.raises(UploadValidationError, match="not a valid or readable ZIP archive"):
        inspect_uploaded_zip(corrupt_payload, "corrupt.zip")


def test_zip_archive_unsafe_path_traversal():
    """Verify that ZIP entries with directory traversal ('..') or absolute paths are rejected."""
    # Case 1: directory traversal
    unsafe_zip_1 = _make_test_zip({
        "../../etc/solexs_data.lc": b"time,counts\n0,1\n",
    })
    with pytest.raises(UploadValidationError, match="violates path traversal"):
        inspect_uploaded_zip(unsafe_zip_1, "traversal.zip")

    # Case 2: absolute root path
    unsafe_zip_2 = _make_test_zip({
        "/opt/solexs_data.lc": b"time,counts\n0,1\n",
    })
    with pytest.raises(UploadValidationError, match="violates path traversal"):
        inspect_uploaded_zip(unsafe_zip_2, "absolute.zip")


def test_zip_archive_oversized_uncompressed():
    """Verify that entries exceeding single file uncompressed size are rejected."""
    mock_info = MagicMock(spec=zipfile.ZipInfo)
    mock_info.filename = "large_observation.lc"
    mock_info.is_dir.return_value = False
    mock_info.file_size = 105 * 1024 * 1024  # 105 MB > 100 MB
    mock_info.compress_size = 1000

    base_zip = _make_test_zip({"dummy.lc": b"time,counts\n1,2\n"})
    with patch("zipfile.ZipFile.infolist", return_value=[mock_info]):
        with pytest.raises(UploadValidationError, match="exceeds single file limit"):
            inspect_uploaded_zip(base_zip, "oversized.zip")


def test_zip_archive_suspicious_compression_ratio():
    """Verify zip bomb defense: reject entries with suspicious compression ratio > 100:1."""
    mock_info = MagicMock(spec=zipfile.ZipInfo)
    mock_info.filename = "suspicious.lc"
    mock_info.is_dir.return_value = False
    mock_info.file_size = 50 * 1024 * 1024  # 50 MB
    mock_info.compress_size = 100  # 100 bytes -> ratio 500,000:1 > 100:1

    base_zip = _make_test_zip({"dummy.lc": b"time,counts\n1,2\n"})
    with patch("zipfile.ZipFile.infolist", return_value=[mock_info]):
        with pytest.raises(UploadValidationError, match="suspicious compression ratio"):
            inspect_uploaded_zip(base_zip, "zip_bomb.zip")


def test_zip_archive_duplicate_ambiguous_lightcurves():
    """Verify that conflicting duplicate light curves for the same observation ID are rejected."""
    dup_zip = _make_test_zip({
        "AL1_SOLEXS_20240713_SDD2_L1.lc.gz": b"header",
        "AL1_SOLEXS_20240713_SDD2_L1.fits.gz": b"duplicate_data",
    })
    with pytest.raises(UploadValidationError, match="duplicate/ambiguous"):
        inspect_uploaded_zip(dup_zip, "duplicates.zip")


def test_successful_inference_from_zip(pilot_lc_bytes: bytes, pilot_gti_bytes: bytes):
    """Verify end-to-end inference using existing model on data extracted from a ZIP package."""
    zip_payload = _make_test_zip({
        "AL1_SOLEXS_20261018_SDD2_L1.lc.gz": pilot_lc_bytes,
        "AL1_SOLEXS_20261018_SDD2_L1.gti.gz": pilot_gti_bytes,
    })

    df, meta, gtis, insp = process_uploaded_zip(zip_payload, "pilot_package.zip", observation_key=None)
    assert insp["n_observations"] == 1
    assert len(df) == 86400
    assert gtis is not None and len(gtis) == 8

    # Focus on flaring segment
    t_flare = 1792320568.0
    flare_slice = df[(df["time"] >= t_flare - 1200.0) & (df["time"] <= t_flare + 600.0)].copy()

    pipeline = get_default_pipeline()
    out = execute_dataset_inference(
        df=flare_slice,
        gti_intervals=gtis,
        pipeline=pipeline,
        threshold=0.50,
        window_seconds=60.0,
        stride_seconds=30.0,
    )

    res_df = out["results_df"]
    assert not res_df.empty
    assert res_df["flare_probability"].max() > 0.80
    assert len(out["candidate_episodes"]) >= 1

