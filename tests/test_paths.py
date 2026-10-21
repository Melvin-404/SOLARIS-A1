"""Unit tests for solar_flare.paths module."""

from pathlib import Path
from solar_flare.paths import (
    project_root,
    get_raw_dir,
    get_gti_dir,
    get_processed_dir,
    get_results_dir,
    get_logs_dir,
    get_config_dir,
)


def test_project_root_exists():
    """Verify that project_root resolves to an existing directory."""
    root = project_root()
    assert isinstance(root, Path)
    assert root.is_dir()
    assert (root / "README.md").is_file()


def test_project_root_contains_expected_subdirs():
    """Verify that root contains key project folders."""
    root = project_root()
    assert (root / "src").is_dir()
    assert (root / "docs").is_dir()
    assert (root / "config").is_dir()


def test_paths_are_absolute():
    """Verify that all helper functions return absolute paths."""
    assert get_raw_dir().is_absolute()
    assert get_gti_dir().is_absolute()
    assert get_processed_dir().is_absolute()
    assert get_results_dir().is_absolute()
    assert get_logs_dir().is_absolute()
    assert get_config_dir().is_absolute()


def test_paths_relative_to_root():
    """Verify that subdirectories are anchored under project_root."""
    root = project_root()
    assert get_raw_dir() == root / "data" / "raw"
    assert get_gti_dir() == root / "data" / "raw" / "gti"
    assert get_processed_dir() == root / "data" / "processed"
    assert get_results_dir() == root / "results"
    assert get_logs_dir() == root / "logs"
    assert get_config_dir() == root / "config"
