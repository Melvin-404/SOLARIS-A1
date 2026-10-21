"""Real-data reproducibility check for SOLARIS-A1 development pipeline (Stage 14).

Executes Stages 4, 5, 7, 8, 9 in development mode into a temporary output tree,
and compares deterministic artifacts against the existing outputs.
Reports matching artifacts, differing artifacts, and explains causes.
"""

from __future__ import annotations

import filecmp
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Tuple

# Ensure src/ is on python path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from solar_flare.paths import project_root


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_real_pipeline_in_temp(tmp_dir: Path) -> Dict[str, Any]:
    """Execute stages 4, 5, 7, 8, 9 development runs into tmp_dir."""
    py_exec = sys.executable
    env_root = _ROOT

    # 1. Stage 4: Quality Assessment
    q_out = tmp_dir / "results" / "quality"
    subprocess.run([
        py_exec, str(env_root / "scripts" / "run_quality.py"),
        "--raw-dir", "data/raw",
        "--manifest", "data/manifests/manifest.csv",
        "--out-dir", str(q_out),
    ], check=True, cwd=str(env_root), capture_output=True)

    # 2. Stage 5: Exploratory Data Analysis
    eda_out = tmp_dir / "results" / "eda"
    subprocess.run([
        py_exec, str(env_root / "scripts" / "run_eda.py"),
        "--raw-dir", "data/raw",
        "--out-dir", str(eda_out),
    ], check=True, cwd=str(env_root), capture_output=True)

    # 3. Stage 7: Preprocessing & Segmentation
    prep_out = tmp_dir / "results" / "preprocessing"
    seg_out = tmp_dir / "data" / "processed" / "segments"
    subprocess.run([
        py_exec, str(env_root / "scripts" / "run_preprocessing.py"),
        "--stem", "all",
        "--raw-dir", "data/raw",
        "--out-dir", str(prep_out),
        "--segments-dir", str(seg_out),
    ], check=True, cwd=str(env_root), capture_output=True)

    # 4. Stage 8: Features
    feat_out = tmp_dir / "data" / "processed" / "features"
    res_feat_out = tmp_dir / "results" / "features"
    subprocess.run([
        py_exec, str(env_root / "scripts" / "build_features.py"),
        "--stem", "all",
        "--segments-dir", str(seg_out),
        "--features-dir", str(feat_out),
        "--results-dir", str(res_feat_out),
    ], check=True, cwd=str(env_root), capture_output=True)

    # 5. Stage 9: Export (Development mode - expected to write BLOCKED report)
    exp_out = tmp_dir / "results" / "exports"
    exp_out.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        py_exec, str(env_root / "scripts" / "export_dataset.py"),
        "--task", "detection",
        "--features-dir", str(feat_out),
    ], cwd=str(env_root), capture_output=True)  # Returns code 1 because G3 is blocked (expected)

    # Return key generated artifact files
    stem = "AL1_SOLEXS_20261018_SDD2_L1"
    return {
        "quality_summary_csv": q_out / "summary.csv",
        "eda_bursts_csv": eda_out / f"{stem}.lc" / "candidate_bursts.csv",
        "eda_variability_csv": eda_out / f"{stem}.lc" / "variability_summary.csv",
        "prep_summary_csv": prep_out / "summary.csv",
        "segment_001_csv": seg_out / stem / f"{stem}_seg_001.csv",
        "segment_002_csv": seg_out / stem / f"{stem}_seg_002.csv",
        "segment_003_csv": seg_out / stem / f"{stem}_seg_003.csv",
        "segment_004_csv": seg_out / stem / f"{stem}_seg_004.csv",
        "window_index_csv": feat_out / stem / "window_index.csv",
        "window_features_csv": feat_out / stem / "window_features.csv",
    }


def compare_with_original(repro_artifacts: Dict[str, Path]) -> Dict[str, Any]:
    """Compare generated artifacts against baseline artifacts on disk."""
    stem = "AL1_SOLEXS_20261018_SDD2_L1"
    baseline_map = {
        "quality_summary_csv": _ROOT / "results" / "quality" / "summary.csv",
        "eda_bursts_csv": _ROOT / "results" / "eda" / f"{stem}.lc" / "candidate_bursts.csv",
        "eda_variability_csv": _ROOT / "results" / "eda" / f"{stem}.lc" / "variability_summary.csv",
        "prep_summary_csv": _ROOT / "results" / "preprocessing" / "summary.csv",
        "segment_001_csv": _ROOT / "data" / "processed" / "segments" / stem / f"{stem}_seg_001.csv",
        "segment_002_csv": _ROOT / "data" / "processed" / "segments" / stem / f"{stem}_seg_002.csv",
        "segment_003_csv": _ROOT / "data" / "processed" / "segments" / stem / f"{stem}_seg_003.csv",
        "segment_004_csv": _ROOT / "data" / "processed" / "segments" / stem / f"{stem}_seg_004.csv",
        "window_index_csv": _ROOT / "data" / "processed" / "features" / stem / "window_index.csv",
        "window_features_csv": _ROOT / "data" / "processed" / "features" / stem / "window_features.csv",
    }

    matches = []
    differences = []

    for name, repro_path in repro_artifacts.items():
        orig_path = baseline_map.get(name)
        if not orig_path or not orig_path.is_file():
            differences.append({
                "artifact": name,
                "status": "MISSING_ORIGINAL",
                "path": str(orig_path),
            })
            continue

        if not repro_path.is_file():
            differences.append({
                "artifact": name,
                "status": "MISSING_REPRODUCED",
                "path": str(repro_path),
            })
            continue

        hash_orig = compute_sha256(orig_path)
        hash_repro = compute_sha256(repro_path)

        if hash_orig == hash_repro:
            matches.append({
                "artifact": name,
                "path": str(orig_path.relative_to(_ROOT)),
                "sha256": hash_orig,
            })
        else:
            differences.append({
                "artifact": name,
                "path": str(orig_path.relative_to(_ROOT)),
                "hash_orig": hash_orig,
                "hash_repro": hash_repro,
                "reason": "Divergence in output data bytes",
            })

    return {
        "matches": matches,
        "differences": differences,
        "n_matches": len(matches),
        "n_differences": len(differences),
    }


def main() -> int:
    print("=== SOLARIS-A1 Real-Data Reproducibility Check (Stage 14) ===\n")
    with tempfile.TemporaryDirectory(prefix="solaris_repro_") as tmp_str:
        tmp_dir = Path(tmp_str)
        print(f"Executing development pipeline in isolated temporary directory:\n  {tmp_dir}\n")

        repro_artifacts = run_real_pipeline_in_temp(tmp_dir)
        results = compare_with_original(repro_artifacts)

        print(f"Deterministic tabular artifacts evaluated: {results['n_matches'] + results['n_differences']}")
        print(f"Bit-for-bit identical matches: {results['n_matches']}")
        for m in results["matches"]:
            print(f"  [OK] {m['artifact']:20s} ({m['path']}) -> {m['sha256'][:16]}...")

        if results["differences"]:
            print(f"\nDivergences detected: {results['n_differences']}")
            for d in results["differences"]:
                print(f"  [DIFF] {d['artifact']}: {d.get('reason')} (orig={d.get('hash_orig', '')[:8]}... vs repro={d.get('hash_repro', '')[:8]}...)")
            return 1
        else:
            print("\n[SUCCESS] 100% of deterministic tabular artifacts match bit-for-bit!")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
