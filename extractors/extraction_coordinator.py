"""
Extraction coordinator to orchestrate the full extraction pipeline.

Coordinates text extraction, OCR, and LLM processing based on document type and strategy.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from .base_extractor import ExtractedTextResult
from .strategy_factory import StrategyFactory
from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .ocr_handler import OCRHandler
from ai.gemini_client import GeminiClient
from utils.logger import get_logger
from utils.exceptions import FileError, ExtractionError, LLMError
from config import EXTRACTION_STRATEGY, OCR_ENGINE

logger = get_logger(__name__)


class ExtractionCoordinator:
    """Coordinate the full extraction and metadata extraction pipeline."""
    
    def __init__(self, gemini_client=None):
        """
        Initialize extraction coordinator.
        
        Args:
            gemini_client: Optional Gemini client (will be created if needed)
        """
        if gemini_client is None and GeminiClient:
            self.gemini_client = GeminiClient()
        else:
            self.gemini_client = gemini_client
        
        self.strategy_factory = StrategyFactory(gemini_client=self.gemini_client)
        self.logger = get_logger(self.__class__.__module__)
    
    def extract_metadata(self, file_path: str, 
                        strategy: str = None) -> Dict[str, Any]:
        """
        Extract metadata from document using full pipeline.
        
        This is the main entry point that:
        1. Extracts text from document (PDF/DOCX)
        2. Handles OCR if needed (for scanned PDFs)
        3. Processes extracted text with Gemini to extract metadata
        4. Returns structured metadata matching schema
        
        Args:
            file_path: Path to document file
            strategy: Extraction strategy (defaults to config value)
        
        Returns:
            Dictionary with extracted metadata matching schema
        """
        self.logger.info(f"Starting metadata extraction for: {file_path}")
        
        # Step 1: Extract text from document
        extraction_result = self._extract_text(file_path, strategy)
        
        # Step 2: Process with LLM to extract metadata
        # Check actual strategy used (from result metadata) not global config
        if (extraction_result.metadata.get("is_scanned") and 
            extraction_result.metadata.get("extraction_strategy") == "gemini_vision"):
            # Gemini Vision already extracted metadata directly
            metadata = extraction_result.metadata.get("extracted_metadata", {})
        else:
            # Process extracted text with Gemini Flash
            metadata = self._process_with_llm(extraction_result)
        
        return metadata
    
    def _extract_text(self, file_path: str, 
                     strategy: str = None) -> ExtractedTextResult:
        """
        Extract text from document.
        
        Args:
            file_path: Path to document file
            strategy: Extraction strategy
        
        Returns:
            ExtractedTextResult with text
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == ".pdf":
            return self._extract_from_pdf(file_path, strategy)
        elif file_ext == ".docx":
            return self._extract_from_docx(file_path)
        else:
            raise FileError(
                f"Unsupported file type: {file_ext}",
                details={"file_path": file_path, "file_extension": file_ext}
            )
    
    def _extract_from_pdf(self, file_path: str, 
                          strategy: str = None) -> ExtractedTextResult:
        """
        Extract text from PDF.
        
        Args:
            file_path: Path to PDF file
            strategy: Extraction strategy
        
        Returns:
            ExtractedTextResult with text
        """
        extractor = self.strategy_factory.get_extractor(file_path, strategy)
        result = extractor.extract(file_path)
        
        # If image-based PDF and not using Gemini Vision, run OCR
        # Check actual strategy used (from result metadata) not global config
        if (result.metadata.get("is_scanned") and 
            result.metadata.get("extraction_method") == "ocr" and
            result.metadata.get("extraction_strategy") != "gemini_vision"):
            
            # Get preprocessed images from result
            images = result.metadata.get("preprocessed_images", [])
            
            if images:
                # Run OCR
                ocr_handler = OCRHandler(ocr_engine=OCR_ENGINE)
                ocr_texts = ocr_handler.extract_text_from_images(images)
                
                # Combine OCR text
                result.raw_text = "\n\n".join(ocr_texts)
                result.metadata["ocr_engine"] = OCR_ENGINE
                
                # Clear preprocessed images from memory after OCR is complete
                # This is important for large PDFs to reduce memory usage
                if "preprocessed_images" in result.metadata:
                    del result.metadata["preprocessed_images"]
                    self.logger.debug("Cleared preprocessed images from memory after OCR")
        
        return result
    
    def _extract_from_docx(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text from DOCX.
        
        Args:
            file_path: Path to DOCX file
        
        Returns:
            ExtractedTextResult with text
        """
        from .docx_extractor import DOCXExtractor
        extractor = DOCXExtractor(gemini_client=self.gemini_client)
        return extractor.extract(file_path)
    
    def _process_with_llm(self, extraction_result: ExtractedTextResult) -> Dict[str, Any]:
        """
        Process extracted text with Gemini LLM to extract metadata.
        
        Args:
            extraction_result: Result from text extraction
        
        Returns:
            Dictionary with extracted metadata
        """
        if not extraction_result.raw_text:
            self.logger.warning("No text extracted, returning empty schema")
            from ai.schema import SchemaValidator
            validator = SchemaValidator()
            return validator.get_empty_schema()
        
        try:
            # Use Gemini Flash to extract metadata
            metadata = self.gemini_client.extract_metadata_from_text(
                extraction_result.raw_text
            )
            return metadata
        except LLMError as e:
            self.logger.error("LLM extraction failed", exc_info=True)
            raise ExtractionError(
                f"Failed to extract metadata using LLM: {e}",
                details={"file_path": extraction_result.metadata.get("file_path", "unknown")}
            ) from e

