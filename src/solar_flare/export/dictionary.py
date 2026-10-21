"""Automated Data Dictionary Generator for SOLARIS-A1 Dataset Exports (Stage 9).

Compiles standard markdown documentation describing all feature variables, label semantics,
metadata provenance, and critical warnings against data leakage for exported datasets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from solar_flare.features.registry import DEFAULT_REGISTRY


def generate_data_dictionary(
    task: str,
    feature_names: Optional[List[str]] = None,
    config_params: Optional[Dict[str, Any]] = None,
    policy_version: str = "1.0",
) -> str:
    """Generate a comprehensive data dictionary markdown document for a dataset export.
    
    Parameters
    ----------
    task : str
        "detection" (Task A) or "prediction" (Task B).
    feature_names : Optional[List[str]]
        List of feature column names present in X_features.csv.
    config_params : Optional[dict]
        Snapshot of configuration parameters used.
    policy_version : str
        Policy version string.
        
    Returns
    -------
    str
        Complete markdown string.
    """
    task_clean = task.strip().lower()
    is_detection = "det" in task_clean
    task_name = "Task A: Solar Flare Detection" if is_detection else "Task B: Pre-Flare Activity Forecasting"
    target_col = "label_detection" if is_detection else "label_prediction"

    reg = DEFAULT_REGISTRY
    if feature_names is None:
        feature_names = [f.name for f in reg.list_features()]

    lines: List[str] = [
        f"# DATA DICTIONARY — SOLARIS-A1 DATASET EXPORT",
        f"",
        f"**Task:** `{task_name}`  ",
        f"**Policy Version:** `{policy_version}`  ",
        f"**Format:** Tabular CSV files (`X_features.csv`, `y_labels.csv`, `metadata.csv`, `exclusions.csv`)  ",
        f"",
        f"---",
        f"",
        f"## 1. CRITICAL NOTICE: AVOID ROW-LEVEL RANDOM SPLITTING",
        f"",
        f"> [!WARNING]",
        f"> **DO NOT USE RANDOM TRAIN/TEST SPLITS (e.g. `train_test_split(shuffle=True)`).**  ",
        f"> Observation windows are generated with sliding stride $S < W$ (default $S=10\\text{{ s}}$, $W=60\\text{{ s}}$).  ",
        f"> Adjacent rows share up to $83.3\\%$ of raw observational samples. Random row-level splitting causes  ",
        f"> catastrophic data leakage between train and test partitions, resulting in artificially inflated  ",
        f"> validation performance that fails completely on unseen time intervals.  ",
        f"> **Partitioning MUST strictly use contiguous block-based temporal splits or segment-level grouping (Stage 10).**",
        f"",
        f"---",
        f"",
        f"## 2. Target Variable Semantics (`y_labels.csv`)",
        f"",
        f"| Column Name | Data Type | Nullable | Allowed Values | Description |",
        f"|-------------|:---------:|:--------:|:--------------:|-------------|",
        f"| `window_id` | `string` | No | Alphanumeric | Unique window identifier (`<segment_id>_win_<index>`) |",
        f"| `label` | `Int8` | **Yes** | `1`, `0`, `<NA>` | Binary target label (nullable) |",
        f"| `label_reason` | `string` | No | Text code | Auditable decision reason code for assignment or exclusion |",
        f"",
        f"### Label Definitions:",
    ]

    if is_detection:
        lines.extend([
            f"- **`1` (Verified Positive):** A verified solar flare event overlaps the window by at least the approved tolerance and overlap fraction threshold.",
            f"- **`0` (Verified Negative):** The window is completely outside every verified flare event and its surrounding embargo buffer, AND has $\\ge 80\\%$ observation coverage.",
            f"- **`<NA>` (Excluded / Ambiguous):** Windows with partial overlap ($< \\text{{threshold}}$), within event embargo buffers, or with $< 80\\%$ sample coverage. Excluded intervals are strictly preserved in `exclusions.csv` and MUST NEVER be filled with `0`.",
        ])
    else:
        lines.extend([
            f"- **`1` (Verified Positive Onset):** A verified solar flare onset occurs within the future forecast horizon $(t_0, t_0 + H]$ after window reference time $t_0$.",
            f"- **`0` (Verified Clean Horizon):** No verified flare onset occurs within $(t_0 - \\text{{embargo}}, t_0 + H]$, and the observation segment covers $\\ge 80\\%$ of the forecast horizon.",
            f"- **`<NA>` (Excluded / Right-Censored):** Windows where a flare is active at $t_0$, an onset occurred during recent embargo, or the observation segment ends before horizon $H$ expires. MUST NEVER be treated as 0.",
        ])

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 3. Feature Variables (`X_features.csv`)",
        f"",
        f"All features in `X_features.csv` are strictly causal, using only observational samples with timestamp $t \\le w_{{\\text{{end}}}} = t_0$.",
        f"The table contains **NO identifier columns**, **NO target labels**, and **NO timestamp fields**.",
        f"",
        f"| Feature Name | Units | Definition | Edge Cases & Missing Value Reasons |",
        f"|--------------|:-----:|------------|-------------------------------------|",
    ])

    for feat_name in feature_names:
        feat = reg.get(feat_name)
        if feat:
            units = feat.units or "unitless"
            formula = feat.formula_text.replace("|", "\\|")
            leakage = feat.leakage_note.replace("|", "\\|")
            lines.append(f"| `{feat.name}` | `{units}` | {formula} | {leakage} |")
        else:
            lines.append(f"| `{feat_name}` | `arbitrary` | Engineered summary feature | NaN if insufficient samples |")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 4. Metadata Variables (`metadata.csv`)",
        f"",
        f"| Column Name | Type | Description |",
        f"|-------------|:----:|-------------|",
        f"| `window_id` | `string` | Primary key joining `X_features.csv` and `y_labels.csv` |",
        f"| `file_stem` | `string` | Source Level-1 FITS file stem |",
        f"| `segment_id` | `string` | Continuous segment identifier |",
        f"| `window_start` | `float` | Window start time in Mission Elapsed Seconds |",
        f"| `window_end` | `float` | Window reference time $t_0$ in Mission Elapsed Seconds |",
        f"| `coverage_fraction` | `float` | Ratio of observed samples to nominal expected samples |",
        f"| `quality_flag` | `string` | Window quality assessment flag (`OK`, `LOW_COVERAGE`) |",
        f"| `event_id` | `string` | Matched ground-truth event ID (if applicable) |",
        f"| `next_onset_time` | `float` | Next verified flare onset timestamp (if applicable) |",
        f"",
        f"---",
        f"",
        f"## 5. Audit & Exclusions (`exclusions.csv`)",
        f"",
        f"Contains all window instances where `label` is `<NA>`. Each row records the exact exclusion reason",
        f"(e.g. `EMBARGO_EXCLUDED`, `PARTIAL_OVERLAP_EXCLUDED`, `INSUFFICIENT_HORIZON_COVERAGE`).",
        f"Exclusion preserves scientific integrity: unverified intervals are never coerced into negative examples.",
        f"",
    ])

    return "\n".join(lines)
