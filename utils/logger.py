"""
Centralized logging configuration for MSA Metadata Extractor.

Provides structured logging with file rotation, multiple formats, and module-level control.
"""

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from config import (
    LOG_LEVEL,
    LOG_FILE_ENABLED,
    LOG_FILE_PATH,
    LOG_FILE_FORMAT,
    LOG_FILE_ROTATION_DAYS,
    LOG_FILE_MAX_SIZE_MB,
    LOG_CONSOLE_ENABLED,
    LOG_CONSOLE_FORMAT,
    LOG_LEVELS,
)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra") and record.extra:
            log_data.update(record.extra)
        
        return json.dumps(log_data, ensure_ascii=False)


class StandardFormatter(logging.Formatter):
    """Standard human-readable formatter."""
    
    def __init__(self):
        super().__init__(
            fmt='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_logging() -> None:
    """
    Set up centralized logging configuration.
    
    Configures console and file handlers based on config settings.
    Should be called once at application startup.
    """
    # Get root logger
    root_logger = logging.getLogger("msa_extractor")
    root_logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers filter
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler
    if LOG_CONSOLE_ENABLED:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
        
        if LOG_CONSOLE_FORMAT == "json":
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(StandardFormatter())
        
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if LOG_FILE_ENABLED:
        # Create log file path
        log_file = LOG_FILE_PATH / f"msa_extractor_{datetime.now().strftime('%Y-%m-%d')}.log"
        
        # Use RotatingFileHandler for size-based rotation
        # Combined with daily naming for date-based rotation
        max_bytes = LOG_FILE_MAX_SIZE_MB * 1024 * 1024  # Convert MB to bytes
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=LOG_FILE_ROTATION_DAYS,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
        
        if LOG_FILE_FORMAT == "json":
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(StandardFormatter())
        
        root_logger.addHandler(file_handler)
    
    # Set module-specific log levels
    for module_name, level in LOG_LEVELS.items():
        module_logger = logging.getLogger(module_name)
        module_logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent propagation to root logger to avoid duplicate logs
    root_logger.propagate = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (usually __name__). If None, uses caller's module.
    
    Returns:
        Logger instance configured with centralized settings
    
    Example:
        logger = get_logger(__name__)
        logger.info("Processing file", extra={"file_path": path})
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'msa_extractor')
    
    # Ensure logging is set up (idempotent)
    root_logger = logging.getLogger("msa_extractor")
    if not root_logger.handlers:
        setup_logging()
    
    return logging.getLogger(name)


# Initialize logging on import
setup_logging()

