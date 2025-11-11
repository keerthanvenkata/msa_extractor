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
from config import (
    EXTRACTION_METHOD,
    LLM_PROCESSING_MODE,
    OCR_ENGINE
)

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
        
        # Step 2: Process with LLM based on LLM_PROCESSING_MODE
        llm_mode = extraction_result.metadata.get("llm_processing_mode", LLM_PROCESSING_MODE)
        metadata = self._process_with_llm(extraction_result, llm_mode)
        
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
        
        # Run OCR if extraction method requires it
        extraction_method = result.metadata.get("extraction_method", "")
        preprocessed_images = result.metadata.get("preprocessed_images")
        
        if preprocessed_images and extraction_method in ["ocr_all", "ocr_images_only"]:
            # Run OCR on preprocessed images
            ocr_handler = OCRHandler(ocr_engine=OCR_ENGINE)
            ocr_texts = ocr_handler.extract_text_from_images(preprocessed_images)
            
            # Combine with existing text (for ocr_images_only)
            if extraction_method == "ocr_images_only" and result.raw_text:
                result.raw_text += "\n\n" + "\n\n".join(ocr_texts)
            else:
                result.raw_text = "\n\n".join(ocr_texts)
            
            result.metadata["ocr_engine"] = OCR_ENGINE
            
            # Clear preprocessed images from memory after OCR
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
    
    def _process_with_llm(self, extraction_result: ExtractedTextResult, 
                         llm_mode: str = None) -> Dict[str, Any]:
        """
        Process extracted content with LLM based on LLM_PROCESSING_MODE.
        
        Supports:
        - text_llm: Send text to text LLM
        - vision_llm: Send images to vision LLM
        - multimodal: Send text + images together to vision LLM
        - dual_llm: Send text to text LLM + images to vision LLM separately, then merge
        
        Args:
            extraction_result: Result from content extraction
            llm_mode: LLM processing mode (defaults to config)
        
        Returns:
            Dictionary with extracted metadata
        """
        llm_mode = llm_mode or LLM_PROCESSING_MODE
        
        if llm_mode == "text_llm":
            # Send text to text LLM
            if not extraction_result.raw_text:
                self.logger.warning("No text extracted, returning empty schema")
                from ai.schema import SchemaValidator
                validator = SchemaValidator()
                return validator.get_empty_schema()
            
            try:
                metadata = self.gemini_client.extract_metadata_from_text(
                    extraction_result.raw_text
                )
                return metadata
            except LLMError as e:
                self.logger.error("Text LLM extraction failed", exc_info=True)
                raise ExtractionError(
                    f"Failed to extract metadata using text LLM: {e}",
                    details={"file_path": extraction_result.metadata.get("file_path", "unknown")}
                ) from e
        
        elif llm_mode == "vision_llm":
            # Send images to vision LLM
            image_pages_bytes = extraction_result.metadata.get("image_pages_bytes", [])
            
            if not image_pages_bytes:
                self.logger.warning("No images found, returning empty schema")
                from ai.schema import SchemaValidator
                validator = SchemaValidator()
                return validator.get_empty_schema()
            
            img_bytes_list = [img_bytes for _, img_bytes in image_pages_bytes]
            self.logger.info(f"Using vision LLM: {len(img_bytes_list)} image(s)")
            
            try:
                # Process first image (or all images - depends on implementation)
                # For now, process first image as primary
                if img_bytes_list:
                    metadata = self.gemini_client.extract_metadata_from_image(
                        img_bytes_list[0],
                        image_mime_type="image/png"
                    )
                    # TODO: Process all images and merge intelligently
                    return metadata
                else:
                    from ai.schema import SchemaValidator
                    validator = SchemaValidator()
                    return validator.get_empty_schema()
            except LLMError as e:
                self.logger.error("Vision LLM extraction failed", exc_info=True)
                raise ExtractionError(
                    f"Failed to extract metadata using vision LLM: {e}",
                    details={"file_path": extraction_result.metadata.get("file_path", "unknown")}
                ) from e
        
        elif llm_mode == "multimodal":
            # Send text + images together to vision LLM
            image_pages_bytes = extraction_result.metadata.get("image_pages_bytes", [])
            text_content = extraction_result.raw_text or ""
            
            if not image_pages_bytes and not text_content:
                self.logger.warning("No content found, returning empty schema")
                from ai.schema import SchemaValidator
                validator = SchemaValidator()
                return validator.get_empty_schema()
            
            if image_pages_bytes:
                img_bytes_list = [img_bytes for _, img_bytes in image_pages_bytes]
                self.logger.info(
                    f"Using multimodal extraction: {len(text_content)} chars text, "
                    f"{len(img_bytes_list)} image(s)"
                )
                
                try:
                    metadata = self.gemini_client.extract_metadata_multimodal(
                        text_content,
                        img_bytes_list
                    )
                    return metadata
                except LLMError as e:
                    self.logger.error("Multimodal extraction failed", exc_info=True)
                    raise ExtractionError(
                        f"Failed to extract metadata using multimodal LLM: {e}",
                        details={"file_path": extraction_result.metadata.get("file_path", "unknown")}
                    ) from e
            else:
                # No images, fall back to text-only
                self.logger.warning("Multimodal mode but no images, using text-only")
                try:
                    metadata = self.gemini_client.extract_metadata_from_text(text_content)
                    return metadata
                except LLMError as e:
                    raise ExtractionError(
                        f"Failed to extract metadata: {e}",
                        details={"file_path": extraction_result.metadata.get("file_path", "unknown")}
                    ) from e
        
        elif llm_mode == "dual_llm":
            # Send text to text LLM + images to vision LLM separately, then merge
            text_content = extraction_result.raw_text or ""
            image_pages_bytes = extraction_result.metadata.get("image_pages_bytes", [])
            
            text_metadata = {}
            vision_metadata = {}
            
            # Process text with text LLM
            if text_content:
                try:
                    text_metadata = self.gemini_client.extract_metadata_from_text(text_content)
                    self.logger.info("Text LLM extraction complete")
                except LLMError as e:
                    self.logger.warning(f"Text LLM extraction failed: {e}")
            
            # Process images with vision LLM
            if image_pages_bytes:
                img_bytes_list = [img_bytes for _, img_bytes in image_pages_bytes]
                try:
                    # Process first image (or all - depends on implementation)
                    if img_bytes_list:
                        vision_metadata = self.gemini_client.extract_metadata_from_image(
                            img_bytes_list[0],
                            image_mime_type="image/png"
                        )
                        self.logger.info("Vision LLM extraction complete")
                except LLMError as e:
                    self.logger.warning(f"Vision LLM extraction failed: {e}")
            
            # Merge metadata intelligently (prefer non-empty values, vision over text for conflicts)
            from ai.schema import SchemaValidator
            validator = SchemaValidator()
            merged_metadata = validator.get_empty_schema()
            
            # Start with text metadata
            for category, fields in text_metadata.items():
                if isinstance(fields, dict):
                    for field_name, value in fields.items():
                        if value and value != "Not Found":
                            if category not in merged_metadata:
                                merged_metadata[category] = {}
                            merged_metadata[category][field_name] = value
            
            # Override with vision metadata (vision takes precedence)
            for category, fields in vision_metadata.items():
                if isinstance(fields, dict):
                    for field_name, value in fields.items():
                        if value and value != "Not Found":
                            if category not in merged_metadata:
                                merged_metadata[category] = {}
                            merged_metadata[category][field_name] = value
            
            self.logger.info("Dual LLM extraction complete, results merged")
            return merged_metadata
        
        else:
            # Unknown mode, fall back to text_llm
            self.logger.warning(f"Unknown LLM processing mode: {llm_mode}, using text_llm")
            if not extraction_result.raw_text:
                from ai.schema import SchemaValidator
                validator = SchemaValidator()
                return validator.get_empty_schema()
            
            try:
                metadata = self.gemini_client.extract_metadata_from_text(
                    extraction_result.raw_text
                )
                return metadata
            except LLMError as e:
                raise ExtractionError(
                    f"Failed to extract metadata: {e}",
                    details={"file_path": extraction_result.metadata.get("file_path", "unknown")}
                ) from e

