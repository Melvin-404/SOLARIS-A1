"""Unit tests for solar_flare.config module."""

from pathlib import Path
import pytest
from solar_flare.config import load_config, ConfigError
from solar_flare.paths import project_root


def test_load_default_config():
    """Verify that default config loads correctly with expected structure."""
    cfg = load_config()
    assert isinstance(cfg, dict)
    assert "project" in cfg
    assert "paths" in cfg
    assert "logging" in cfg
    assert cfg["project"]["name"] == "SOLARIS-A1"
    assert "stage_status" in cfg["project"]
    assert cfg["project"]["stage_status"].startswith("Stage")


def test_config_resolved_paths():
    """Verify that resolved_paths contains absolute Path objects anchored to root."""
    cfg = load_config()
    assert "resolved_paths" in cfg
    resolved = cfg["resolved_paths"]
    root = project_root()

    for path_key in ("raw_dir", "processed_dir", "results_dir", "logs_dir"):
        assert path_key in resolved
        assert isinstance(resolved[path_key], Path)
        assert resolved[path_key].is_absolute()

    assert resolved["raw_dir"] == root / "data" / "raw"
    assert resolved["processed_dir"] == root / "data" / "processed"


def test_config_file_not_found():
    """Verify that missing config file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_config_file.yaml")


def test_config_missing_required_section(tmp_path):
    """Verify that omitting a required section raises ConfigError."""
    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text("project:\n  name: Test\n  stage_status: S1\n", encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_config(bad_config)
    assert "Missing required section" in str(exc_info.value)


def test_config_missing_required_key(tmp_path):
    """Verify that omitting a required key inside a section raises ConfigError."""
    bad_config = tmp_path / "bad_key.yaml"
    content = (
        "project:\n"
        "  name: Test\n"
        "paths:\n"
        "  raw_dir: data/raw\n"
        "  processed_dir: data/processed\n"
        "  results_dir: results\n"
        "  logs_dir: logs\n"
        "logging:\n"
        "  level: INFO\n"
        "  file_name: test.log\n"
    )
    bad_config.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_config(bad_config)
    assert "Missing required key 'stage_status'" in str(exc_info.value)


def test_config_malformed_yaml(tmp_path):
    """Verify that unparseable YAML syntax raises ConfigError."""
    bad_config = tmp_path / "syntax_error.yaml"
    bad_config.write_text("project: {unclosed_dict", encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_config(bad_config)
    assert "Malformed YAML" in str(exc_info.value)
