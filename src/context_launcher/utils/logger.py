"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_level: int = logging.INFO, log_file: Optional[Path] = None):
    """Configure application logging.

    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional log file path
    """
    from ..core.platform_utils import PlatformManager

    # Get default log directory
    if log_file is None:
        log_dir = PlatformManager.get_default_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "context_launcher.log"

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # Configure root logger
    root_logger = logging.getLogger('context_launcher')
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # File handler (detailed logging)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # Console handler (simple logging)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)

    root_logger.info(f"Logging initialized. Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.

    Args:
        name: Logger name (usually module name)

    Returns:
        Logger instance
    """
    if not name.startswith('context_launcher'):
        name = f'context_launcher.{name}'

    return logging.getLogger(name)
