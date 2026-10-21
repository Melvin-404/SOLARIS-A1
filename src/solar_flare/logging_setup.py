"""Logging setup for SOLARIS-A1.

Configures console and rotating file logging writing to the logs/ directory.
Setup is idempotent and safe to invoke multiple times.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from solar_flare.paths import get_logs_dir

_LOGGER_NAME = "solar_flare"
_DEFAULT_LOG_FILE = "solaris_a1.log"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3

_configured: bool = False


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: Optional[Path] = None,
    force: bool = False,
) -> logging.Logger:
    """Configure console and rotating file logging for SOLARIS-A1.

    This function is idempotent. Calling it multiple times updates log levels
    without adding duplicate stream or file handlers.

    Args:
        level: Logging level string ('DEBUG', 'INFO', 'WARNING', 'ERROR').
            Defaults to 'INFO'.
        log_file: Name of the log file. Defaults to 'solaris_a1.log'.
        log_dir: Directory where logs are saved. Defaults to `<project_root>/logs`.
        force: If True, forces handler recreation even if already configured.

    Returns:
        logging.Logger: Configured logger for the 'solar_flare' namespace.
    """
    global _configured

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(numeric_level)

    # Determine destination directory
    target_dir = log_dir if log_dir is not None else get_logs_dir(create=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = log_file if log_file is not None else _DEFAULT_LOG_FILE
    log_path = (target_dir / filename).resolve()

    # Avoid duplicate handlers on repeated calls with the same configuration
    if _configured and not force:
        # Check if an existing RotatingFileHandler is already pointing to this log_path
        current_file_handlers = [
            h for h in logger.handlers if isinstance(h, RotatingFileHandler)
        ]
        if current_file_handlers and Path(current_file_handlers[0].baseFilename).resolve() == log_path:
            for handler in logger.handlers:
                handler.setLevel(numeric_level)
            return logger


    # Remove any existing handlers on this logger to guarantee clean state
    logger.handlers.clear()
    logger.propagate = False

    # Formatters
    console_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d (%(funcName)s): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    _configured = True
    logger.debug("Logging initialized. Writing to %s", log_path)
    return logger
