"""
Logging Utilities for Black Eagle Arrows Inventory Scraper

This module provides logging functionality for the Black Eagle Arrows inventory scraper.
It creates and configures loggers with both console and file handlers for comprehensive
logging throughout the application.

Author: Project Developer
License: MIT
"""

from pathlib import Path 
import logging 
from datetime import datetime 
import sys
from typing import Optional


def create_logger(logging_level: int, log_name: Optional[str] = None) -> logging.RootLogger:
    """
    Create and configure a logger with both console and file handlers.
    
    This function sets up a logger that writes to both the console and a timestamped
    log file. The log file is created in the 'logs' directory with a timestamp
    to avoid conflicts between different runs.
    
    Args:
        logging_level: Logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING)
        log_name: Optional name for the logger (defaults to module name)
        
    Returns:
        logging.RootLogger: Configured logger instance with console and file handlers
        
    Example:
        >>> logger = create_logger(logging.DEBUG)
        >>> logger.info("Application started")
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parents[1].joinpath('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger_name = log_name or __name__
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_level)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    # File handler with timestamp
    timestamp = str(datetime.now()).replace(":", "-").replace(" ", "_")
    log_file_path = logs_dir.joinpath(f'logs_{timestamp}.log')
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.
    
    Args:
        name: Optional name for the logger
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name or __name__)


def set_log_level(logger: logging.Logger, level: int) -> None:
    """
    Set the logging level for an existing logger.
    
    Args:
        logger: Logger instance to configure
        level: New logging level
    """
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)