"""
Utility modules for MSA Metadata Extractor.

Provides logging, exception handling, and other shared utilities.
"""

from .logger import get_logger, setup_logging
from .exceptions import (
    MSAExtractorError,
    ConfigurationError,
    FileError,
    ExtractionError,
    OCRError,
    LLMError,
    ValidationError
)

__all__ = [
    "get_logger",
    "setup_logging",
    "MSAExtractorError",
    "ConfigurationError",
    "FileError",
    "ExtractionError",
    "OCRError",
    "LLMError",
    "ValidationError",
]

