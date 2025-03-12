"""
Logging utilities module for APIFromAnything.

This module provides enhanced logging functionality for the application.
It includes structured logging, log rotation, and integration with external
logging services.
"""

import json
import logging
import logging.config
import os
import sys
import time
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

# Try to import optional dependencies
try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


class StructuredLogFormatter(logging.Formatter):
    """
    Formatter for structured JSON logs.
    
    This formatter outputs logs in JSON format with additional context
    information such as timestamp, level, module, and process ID.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: The log record to format.
            
        Returns:
            A JSON string representation of the log record.
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }
        
        # Add extra fields from record
        if hasattr(record, "extra") and record.extra:
            log_data.update(record.extra)
        
        return json.dumps(log_data)


def get_logger(name: str, extra: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Get a logger with the specified name and extra context.
    
    Args:
        name: The name of the logger.
        extra: Extra context to include in all log messages.
        
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    
    if extra:
        # Create a filter to add extra context to all records
        class ContextFilter(logging.Filter):
            def filter(self, record):
                record.extra = extra
                return True
        
        logger.addFilter(ContextFilter())
    
    return logger


def log_execution_time(logger: Optional[logging.Logger] = None, 
                      level: int = logging.DEBUG) -> Callable:
    """
    Decorator to log the execution time of a function.
    
    Args:
        logger: The logger to use. If None, a logger will be created.
        level: The logging level to use.
        
    Returns:
        A decorator function.
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.log(level, f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.log(level, f"Function '{func.__name__}' failed after {execution_time:.4f} seconds")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.log(level, f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.log(level, f"Function '{func.__name__}' failed after {execution_time:.4f} seconds")
                raise
        
        # Determine if the function is async or sync
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def setup_sentry(dsn: str, environment: str, release: str) -> None:
    """
    Set up Sentry for error tracking.
    
    Args:
        dsn: The Sentry DSN.
        environment: The environment name.
        release: The release version.
    """
    if not SENTRY_AVAILABLE:
        logging.warning("Sentry SDK not installed. Skipping Sentry setup.")
        return
    
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        traces_sample_rate=0.2,
        send_default_pii=False,
    )
    logging.info(f"Sentry initialized for environment: {environment}, release: {release}")


def configure_logging_dict(
    log_level: str = "INFO",
    log_format: str = "structured",
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10 MB
    backup_count: int = 5,
) -> Dict[str, Any]:
    """
    Create a logging configuration dictionary.
    
    Args:
        log_level: The logging level.
        log_format: The log format ('structured' for JSON, 'simple' for text).
        log_file: The path to the log file. If None, logs will be sent to stdout.
        max_bytes: The maximum size of the log file before rotation.
        backup_count: The number of backup log files to keep.
        
    Returns:
        A logging configuration dictionary.
    """
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "structured" if log_format == "structured" else "simple",
            "stream": "ext://sys.stdout",
        }
    }
    
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "structured" if log_format == "structured" else "simple",
            "filename": log_file,
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "encoding": "utf8",
        }
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "structured": {
                "()": "apifrom.logging_utils.StructuredLogFormatter",
            },
        },
        "handlers": handlers,
        "loggers": {
            "": {
                "level": log_level,
                "handlers": list(handlers.keys()),
                "propagate": True,
            },
            "uvicorn": {
                "level": log_level,
                "handlers": list(handlers.keys()),
                "propagate": False,
            },
            "uvicorn.access": {
                "level": log_level,
                "handlers": list(handlers.keys()),
                "propagate": False,
            },
        },
    }
    
    return config 