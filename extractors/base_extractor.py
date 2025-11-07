"""
Base extractor class for all document extractors.

Provides common interface and functionality for PDF and DOCX extractors.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ExtractedTextResult:
    """Result structure for extracted text."""
    
    def __init__(self, raw_text: str = "", structured_text: list = None, 
                 headers: list = None, metadata: dict = None):
        self.raw_text = raw_text
        self.structured_text = structured_text or []
        self.headers = headers or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return {
            "raw_text": self.raw_text,
            "structured_text": self.structured_text,
            "headers": self.headers,
            "metadata": self.metadata
        }


class BaseExtractor(ABC):
    """Abstract base class for all document extractors."""
    
    def __init__(self):
        """Initialize the extractor."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def extract(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text from a document file.
        
        Args:
            file_path: Path to the document file
        
        Returns:
            ExtractedTextResult with extracted text and metadata
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid or unsupported
        """
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate that the file exists and is readable.
        
        Args:
            file_path: Path to the file
        
        Returns:
            True if file is valid
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        if path.stat().st_size == 0:
            raise ValueError(f"File is empty: {file_path}")
        
        return True
    
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic file metadata.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Dictionary with file metadata
        """
        path = Path(file_path)
        stat = path.stat()
        
        return {
            "file_path": str(path.absolute()),
            "file_name": path.name,
            "file_size": stat.st_size,
            "file_extension": path.suffix.lower(),
            "modified_time": stat.st_mtime
        }
    
    def _log_extraction_start(self, file_path: str):
        """Log extraction start."""
        self.logger.info(f"Starting extraction for: {file_path}")
    
    def _log_extraction_complete(self, file_path: str, result: ExtractedTextResult):
        """Log extraction completion."""
        self.logger.info(
            f"Extraction complete for: {file_path}. "
            f"Text length: {len(result.raw_text)}, "
            f"Pages: {result.metadata.get('page_count', 'unknown')}"
        )
    
    def _log_error(self, file_path: str, error: Exception):
        """Log extraction error."""
        self.logger.error(f"Extraction failed for {file_path}: {error}", exc_info=True)

