"""
Custom exception classes for MSA Metadata Extractor.

Provides structured error handling with specific exception types for different error categories.
"""


class MSAExtractorError(Exception):
    """Base exception for all MSA Extractor errors."""
    
    def __init__(self, message: str, details: dict = None):
        """
        Initialize exception.
        
        Args:
            message: Error message
            details: Additional error details (optional)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(MSAExtractorError):
    """Configuration-related errors (missing API keys, invalid settings, etc.)."""
    pass


class FileError(MSAExtractorError):
    """File-related errors (not found, invalid format, encrypted, etc.)."""
    pass


class ExtractionError(MSAExtractorError):
    """Text extraction errors (PDF parsing, DOCX parsing, etc.)."""
    pass


class OCRError(MSAExtractorError):
    """OCR-related errors (Tesseract failures, GCV errors, etc.)."""
    pass


class LLMError(MSAExtractorError):
    """LLM API errors (authentication, rate limits, parsing failures, etc.)."""
    pass


class ValidationError(MSAExtractorError):
    """Schema validation errors (missing fields, invalid format, etc.)."""
    pass

