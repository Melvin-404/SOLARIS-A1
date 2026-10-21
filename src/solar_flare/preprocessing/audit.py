"""Audit logging and mathematical reconciliation for SOLARIS-A1 (Stage 7).

Accumulates exclusion logs across all filtering steps, asserts exact sample conservation:
    retained_samples + excluded_samples == original_samples
Raises ReconciliationError if the invariant is violated.
Records source file SHA-256 hashes before and after execution to ensure zero mutation.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from solar_flare.preprocessing.filters import EXCLUSION_COLUMNS


class ReconciliationError(AssertionError):
    """Raised when mathematical sample conservation fails: retained + excluded != original."""
    pass


class ProcessingAudit:
    """Audit accumulator tracking sample exclusions and mathematical reconciliation."""

    def __init__(
        self,
        file_stem: str,
        original_sample_count: int,
        source_file_sha256_before: str,
        parameters: Dict[str, Any],
        is_final_run: bool = False,
        software_version: str = "SOLARIS-A1 Stage 7 (1.0.0)",
    ) -> None:
        self.file_stem = file_stem
        self.original_sample_count = int(original_sample_count)
        self.source_file_sha256_before = source_file_sha256_before
        self.source_file_sha256_after: Optional[str] = None
        self.parameters = dict(parameters)
        self.is_final_run = bool(is_final_run)
        self.software_version = software_version
        self.utc_processing_timestamp = datetime.now(timezone.utc).isoformat()

        self._exclusion_logs: List[pd.DataFrame] = []
        self.retained_sample_count: int = 0
        self.segments_metadata: List[Dict[str, Any]] = []
        self._reconciled: bool = False

    def add_exclusions(self, df_log: pd.DataFrame) -> None:
        """Add an exclusion log slice to the audit trail."""
        if df_log is not None and not df_log.empty:
            self._exclusion_logs.append(df_log)

    def set_retained(self, retained_count: int, segments: Optional[List[Any]] = None) -> None:
        """Record final retained sample count and segment metadata."""
        self.retained_sample_count = int(retained_count)
        self.segments_metadata = []
        if segments:
            for s in segments:
                if hasattr(s, "to_dict"):
                    self.segments_metadata.append(s.to_dict())
                elif isinstance(s, dict):
                    self.segments_metadata.append(s)

    def finalize_hashes(self, sha256_after: str) -> None:
        """Record the post-processing hash of the source raw file."""
        self.source_file_sha256_after = sha256_after

    def get_consolidated_exclusion_log(self) -> pd.DataFrame:
        """Return all accumulated exclusion records in a single DataFrame."""
        if not self._exclusion_logs:
            return pd.DataFrame(columns=EXCLUSION_COLUMNS)
        return pd.concat(self._exclusion_logs, ignore_index=True)

    def get_counts_by_reason(self) -> Dict[str, int]:
        """Aggregate total excluded sample count per reason."""
        full_log = self.get_consolidated_exclusion_log()
        if full_log.empty:
            return {}
        counts = full_log["reason"].value_counts().to_dict()
        return {str(k): int(v) for k, v in counts.items()}

    def reconcile(self) -> bool:
        """Assert strict sample conservation: retained + excluded == original.
        
        Returns
        -------
        bool
            True if sample reconciliation and hash verification succeed.
            
        Raises
        -------
        ReconciliationError
            If sample conservation fails or raw hash has changed.
        """
        full_log = self.get_consolidated_exclusion_log()
        excluded_count = len(full_log)
        total_accounted = self.retained_sample_count + excluded_count

        if total_accounted != self.original_sample_count:
            diff = total_accounted - self.original_sample_count
            raise ReconciliationError(
                f"Mathematical sample reconciliation failed for '{self.file_stem}': "
                f"retained ({self.retained_sample_count}) + excluded ({excluded_count}) = {total_accounted} "
                f"!= original ({self.original_sample_count}) [discrepancy: {diff:+d} samples]"
            )

        if self.source_file_sha256_after is not None:
            if self.source_file_sha256_before != self.source_file_sha256_after:
                raise ReconciliationError(
                    f"CRITICAL IMMUTABILITY VIOLATION: Source raw file hash changed for '{self.file_stem}'! "
                    f"Before: {self.source_file_sha256_before} != After: {self.source_file_sha256_after}"
                )

        self._reconciled = True
        return True


def write_audit(audit: ProcessingAudit, out_dir: Union[Path, str]) -> Dict[str, Path]:
    """Export audit reports to CSV, JSON, and Markdown in out_dir.
    
    Parameters
    ----------
    audit : ProcessingAudit
        Completed processing audit object.
    out_dir : Path or str
        Destination directory.
        
    Returns
    -------
    Dict[str, Path]
        Paths to created audit files.
    """
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    stem = audit.file_stem
    csv_path = target_dir / f"audit_{stem}.csv"
    json_path = target_dir / f"audit_{stem}.json"
    md_path = target_dir / f"audit_{stem}.md"

    # 1. Write exclusion log CSV
    full_log = audit.get_consolidated_exclusion_log()
    full_log.to_csv(csv_path, index=False)

    # 2. Write JSON parameters and summary
    counts_by_reason = audit.get_counts_by_reason()
    total_excluded = len(full_log)
    retention_pct = (
        float(audit.retained_sample_count / audit.original_sample_count * 100.0)
        if audit.original_sample_count > 0
        else 0.0
    )

    payload = {
        "file_stem": stem,
        "is_final_run": audit.is_final_run,
        "run_mode": "APPROVED (FINAL)" if audit.is_final_run else "PROVISIONAL (DEVELOPMENT)",
        "utc_processing_timestamp": audit.utc_processing_timestamp,
        "software_version": audit.software_version,
        "raw_file_sha256_before": audit.source_file_sha256_before,
        "raw_file_sha256_after": audit.source_file_sha256_after,
        "raw_immutability_verified": (audit.source_file_sha256_before == audit.source_file_sha256_after),
        "reconciliation_passed": audit._reconciled,
        "sample_counts": {
            "original": audit.original_sample_count,
            "retained": audit.retained_sample_count,
            "excluded_total": total_excluded,
            "retention_percentage": round(retention_pct, 4),
            "excluded_by_reason": counts_by_reason,
        },
        "parameters": audit.parameters,
        "segments": audit.segments_metadata,
    }

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(payload, jf, indent=2)

    # 3. Write Markdown summary
    status_label = "**APPROVED (FINAL)**" if audit.is_final_run else "**PROVISIONAL (DEVELOPMENT)**"
    lines = [
        f"# Preprocessing & Segmentation Audit: `{stem}`",
        "",
        f"- **Run Mode:** {status_label}",
        f"- **Processing Timestamp (UTC):** `{audit.utc_processing_timestamp}`",
        f"- **Software Version:** `{audit.software_version}`",
        f"- **Source Raw Hash (Before):** `{audit.source_file_sha256_before}`",
        f"- **Source Raw Hash (After):**  `{audit.source_file_sha256_after}`",
        f"- **Raw Immutability:** `{'PASS (100% IDENTICAL)' if audit.source_file_sha256_before == audit.source_file_sha256_after else 'FAIL'}`",
        f"- **Mathematical Reconciliation:** `{'PASS (retained + excluded == original)' if audit._reconciled else 'FAIL'}`",
        "",
        "---",
        "",
        "## Sample Conservation Table",
        "",
        "| Category | Count | Percentage of Original |",
        "| :--- | :--- | :--- |",
        f"| **Original Total Samples** | `{audit.original_sample_count:,}` | `100.0000%` |",
        f"| **Retained in Valid Segments** | `{audit.retained_sample_count:,}` | `{retention_pct:.4f}%` |",
        f"| **Total Excluded Samples** | `{total_excluded:,}` | `{float(total_excluded / audit.original_sample_count * 100.0):.4f}%` |",
    ]

    for reason, count in sorted(counts_by_reason.items()):
        pct = float(count / audit.original_sample_count * 100.0) if audit.original_sample_count > 0 else 0.0
        lines.append(f"| ↳ Excluded: `{reason}` | `{count:,}` | `{pct:.4f}%` |")

    lines.extend([
        "",
        "---",
        "",
        "## Segmentation Results",
        "",
        f"- **Total Valid Segments:** `{len(audit.segments_metadata)}`",
        "",
        "| Segment ID | Start (s) | End (s) | Duration (s) | N Samples | Median Cadence (s) | Gap Before (s) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    if audit.segments_metadata:
        for s in audit.segments_metadata:
            lines.append(
                f"| `{s['segment_id']}` | `{s['start']:.1f}` | `{s['end']:.1f}` | "
                f"`{s['duration_seconds']:.1f}` | `{s['n_samples']:,}` | "
                f"`{s['cadence_median']:.4f}` | `{s['gap_before_seconds']:.1f}` |"
            )
    else:
        lines.append("| *None* | - | - | - | 0 | - | - |")

    lines.extend([
        "",
        "---",
        "",
        "## Preprocessing Parameters Applied",
        "",
        "```yaml",
    ])
    for k, v in audit.parameters.items():
        lines.append(f"{k}: {v}")
    lines.extend([
        "```",
        "",
    ])

    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write("\n".join(lines))

    return {
        "csv": csv_path,
        "json": json_path,
        "md": md_path,
    }
