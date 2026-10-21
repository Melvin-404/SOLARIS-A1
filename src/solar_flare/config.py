"""Configuration loading and validation for SOLARIS-A1.

Loads YAML configuration files, resolves paths relative to the project root,
and validates required keys with informative error reporting.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from solar_flare.paths import project_root, get_config_dir

REQUIRED_SECTIONS = ("project", "paths", "logging")
REQUIRED_KEYS = {
    "project": ("name", "stage_status"),
    "paths": ("raw_dir", "processed_dir", "results_dir", "logs_dir"),
    "logging": ("level", "file_name"),
}


class ConfigError(ValueError):
    """Exception raised for invalid, missing, or malformed configuration."""
    pass


def load_config(config_path: Optional[Path | str] = None) -> Dict[str, Any]:
    """Load, validate, and resolve paths for a YAML configuration file.

    Args:
        config_path: Optional path to the configuration YAML file.
            Defaults to `<project_root>/config/default.yaml`.

    Returns:
        Dict[str, Any]: Parsed configuration dictionary with an added
            `resolved_paths` dictionary containing absolute Path objects.

    Raises:
        FileNotFoundError: If the specified config file does not exist.
        ConfigError: If the file is malformed or missing required keys.
    """
    if config_path is None:
        file_path = get_config_dir() / "default.yaml"
    else:
        file_path = Path(config_path)
        if not file_path.is_absolute():
            file_path = project_root() / file_path

    if not file_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_cfg = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigError(
            f"Malformed YAML in configuration file '{file_path}': {exc}"
        ) from exc

    if not isinstance(raw_cfg, dict):
        raise ConfigError(
            f"Configuration file '{file_path}' must contain a YAML mapping (dictionary), got {type(raw_cfg).__name__}."
        )

    # Validate required sections and keys
    for section in REQUIRED_SECTIONS:
        if section not in raw_cfg:
            raise ConfigError(
                f"Missing required section '{section}' in configuration file '{file_path}'."
            )
        if not isinstance(raw_cfg[section], dict):
            raise ConfigError(
                f"Section '{section}' in '{file_path}' must be a dictionary, got {type(raw_cfg[section]).__name__}."
            )
        for key in REQUIRED_KEYS[section]:
            if key not in raw_cfg[section]:
                raise ConfigError(
                    f"Missing required key '{key}' in section '{section}' of configuration file '{file_path}'."
                )

    # Resolve paths relative to project root (NOT current working directory)
    root = project_root()
    resolved_paths: Dict[str, Path] = {}
    for path_key, rel_path in raw_cfg["paths"].items():
        resolved_paths[path_key] = (root / rel_path).resolve()

    raw_cfg["resolved_paths"] = resolved_paths
    return raw_cfg
