"""Scientific evaluation report generation engine for SOLARIS-A1 (Stage 11).

Generates transparent, auditable markdown, JSON, CSV, and dashboard contract files.
Mandatory scientific governance constraints:
1. Strict Single-Shot Rule: Refuses to write if an evaluation/ directory already exists.
2. Cryptographic Integrity: Refuses to write unless lock verification has succeeded.
3. Prevalence Transparency: Prevalence is reported in every table alongside metrics.
4. Mandatory Researcher Disclaimer:
   "This report contains computed values only. Interpretation is the responsibility of the human researcher."
5. Mandatory Prediction Baseline Disclaimer:
   "Forecasting skill requires comparison with the climatological and persistence baselines reported here. This report alone does not establish skill."
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from solar_flare.evaluation.window_metrics import WindowMetricsReport
from solar_flare.evaluation.event_metrics import EventMetricsReport
from solar_flare.evaluation.false_alarms import FalseAlarmReport
from solar_flare.evaluation.calibration import CalibrationReport
from solar_flare.evaluation.uncertainty import BootstrapUncertaintyReport


MANDATORY_DISCLAIMER = (
    "This report contains computed values only. "
    "Interpretation is the responsibility of the human researcher."
)

PREDICTION_SKILL_DISCLAIMER = (
    "Forecasting skill requires comparison with the climatological and "
    "persistence baselines reported here. This report alone does not establish skill."
)


def write_dashboard_contract(eval_dir: Path) -> Path:
    """Generate evaluation/dashboard_contract.json for Stage 12 and 13 consumption."""
    contract = {
        "contract_version": "1.0",
        "stage": "STAGE_11_SCIENTIFIC_EVALUATION",
        "description": "Standardized schema contract for Stage 12 (interactive analysis) and Stage 13 (dashboard).",
        "files": {
            "metrics_csv": {
                "relative_path": "evaluation/metrics.csv",
                "format": "csv",
                "required_columns": [
                    "model_name",
                    "model_type",
                    "n_evaluated",
                    "prevalence",
                    "precision",
                    "recall",
                    "f1",
                    "pr_auc",
                    "roc_auc",
                    "true_positives",
                    "false_positives",
                    "true_negatives",
                    "false_negatives",
                ],
            },
            "test_predictions": {
                "relative_path": "evaluation/test_predictions.csv",
                "format": "csv",
                "required_columns": [
                    "window_id",
                    "model_name",
                    "label",
                    "score",
                    "pred",
                ],
            },
            "evaluation_report_json": {
                "relative_path": "evaluation/evaluation_report.json",
                "format": "json",
                "required_sections": [
                    "metadata",
                    "window_metrics",
                    "event_metrics",
                    "false_alarms",
                    "calibration",
                    "uncertainty",
                ],
            },
            "evaluation_report_md": {
                "relative_path": "evaluation/evaluation_report.md",
                "format": "markdown",
            },
        },
    }
    out_file = eval_dir / "dashboard_contract.json"
    out_file.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return out_file


def build_evaluation_report(
    exp_dir: Union[Path, str],
    protocol_id: str,
    dataset_status: str,
    lock_verified: bool,
    task: str,
    window_reports: Dict[str, WindowMetricsReport],
    event_report: Optional[EventMetricsReport] = None,
    false_alarm_report: Optional[FalseAlarmReport] = None,
    calibration_reports: Optional[Dict[str, CalibrationReport]] = None,
    uncertainty_report: Optional[BootstrapUncertaintyReport] = None,
    split_report: Optional[Dict[str, Any]] = None,
    force_overwrite: bool = False,
) -> Path:
    """Build and write comprehensive evaluation reports, metrics CSV, and dashboard contract.

    Parameters
    ----------
    exp_dir : Path or str
        Experiment output directory containing sealed/ and models/.
    protocol_id : str
        Approved protocol identifier.
    dataset_status : str
        Dataset status ("PILOT" or "APPROVED-main").
    lock_verified : bool
        Whether cryptographic lock verification succeeded.
    task : str
        Evaluation task: "detection" or "prediction".
    window_reports : dict of WindowMetricsReport
        Window metrics per evaluated model and baseline.
    event_report : EventMetricsReport, optional
        Macro event detection report.
    false_alarm_report : FalseAlarmReport, optional
        False alarm and missed event report.
    calibration_reports : dict of CalibrationReport, optional
        Calibration reports per model.
    uncertainty_report : BootstrapUncertaintyReport, optional
        Block bootstrap confidence intervals report.
    split_report : dict, optional
        Split metadata.
    force_overwrite : bool, default=False
        Strict safety: single-shot evaluation forbids overwrite.

    Returns
    -------
    Path
        Path to evaluation directory.

    Raises
    ------
    RuntimeError
        If lock verification failed.
    FileExistsError
        If evaluation directory already exists and force_overwrite is False.
    """
    if not lock_verified:
        raise RuntimeError("CANNOT WRITE EVALUATION REPORT: Test set lock verification failed!")

    e_dir = Path(exp_dir) / "evaluation"
    if e_dir.exists() and not force_overwrite:
        raise FileExistsError(
            f"SINGLE-SHOT EVALUATION VIOLATION: Evaluation directory '{e_dir}' already exists! "
            "Re-evaluating the test set is strictly prohibited under the frozen protocol."
        )

    e_dir.mkdir(parents=True, exist_ok=True)
    ts_now = datetime.now(timezone.utc).isoformat()

    # 1. Build metrics.csv
    csv_rows = []
    for model_name, rep in window_reports.items():
        m_type = "baseline" if "baseline" in model_name.lower() else "learned_model"
        csv_rows.append({
            "model_name": model_name,
            "model_type": m_type,
            "n_total": rep.n_total,
            "n_evaluated": rep.n_evaluated,
            "n_excluded_na": rep.n_excluded_na,
            "prevalence": rep.prevalence,
            "precision": rep.precision,
            "recall": rep.recall,
            "f1": rep.f1,
            "pr_auc": rep.pr_auc if rep.pr_auc is not None else float("nan"),
            "roc_auc": rep.roc_auc if rep.roc_auc is not None else float("nan"),
            "true_positives": rep.true_positives,
            "false_positives": rep.false_positives,
            "true_negatives": rep.true_negatives,
            "false_negatives": rep.false_negatives,
            "dataset_status": dataset_status,
        })

    metrics_df = pd.DataFrame(csv_rows)
    metrics_csv_path = e_dir / "metrics.csv"
    metrics_df.to_csv(metrics_csv_path, index=False)

    # 2. Build evaluation_report.json
    full_json = {
        "metadata": {
            "protocol_id": protocol_id,
            "dataset_status": dataset_status,
            "lock_hash_verified": lock_verified,
            "evaluation_timestamp_utc": ts_now,
            "task": task,
            "mandatory_statement": MANDATORY_DISCLAIMER,
        },
        "window_metrics": {name: rep.to_dict() for name, rep in window_reports.items()},
        "event_metrics": event_report.to_dict() if event_report else None,
        "false_alarms": false_alarm_report.to_dict() if false_alarm_report else None,
        "calibration": {
            name: rep.to_dict() for name, rep in (calibration_reports or {}).items()
        },
        "uncertainty": uncertainty_report.to_dict() if uncertainty_report else None,
        "split_summary": split_report,
    }
    if task == "prediction":
        full_json["metadata"]["prediction_skill_disclaimer"] = PREDICTION_SKILL_DISCLAIMER

    report_json_path = e_dir / "evaluation_report.json"
    report_json_path.write_text(json.dumps(full_json, indent=2), encoding="utf-8")

    # 3. Build evaluation_report.md
    md_lines = [
        f"# SOLARIS-A1 Scientific Evaluation Report (Stage 11)",
        f"",
        f"**Dataset Status:** `{dataset_status}`  ",
        f"**Protocol ID:** `{protocol_id}`  ",
        f"**Test Set Lock Hash Verified:** `{'PASSED' if lock_verified else 'FAILED'}`  ",
        f"**Evaluation Timestamp (UTC):** `{ts_now}`  ",
        f"**Task:** `{task}`  ",
        f"",
        f"> **MANDATORY NOTICE:**  ",
        f"> {MANDATORY_DISCLAIMER}",
        f"",
    ]

    if task == "prediction":
        md_lines.extend([
            f"> **PREDICTION BASELINE REQUIREMENT:**  ",
            f"> {PREDICTION_SKILL_DISCLAIMER}",
            f"",
        ])

    md_lines.extend([
        f"---",
        f"",
        f"## 1. Window-Level Classification Performance (Sealed Test Set)",
        f"",
        f"| Model / Baseline | Prevalence | Precision | Recall | F1 | PR-AUC | ROC-AUC | TP | FP | TN | FN |",
        f"| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    for row in csv_rows:
        pr_str = f"{row['pr_auc']:.4f}" if not pd.isna(row["pr_auc"]) else "N/A"
        roc_str = f"{row['roc_auc']:.4f}" if not pd.isna(row["roc_auc"]) else "N/A"
        md_lines.append(
            f"| **{row['model_name']}** | {row['prevalence']:.4f} | {row['precision']:.4f} | "
            f"{row['recall']:.4f} | {row['f1']:.4f} | {pr_str} | {roc_str} | "
            f"{row['true_positives']} | {row['false_positives']} | {row['true_negatives']} | {row['false_negatives']} |"
        )

    md_lines.append("")

    # Event metrics section
    if event_report:
        md_lines.extend([
            f"## 2. Event-Level Macro Detection Performance",
            f"",
            f"- **Reference Events in Test Partition:** {event_report.n_reference_events}",
            f"- **Detected Events:** {event_report.n_detected_events}",
            f"- **Missed Events:** {event_report.n_missed_events}",
            f"- **Event Detection Rate (Macro Recall):** {event_report.event_detection_rate:.4f}",
            f"- **Candidate Predicted Intervals (Merged):** {event_report.n_predicted_intervals}",
            f"- **False-Alarm Predicted Intervals:** {event_report.n_false_alarm_intervals}",
            f"- **Merge Gap Parameter:** {event_report.merge_gap_seconds} s",
        ])
        if event_report.median_timing_error_sec is not None:
            md_lines.append(
                f"- **Onset Timing Error (Median):** {event_report.median_timing_error_sec:.1f} s "
                f"(IQR: {event_report.iqr_timing_error_sec:.1f} s)"
            )
        if task == "prediction":
            md_lines.append(
                f"- **Unwarned Onsets:** {event_report.n_unwarned_onsets}"
            )
            if event_report.median_lead_time_sec is not None:
                md_lines.append(
                    f"- **Median Forecast Lead Time:** {event_report.median_lead_time_sec:.1f} s"
                )
        md_lines.append("")

    # False alarm analysis section
    if false_alarm_report:
        md_lines.extend([
            f"## 3. Operational False-Alarm Analysis",
            f"",
            f"- **Verified Covered Observation Time:** {false_alarm_report.covered_observation_hours:.3f} hours "
            f"({false_alarm_report.covered_duration_sec:.1f} s of valid GTI)",
            f"- **False Alarms:** {false_alarm_report.n_false_alarms}",
            f"- **False Alarm Rate:** **{false_alarm_report.false_alarm_rate_per_hour:.3f} per covered observation hour**",
            f"",
        ])
        if false_alarm_report.missed_events:
            md_lines.extend([
                f"### Missed Event Detail Table",
                f"",
                f"| Event ID | Onset (sec) | End (sec) | Reason |",
                f"| :--- | :---: | :---: | :--- |",
            ])
            for m in false_alarm_report.missed_events:
                md_lines.append(f"| {m.event_id} | {m.onset_sec:.1f} | {m.end_sec:.1f} | {m.reason} |")
            md_lines.append("")

    # Calibration section
    if calibration_reports:
        md_lines.extend([
            f"## 4. Probability Calibration Assessment",
            f"",
            f"| Model | Brier Score | Expected Calibration Error (ECE) | Max Calibration Error (MCE) |",
            f"| :--- | :---: | :---: | :---: |",
        ])
        for m_name, c_rep in calibration_reports.items():
            md_lines.append(
                f"| **{m_name}** | {c_rep.brier_score:.4f} | {c_rep.expected_calibration_error:.4f} | {c_rep.max_calibration_error:.4f} |"
            )
        md_lines.append("")

    # Uncertainty section
    if uncertainty_report:
        md_lines.extend([
            f"## 5. Statistical Uncertainty (Block Bootstrap)",
            f"",
            f"- **Status:** `{uncertainty_report.status_message}`",
            f"- **Independent Observation Blocks:** {uncertainty_report.n_blocks} (Threshold required: {uncertainty_report.min_required_blocks})",
            f"- **Resamples:** {uncertainty_report.n_resamples}",
        ])
        if uncertainty_report.computed and uncertainty_report.metrics_ci:
            md_lines.extend([
                f"",
                f"| Metric | Point Estimate | {int(uncertainty_report.ci_level * 100)}% CI Lower | {int(uncertainty_report.ci_level * 100)}% CI Upper |",
                f"| :--- | :---: | :---: | :---: |",
            ])
            for m_name, ci in uncertainty_report.metrics_ci.items():
                md_lines.append(
                    f"| {m_name.upper()} | {ci.point_estimate:.4f} | {ci.ci_lower:.4f} | {ci.ci_upper:.4f} |"
                )
        md_lines.append("")

    report_md_path = e_dir / "evaluation_report.md"
    report_md_path.write_text("\n".join(md_lines), encoding="utf-8")

    # 4. Write dashboard contract
    write_dashboard_contract(e_dir)

    return e_dir
