"""Path resolution utilities for SOLARIS-A1.

Provides project root derivation and path helpers anchored to the repository
root rather than the current working directory.
"""

from pathlib import Path


def project_root() -> Path:
    """Return the absolute path to the project root directory.

    Derives the root dynamically from this file's location:
    src/solar_flare/paths.py -> project_root is 3 levels up.

    Returns:
        Path: Absolute resolved path to the project root.
    """
    return Path(__file__).resolve().parent.parent.parent


def get_raw_dir(create: bool = False) -> Path:
    """Return the path to the raw data directory (data/raw).

    Args:
        create: If True, creates the directory if missing. Defaults to False.

    Returns:
        Path: Path to data/raw.
    """
    p = project_root() / "data" / "raw"
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return p


def get_gti_dir(create: bool = False) -> Path:
    """Return the path to the raw GTI directory (data/raw/gti).

    Args:
        create: If True, creates the directory if missing. Defaults to False.

    Returns:
        Path: Path to data/raw/gti.
    """
    p = project_root() / "data" / "raw" / "gti"
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return p


def get_processed_dir(create: bool = False) -> Path:
    """Return the path to the processed data directory (data/processed).

    Args:
        create: If True, creates the directory if missing. Defaults to False.

    Returns:
        Path: Path to data/processed.
    """
    p = project_root() / "data" / "processed"
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return p


def get_results_dir(create: bool = False) -> Path:
    """Return the path to the results directory (results).

    Args:
        create: If True, creates the directory if missing. Defaults to False.

    Returns:
        Path: Path to results.
    """
    p = project_root() / "results"
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return p


def get_logs_dir(create: bool = False) -> Path:
    """Return the path to the logs directory (logs).

    Args:
        create: If True, creates the directory if missing. Defaults to False.

    Returns:
        Path: Path to logs.
    """
    p = project_root() / "logs"
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return p


def get_config_dir() -> Path:
    """Return the path to the configuration directory (config).

    Returns:
        Path: Path to config directory.
    """
    return project_root() / "config"
