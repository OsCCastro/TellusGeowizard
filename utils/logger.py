# utils/logger.py
"""
Centralized logging configuration for GeoWizard application.
Provides consistent logging across all modules with file and console output.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from constants import (
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    LOG_FILE_NAME,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT
)


_loggers = {}  # Cache for loggers


def setup_logging(log_dir: str = None, level: int = logging.INFO) -> None:
    """
    Set up the root logger with file and console handlers.
    
    Args:
        log_dir: Directory to store log files. If None, uses current directory.
        level: Logging level (default: INFO)
    """
    # Determine log directory
    if log_dir is None:
        # Store logs in user's home directory under .geowizard
        log_dir = Path.home() / ".geowizard" / "logs"
    else:
        log_dir = Path(log_dir)
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Full path to log file
    log_file = log_dir / LOG_FILE_NAME
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only show warnings and errors in console
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Log initial message
    root_logger.info("=" * 60)
    root_logger.info("GeoWizard logging initialized")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module (typically __name__)
    
    Returns:
        Logger instance configured with the application's settings
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger
    
    return _loggers[name]


def log_exception(logger: logging.Logger, exc: Exception, context: str = None) -> None:
    """
    Log an exception with context information.
    
    Args:
        logger: Logger instance to use
        exc: Exception to log
        context: Additional context information
    """
    msg = f"Exception occurred"
    if context:
        msg += f" during {context}"
    msg += f": {type(exc).__name__}: {str(exc)}"
    
    logger.exception(msg)


def set_log_level(level: int) -> None:
    """
    Change the logging level for all loggers.
    
    Args:
        level: New logging level (e.g., logging.DEBUG, logging.INFO)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    for handler in root_logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            handler.setLevel(level)
