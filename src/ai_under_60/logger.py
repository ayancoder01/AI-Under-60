"""Logging configuration for AI Under 60.

Provides standard library logging to both console and a local logs directory
with a timestamped format.
"""

import logging
from pathlib import Path
from typing import Optional

from ai_under_60.config import get_config

DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = "ai_under_60",
    log_level: Optional[str] = None,
    logs_dir: Optional[Path] = None,
    clear_existing: bool = False,
) -> logging.Logger:
    """Set up and return a configured logger instance.

    Args:
        name: The name of the logger (defaults to "ai_under_60").
        log_level: Desired log level string (DEBUG, INFO, etc.). If None, loads from config.
        logs_dir: Directory where log files should be written. Defaults to <project_root>/logs.
        clear_existing: Whether to clear existing handlers before configuring.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    if clear_existing:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
    elif logger.handlers:
        return logger

    if isinstance(log_level, str):
        level_str = log_level.strip().upper()
        numeric_level = getattr(logging, level_str, None)
        if not isinstance(numeric_level, int):
            numeric_level = logging.INFO
    else:
        config = get_config()
        level_str = config.log_level
        numeric_level = getattr(logging, level_str, logging.INFO)

    logger.setLevel(numeric_level)

    formatter = logging.Formatter(fmt=DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Local File Handler in logs/ directory
    if logs_dir is None:
        config = get_config()
        logs_dir = config.project_root / "logs"

    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = logs_dir / "ai_under_60.log"
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as err:
        logger.warning("Could not initialize file logger in %s: %s", logs_dir, err)

    return logger

