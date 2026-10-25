"""SOLARIS-A1 Expanded Dataset Builder (2024-2026).

Builds the unified expanded dataset combining:
- 13 existing observations (July 2024 + Oct 18, 2026)
- 218 new observations from Downloads/Solexis dataset

Adheres strictly to:
- 60s sliding window, 10s stride (Decisions D-05, D-06)
- Gate G3 approved NOAA SWPC flare events (tolerance=30s, embargo=300s)
- 19 standardized causal features (Registry Stage 8)
- Zero data leakage, strict provenance preservation
"""

import os
import zipfile
import gzip
import io
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from astropy.io import fits
import numpy as np
import pandas as pd
import yaml

from solar_flare.features.registry import compute_features
from solar_flare.features.baseline import causal_baseline

REPO_ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS_DIR = Path(os.environ.get("SOLEXS_DATASET_DIR", Path.home() / "Downloads" / "Solexis dataset"))
AUDIT_SUMMARY_CSV = REPO_ROOT / "scratch" / "audit_results" / "downloads_audit_summary.csv"
NEW_EVENTS_CSV = REPO_ROOT / "scratch" / "audit_results" / "matched_approved_events_new_dataset.csv"
EXISTING_EVENTS_CSV = REPO_ROOT / "data" / "manifests" / "event_records_approved.csv"
EXISTING_JULY_DIR = REPO_ROOT / "data" / "processed" / "datasets" / "detection" / "exp_det_july2024"
EXISTING_PILOT_DIR = REPO_ROOT / "data" / "processed" / "datasets" / "detection" / "exp_det_7e151632ab"

DEST_DATASET_DIR = REPO_ROOT / "data" / "processed" / "datasets" / "detection" / "exp_det_expanded_2024_2026"
DEST_DATASET_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = [
    "baseline_value", "p05", "p25", "p75", "p95", "coverage_fraction",
    "iqr", "max", "max_abs_first_difference", "mean", "mean_abs_first_difference",
    "median", "min", "n_observed_samples", "peak_to_baseline_ratio",
    "robust_variability", "rolling_trend", "std", "temporal_slope"
]

def process_single_observation(zip_path: str, events_for_day: list) -> dict:
    """Extract sliding windows, features, and labels for a single day archive."""
    zpath = Path(zip_path)
    stem = zpath.stem.replace(".zip", "")
    
    with zipfile.ZipFile(zpath, "r") as z:
        lc_members = [m for m in z.namelist() if "SDD2" in m and m.endswith(".lc.gz")]
        gti_members = [m for m in z.namelist() if "SDD2" in m and m.endswith(".gti.gz")]
        if not lc_members or not gti_members:
            return {"stem": stem, "status": "ERROR_MISSING_MEMBERS"}
            
        with fits.open(io.BytesIO(gzip.decompress(z.read(lc_members[0])))) as hdul:
            times = np.array(hdul[1].data["TIME"], dtype=np.float64)
            counts = np.array(hdul[1].data["COUNTS"], dtype=np.float64)
            
        with fits.open(io.BytesIO(gzip.decompress(z.read(gti_members[0])))) as hdul:
            gdata = hdul[1].data
            gti_starts = np.array(gdata["START"], dtype=np.float64)
            gti_stops = np.array(gdata["STOP"], dtype=np.float64)

    # Clean non-finite counts
    finite_mask = np.isfinite(counts)
    if not np.all(finite_mask):
        counts = np.where(finite_mask, counts, 0.0)

    # Segment lightcurve into continuous GTI intervals
    windows_meta = []
    windows_features = []
    windows_labels = []

    win_counter = 0

    for seg_idx, (g_start, g_stop) in enumerate(zip(gti_starts, gti_stops), 1):
        seg_dur = g_stop - g_start
        if seg_dur < 60.0:
            continue
            
        seg_id = f"{stem}_seg_{seg_idx:03d}"
        
        # Candidate window start times within GTI
        w_starts = np.arange(g_start, g_stop - 60.0 + 1e-6, 10.0)
        
        for w_s in w_starts:
            w_e = w_s + 60.0
            win_counter += 1
            win_id = f"{seg_id}_win_{win_counter:05d}"
            
            # Slice window indices
            idx_s = int(np.searchsorted(times, w_s, side="left"))
            idx_e = int(np.searchsorted(times, w_e, side="right"))
            
            w_times = times[idx_s:idx_e]
            w_vals = counts[idx_s:idx_e]
            n_obs = len(w_vals)
            cov_frac = n_obs / 60.0
            
            # Causal baseline (preceding 600s within GTI segment)
            b_s = max(g_start, w_s - 600.0)
            if w_s - b_s >= 60.0:
                b_idx_s = int(np.searchsorted(times, b_s, side="left"))
                b_vals = counts[b_idx_s:idx_s]
                b_val = float(np.median(b_vals)) if len(b_vals) > 0 else np.nan
            else:
                b_val = np.nan
                
            # Compute 19 features
            feat_dict, _ = compute_features(
                w_vals, w_times, baseline_value=b_val, enabled_features=FEATURE_COLS
            )
            # Ensure baseline_value is in feature dict
            feat_dict["baseline_value"] = b_val
            
            # Label assignment logic per Gate G3 policy
            matched_event_id = None
            max_ov = 0.0
            is_embargoed = False
            
            for ev in events_for_day:
                ev_id = ev["event_id"]
                ev_s = ev["onset_time"]
                ev_e = ev["end_time"]
                
                # Check direct interval overlap
                ov = max(0.0, min(w_e, ev_e) - max(w_s, ev_s))
                if ov > max_ov:
                    max_ov = ov
                    matched_event_id = ev_id
                    
                # Check embargo buffer (300s before onset or after end)
                if (ev_s - 300.0 <= w_e <= ev_s) or (ev_e <= w_s <= ev_e + 300.0):
                    is_embargoed = True

            if cov_frac < 0.80:
                label = np.nan
                reason = "LOW_COVERAGE_EXCLUDED"
            elif max_ov >= 30.0:
                label = 1
                reason = "MATCHED_EVENT"
            elif max_ov > 0.0:
                label = np.nan
                reason = "PARTIAL_OVERLAP_EXCLUDED"
            elif is_embargoed:
                label = np.nan
                reason = "EMBARGO_EXCLUDED"
            else:
                label = 0
                reason = "VERIFIED_QUIET_BACKGROUND"

            windows_meta.append({
                "window_id": win_id,
                "segment_id": seg_id,
                "file_stem": stem,
                "window_start": w_s,
                "window_end": w_e,
                "n_expected_samples": 60,
                "n_observed_samples": n_obs,
                "coverage_fraction": round(cov_frac, 4),
                "start_index": idx_s,
                "end_index": idx_e,
                "min_time_used": float(w_times[0]) if n_obs > 0 else w_s,
                "max_time_used": float(w_times[-1]) if n_obs > 0 else w_e,
                "quality_flag": "OK" if cov_frac >= 0.80 else "LOW_COVERAGE",
                "include_flag": cov_frac >= 0.80,
                "event_id": matched_event_id if label == 1 else np.nan,
            })
            
            windows_features.append([feat_dict.get(c, np.nan) for c in FEATURE_COLS])
            
            windows_labels.append({
                "window_id": win_id,
                "label": label,
                "label_reason": reason,
            })

    return {
        "stem": stem,
        "status": "OK",
        "n_windows": len(windows_meta),
        "meta": windows_meta,
        "features": windows_features,
        "labels": windows_labels,
    }

def main():
    print("=" * 70)
    print("SOLARIS-A1: BUILDING EXPANDED DATASET (2024–2026)")
    print("=" * 70)

    # 1. Load approved events
    df_new_events = pd.read_csv(NEW_EVENTS_CSV)
    df_old_events = pd.read_csv(EXISTING_EVENTS_CSV)
    
    # Standardize and merge approved events catalog
    common_cols = [
        "event_id", "source_id", "onset_time", "end_time", "time_system",
        "classification", "classification_method", "peak_time", "uncertainty_seconds", "notes"
    ]
    df_all_events = pd.concat([
        df_old_events[common_cols],
        df_new_events[common_cols]
    ], ignore_index=True)
    df_all_events = df_all_events.drop_duplicates(subset=["onset_time", "end_time"]).reset_index(drop=True)
    
    combined_events_path = REPO_ROOT / "data" / "manifests" / "event_records_approved_expanded_2024_2026.csv"
    df_all_events.to_csv(combined_events_path, index=False)
    print(f"Merged approved events catalog: {len(df_all_events)} events -> {combined_events_path.name}")

    # Build event index by date string
    events_by_date = {}
    for _, ev in df_all_events.iterrows():
        # Derive date YYYYMMDD from onset_time
        dt = pd.to_datetime(ev["onset_time"], unit="s", utc=True)
        dstr = dt.strftime("%Y%m%d")
        events_by_date.setdefault(dstr, []).append(ev.to_dict())

    # 2. Load existing 13 observation days (July 2024 + Oct 18, 2026)
    print("\nLoading precomputed historical baseline windows (July 2024 & Oct 18, 2026)...")
    X_july = pd.read_csv(EXISTING_JULY_DIR / "X_features.csv")
    y_july = pd.read_csv(EXISTING_JULY_DIR / "y_labels.csv")
    m_july = pd.read_csv(EXISTING_JULY_DIR / "metadata.csv")

    X_pilot = pd.read_csv(EXISTING_PILOT_DIR / "X_features.csv")
    y_pilot = pd.read_csv(EXISTING_PILOT_DIR / "y_labels.csv")
    m_pilot = pd.read_csv(EXISTING_PILOT_DIR / "metadata.csv")

    # Align columns
    for c in FEATURE_COLS:
        if c not in X_july.columns:
            X_july[c] = np.nan
        if c not in X_pilot.columns:
            X_pilot[c] = np.nan
            
    X_hist = pd.concat([X_july[FEATURE_COLS], X_pilot[FEATURE_COLS]], ignore_index=True)
    y_hist = pd.concat([y_july, y_pilot], ignore_index=True)
    m_hist = pd.concat([m_july, m_pilot], ignore_index=True)
    print(f"Loaded {len(X_hist)} historical baseline windows.")

    # 3. Process 218 new observation archives
    audit_df = pd.read_csv(AUDIT_SUMMARY_CSV)
    new_obs = audit_df[audit_df["status"] == "GENUINE_NEW"].copy()
    print(f"\nProcessing {len(new_obs)} new observation archives from {DOWNLOADS_DIR}...")

    all_meta = [m_hist]
    all_features = [X_hist]
    all_labels = [y_hist]

    start_time = time.time()
    n_processed = 0

    for idx, row in new_obs.iterrows():
        zname = row["zip_filename"]
        dstr = str(row["obs_date"])
        zpath = DOWNLOADS_DIR / zname
        
        evs = events_by_date.get(dstr, [])
        res = process_single_observation(str(zpath), evs)
        
        if res["status"] == "OK" and res["n_windows"] > 0:
            df_m = pd.DataFrame(res["meta"])
            df_x = pd.DataFrame(res["features"], columns=FEATURE_COLS)
            df_y = pd.DataFrame(res["labels"])
            
            all_meta.append(df_m)
            all_features.append(df_x)
            all_labels.append(df_y)
            
        n_processed += 1
        if n_processed % 25 == 0 or n_processed == len(new_obs):
            elapsed = time.time() - start_time
            print(f"  Processed {n_processed}/{len(new_obs)} observations ({elapsed:.1f}s elapsed)...")

    # 4. Concatenate unified dataset
    print("\nConcatenating unified expanded dataset tables...")
    df_X_final = pd.concat(all_features, ignore_index=True)
    df_y_final = pd.concat(all_labels, ignore_index=True)
    df_m_final = pd.concat(all_meta, ignore_index=True)

    print(f"Total unified windows: {len(df_X_final):,}")

    # Deduplicate windows by window_id if any duplicate exists
    dup_mask = df_m_final.duplicated(subset=["window_id"])
    if dup_mask.any():
        print(f"Removing {dup_mask.sum()} duplicate window rows...")
        df_X_final = df_X_final[~dup_mask].reset_index(drop=True)
        df_y_final = df_y_final[~dup_mask].reset_index(drop=True)
        df_m_final = df_m_final[~dup_mask].reset_index(drop=True)

    # 5. Export dataset artifacts
    print(f"Exporting expanded dataset to {DEST_DATASET_DIR}...")
    df_X_final.to_csv(DEST_DATASET_DIR / "X_features.csv", index=False)
    df_y_final.to_csv(DEST_DATASET_DIR / "y_labels.csv", index=False)
    df_m_final.to_csv(DEST_DATASET_DIR / "metadata.csv", index=False)

    # Exclusions table (where label is NA)
    exclusions = df_y_final[df_y_final["label"].isna()].copy()
    exclusions.to_csv(DEST_DATASET_DIR / "exclusions.csv", index=False)

    # Summary counts
    label_counts = df_y_final["label"].value_counts(dropna=False).to_dict()
    positives = int(label_counts.get(1, label_counts.get(1.0, 0)))
    negatives = int(label_counts.get(0, label_counts.get(0.0, 0)))
    excluded = int(df_y_final["label"].isna().sum())
    usable = positives + negatives

    summary = {
        "dataset_id": "exp_det_expanded_2024_2026",
        "total_windows": len(df_y_final),
        "usable_windows": usable,
        "positive_windows": positives,
        "negative_windows": negatives,
        "excluded_windows": excluded,
        "prevalence": round(positives / usable, 6) if usable > 0 else 0.0,
        "exclusion_reasons": df_y_final["label_reason"].value_counts().to_dict(),
        "total_observation_stems": int(df_m_final["file_stem"].nunique()),
        "time_min_utc": str(pd.to_datetime(df_m_final["window_start"].min(), unit="s", utc=True)),
        "time_max_utc": str(pd.to_datetime(df_m_final["window_end"].max(), unit="s", utc=True)),
    }

    with open(DEST_DATASET_DIR / "summary_counts.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 50)
    print("EXPANDED DATASET GENERATION COMPLETE")
    print("=" * 50)
    print(f"Total windows: {summary['total_windows']:,}")
    print(f"Usable windows: {summary['usable_windows']:,} ({summary['usable_windows']/summary['total_windows']*100:.1f}%)")
    print(f"Positive flare windows (label=1): {summary['positive_windows']:,} ({summary['prevalence']*100:.2f}%)")
    print(f"Verified quiet background (label=0): {summary['negative_windows']:,}")
    print(f"Excluded boundary/gap/embargo windows: {summary['excluded_windows']:,}")
    print(f"Unique observation stems: {summary['total_observation_stems']}")
    print(f"Temporal coverage: {summary['time_min_utc']} to {summary['time_max_utc']}")

if __name__ == "__main__":
    main()
