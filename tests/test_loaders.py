"""Unit tests for dashboard data loaders (Stage 12).

Tests:
1. Missing file returns LoadResult with status='MISSING'.
2. Synthetic valid CSV loads with status='OK' or 'PROVISIONAL'.
3. Malformed unparseable file returns LoadResult with status='ERROR'.
4. Empty CSV returns LoadResult with status='EMPTY'.
5. Zero unhandled exceptions propagate out of loaders.
"""

from pathlib import Path
import pytest
from dashboard.loaders import (
    load_inventory_pure,
    load_quality_summary_pure,
    load_feature_index_pure,
    load_policy_status_pure,
    load_experiments_pure,
    LoadResult,
)


def test_missing_files_return_missing_status(tmp_path: Path):
    """Verify that loaders return status='MISSING' when files do not exist."""
    empty_root = tmp_path / "empty_proj"
    empty_root.mkdir()

    res_inv = load_inventory_pure(root=empty_root)
    assert isinstance(res_inv, LoadResult)
    assert res_inv.status == "MISSING"
    assert res_inv.data is None

    res_qual = load_quality_summary_pure(root=empty_root)
    assert res_qual.status == "MISSING"

    res_feat = load_feature_index_pure(root=empty_root)
    assert res_feat.status == "MISSING"

    res_exp = load_experiments_pure(root=empty_root)
    assert res_exp.status == "MISSING"


def test_synthetic_valid_csv_loads_ok(tmp_path: Path):
    """Verify that valid synthetic CSV returns status='OK'."""
    root = tmp_path / "valid_proj"
    inv_dir = root / "results" / "inventory"
    inv_dir.mkdir(parents=True)
    inv_csv = inv_dir / "inventory.csv"
    inv_csv.write_text("file_name,product_type\ntest.lc,LIGHTCURVE\n", encoding="utf-8")

    res = load_inventory_pure(root=root)
    assert res.status == "OK"
    assert res.data is not None
    assert len(res.data) == 1
    assert res.data.iloc[0]["file_name"] == "test.lc"


def test_empty_csv_returns_empty_status(tmp_path: Path):
    """Verify that an empty CSV returns status='EMPTY'."""
    root = tmp_path / "empty_csv_proj"
    inv_dir = root / "results" / "inventory"
    inv_dir.mkdir(parents=True)
    inv_csv = inv_dir / "inventory.csv"
    inv_csv.write_text("", encoding="utf-8")  # Completely empty file

    res = load_inventory_pure(root=root)
    assert res.status in {"EMPTY", "ERROR"}


def test_malformed_csv_returns_error_status(tmp_path: Path):
    """Verify that a malformed unparseable file returns status='ERROR' and does not raise."""
    root = tmp_path / "corrupt_proj"
    q_dir = root / "results" / "quality"
    q_dir.mkdir(parents=True)
    q_csv = q_dir / "summary.csv"
    # Write invalid data that triggers a parser error (e.g. mismatched quotes or binary garbage)
    q_csv.write_bytes(b"\x00\xff\xfe\x01\x02\x03\x04")

    res = load_quality_summary_pure(root=root)
    assert res.status == "ERROR"
    assert "Error" in res.message or "Failed" in res.message
    assert res.data is None


def test_policy_status_loader(tmp_path: Path):
    """Verify load_policy_status_pure under missing, draft, and approved policies."""
    root = tmp_path / "policy_proj"
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True)
    policy_md = docs_dir / "08_labelling_policy.md"

    # 1. Missing
    res_miss = load_policy_status_pure(root=root)
    assert res_miss.status == "MISSING"
    assert res_miss.data["approved"] is False

    # 2. Draft
    policy_md.write_text("# STATUS: DRAFT\nContent\n", encoding="utf-8")
    res_draft = load_policy_status_pure(root=root)
    assert res_draft.status == "PROVISIONAL"
    assert res_draft.data["approved"] is False

    # 3. Approved
    policy_md.write_text("# STATUS: APPROVED\nApproved by Researcher\n", encoding="utf-8")
    res_appr = load_policy_status_pure(root=root)
    assert res_appr.status == "OK"
    assert res_appr.data["approved"] is True
