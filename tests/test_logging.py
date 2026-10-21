"""Unit tests for solar_flare.logging_setup module."""

import logging
from solar_flare.logging_setup import setup_logging


def test_setup_logging_idempotent(tmp_path):
    """Verify that setup_logging configures logger without duplicating handlers."""
    log_dir = tmp_path / "logs"
    logger1 = setup_logging(level="DEBUG", log_file="test.log", log_dir=log_dir)
    assert isinstance(logger1, logging.Logger)
    num_handlers_initial = len(logger1.handlers)
    assert num_handlers_initial >= 2  # StreamHandler and RotatingFileHandler

    # Second call should not add additional handlers
    logger2 = setup_logging(level="INFO", log_file="test.log", log_dir=log_dir)
    assert len(logger2.handlers) == num_handlers_initial
    assert logger1 is logger2


def test_setup_logging_creates_log_file(tmp_path):
    """Verify that logging creates the expected log file."""
    log_dir = tmp_path / "logs"
    logger = setup_logging(level="DEBUG", log_file="app_test.log", log_dir=log_dir)
    logger.info("Test log entry")
    log_file = log_dir / "app_test.log"
    assert log_file.is_file()
    content = log_file.read_text(encoding="utf-8")
    assert "Test log entry" in content
