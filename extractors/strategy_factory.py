"""
Strategy factory for selecting and routing extraction strategies.

Handles strategy selection based on configuration and document type.
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from config import (
    EXTRACTION_STRATEGY,
    OCR_ENGINE,
    GEMINI_API_KEY
)
from .base_extractor import BaseExtractor, ExtractedTextResult
from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .ocr_handler import OCRHandler

logger = logging.getLogger(__name__)


class StrategyFactory:
    """Factory for selecting and creating extraction strategies."""
    
    def __init__(self, gemini_client=None):
        """
        Initialize strategy factory.
        
        Args:
            gemini_client: Optional Gemini client (will be created if needed)
        """
        self.gemini_client = gemini_client
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_extractor(self, file_path: str, strategy: str = None) -> BaseExtractor:
        """
        Get appropriate extractor for file based on strategy.
        
        Args:
            file_path: Path to document file
            strategy: Extraction strategy (defaults to config value)
        
        Returns:
            Appropriate extractor instance
        """
        strategy = strategy or EXTRACTION_STRATEGY
        file_ext = Path(file_path).suffix.lower()
        
        # Handle DOCX files (always use DOCX extractor)
        if file_ext == ".docx":
            return DOCXExtractor(gemini_client=self.gemini_client)
        
        # Handle PDF files
        if file_ext == ".pdf":
            if strategy == "auto":
                return self._get_auto_strategy_extractor(file_path)
            elif strategy == "text_extraction":
                return PDFExtractor(gemini_client=self.gemini_client)
            elif strategy == "gemini_vision":
                from .gemini_vision_extractor import GeminiVisionExtractor
                return GeminiVisionExtractor(gemini_client=self.gemini_client)
            elif strategy in ["tesseract", "gcv"]:
                # Use PDF extractor with OCR handler
                return PDFExtractor(gemini_client=self.gemini_client)
            else:
                raise ValueError(f"Unknown extraction strategy: {strategy}")
        
        raise ValueError(f"Unsupported file type: {file_ext}")
    
    def _get_auto_strategy_extractor(self, file_path: str) -> BaseExtractor:
        """
        Get extractor using auto strategy (detects document type).
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            Appropriate extractor instance
        """
        # Detect PDF type and cache it in extractor to avoid re-detection
        pdf_extractor = PDFExtractor(gemini_client=self.gemini_client)
        pdf_type = pdf_extractor._detect_pdf_type(file_path)
        pdf_extractor._cached_pdf_type = pdf_type  # Cache to avoid re-detection
        
        self.logger.info(f"Auto strategy: Detected PDF type: {pdf_type}")
        
        if pdf_type == "text":
            # Text-based: Use text extraction + Gemini Flash
            return pdf_extractor
        elif pdf_type == "image":
            # Image-based: Use configured OCR strategy
            if OCR_ENGINE == "gemini_vision":
                from .gemini_vision_extractor import GeminiVisionExtractor
                return GeminiVisionExtractor(gemini_client=self.gemini_client)
            else:
                # Use PDF extractor with OCR handler
                return pdf_extractor
        else:  # mixed
            # For mixed, default to text extraction
            self.logger.warning("Mixed PDF detected, using text extraction strategy")
            return pdf_extractor
    
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

