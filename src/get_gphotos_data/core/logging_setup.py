"""Logging configuration and setup.

This module configures Python's logging system to write to a rotating
log file in the per-user application data directory. Log files are
rotated to prevent unbounded growth:
- Maximum file size: 2MB
- Number of backup files: 3
- Encoding: UTF-8

The log file is located at: {app_data_dir}/app.log
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .paths import app_data_dir


def setup_logging(enable_console: bool = False) -> None:
    """Configure rotating file logging in the per-user data directory.

    Args:
        enable_console: If True, also log to console (stdout).
    """
    data_dir = app_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    log_file = data_dir / "app.log"

    # Rotate log files to avoid unbounded growth.
    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Ensure we do not duplicate logs if setup_logging is called twice.
    root.handlers.clear()
    root.addHandler(file_handler)

    # Add console handler if debug logging is enabled
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(fmt)
        root.addHandler(console_handler)

    logging.getLogger(__name__).info("Logging initialized: %s (console: %s)", log_file, enable_console)
