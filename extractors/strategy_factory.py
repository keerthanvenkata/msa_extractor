"""
Strategy factory for selecting and routing extraction strategies.

Handles strategy selection based on configuration and document type.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from config import (
    EXTRACTION_METHOD,
    LLM_PROCESSING_MODE,
    OCR_ENGINE,
    GEMINI_API_KEY
)
from .base_extractor import BaseExtractor, ExtractedTextResult
from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .ocr_handler import OCRHandler
from utils.logger import get_logger
from utils.exceptions import ConfigurationError, FileError

logger = get_logger(__name__)


class StrategyFactory:
    """Factory for selecting and creating extraction strategies."""
    
    def __init__(self, gemini_client=None):
        """
        Initialize strategy factory.
        
        Args:
            gemini_client: Optional Gemini client (will be created if needed)
        """
        self.gemini_client = gemini_client
        self.logger = get_logger(self.__class__.__module__)
    
    def get_extractor(self, file_path: str, strategy: str = None) -> BaseExtractor:
        """
        Get appropriate extractor for file based on EXTRACTION_METHOD.
        
        Args:
            file_path: Path to document file
            strategy: Legacy parameter (ignored, use EXTRACTION_METHOD instead)
        
        Returns:
            Appropriate extractor instance
        """
        file_ext = Path(file_path).suffix.lower()
        
        # Handle DOCX files (always use DOCX extractor)
        if file_ext == ".docx":
            return DOCXExtractor(gemini_client=self.gemini_client)
        
        # Handle PDF files
        if file_ext == ".pdf":
            # New architecture: EXTRACTION_METHOD determines approach
            if EXTRACTION_METHOD == "vision_all":
                # Pure vision: use GeminiVisionExtractor
                from .gemini_vision_extractor import GeminiVisionExtractor
                return GeminiVisionExtractor(gemini_client=self.gemini_client)
            else:
                # All other methods use PDFExtractor
                return PDFExtractor(gemini_client=self.gemini_client)
        
        raise FileError(
            f"Unsupported file type: {file_ext}",
            details={"file_path": file_path, "file_extension": file_ext}
        )
    
    def extract_with_strategy(self, file_path: str, 
                             strategy: str = None) -> ExtractedTextResult:
        """
        Extract text using appropriate strategy.
        
        Args:
            file_path: Path to document file
            strategy: Extraction strategy (defaults to config value)
        
        Returns:
            ExtractedTextResult with text and metadata
        """
        extractor = self.get_extractor(file_path, strategy)
        return extractor.extract(file_path)

