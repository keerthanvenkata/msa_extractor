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
    
    def extract_metadata(
        self, 
        file_path: str, 
        strategy: str = None,
        extraction_method: Optional[str] = None,
        llm_processing_mode: Optional[str] = None,
        ocr_engine: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract metadata from document using full pipeline.
        
        This is the main entry point that:
        1. Extracts text from document (PDF/DOCX)
        2. Handles OCR if needed (for scanned PDFs)
        3. Processes extracted text with Gemini to extract metadata
        4. Returns structured metadata matching schema
        
        Args:
            file_path: Path to document file
            strategy: Extraction strategy (deprecated, use extraction_method instead)
            extraction_method: Override extraction method (defaults to config value)
            llm_processing_mode: Override LLM processing mode (defaults to config value)
            ocr_engine: Override OCR engine (defaults to config value)
        
        Returns:
            Dictionary with extracted metadata matching schema
        """
        self.logger.info(f"Starting metadata extraction for: {file_path}")
        
        # Use provided overrides or fall back to config
        extraction_method_used = extraction_method or EXTRACTION_METHOD
        llm_mode_used = llm_processing_mode or LLM_PROCESSING_MODE
        ocr_engine_used = ocr_engine or OCR_ENGINE
        
        # Step 1: Extract text from document
        extraction_result = self._extract_text(
            file_path, 
            strategy,
            extraction_method=extraction_method_used,
            ocr_engine=ocr_engine_used
        )
        
        # Step 2: Process with LLM using override or result metadata or config
        llm_mode = (
            llm_mode_used or 
            extraction_result.metadata.get("llm_processing_mode") or 
            LLM_PROCESSING_MODE
        )
        metadata = self._process_with_llm(extraction_result, llm_mode)
        
        return metadata
    
    def _extract_text(
        self, 
        file_path: str, 
        strategy: str = None,
        extraction_method: Optional[str] = None,
        ocr_engine: Optional[str] = None
    ) -> ExtractedTextResult:
        """
        Extract text from document.
        
        Args:
            file_path: Path to document file
            strategy: Extraction strategy (deprecated)
            extraction_method: Override extraction method
            ocr_engine: Override OCR engine
        
        Returns:
            ExtractedTextResult with text
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == ".pdf":
            return self._extract_from_pdf(file_path, strategy, extraction_method, ocr_engine)
        elif file_ext == ".docx":
            return self._extract_from_docx(file_path)
        else:
            raise FileError(
                f"Unsupported file type: {file_ext}",
                details={"file_path": file_path, "file_extension": file_ext}
            )
    
    def _extract_from_pdf(
        self, 
        file_path: str, 
        strategy: str = None,
        extraction_method: Optional[str] = None,
        ocr_engine: Optional[str] = None
    ) -> ExtractedTextResult:
        """
        Extract text from PDF.
        
        Args:
            file_path: Path to PDF file
            strategy: Extraction strategy (deprecated)
            extraction_method: Override extraction method
            ocr_engine: Override OCR engine
        
        Returns:
            ExtractedTextResult with text
        """
        extractor = self.strategy_factory.get_extractor(file_path, strategy)
        result = extractor.extract(file_path)
        
        # Use provided extraction_method or get from result metadata or config
        extraction_method_used = (
            extraction_method or 
            result.metadata.get("extraction_method") or 
            EXTRACTION_METHOD
        )
        
        # Update result metadata with the extraction method used
        result.metadata["extraction_method"] = extraction_method_used
        
        # Run OCR if extraction method requires it
        preprocessed_images = result.metadata.get("preprocessed_images")
        
        if preprocessed_images and extraction_method_used in ["ocr_all", "ocr_images_only"]:
            # Use provided OCR engine or config default
            ocr_engine_used = ocr_engine or OCR_ENGINE
            
            # Run OCR on preprocessed images
            ocr_handler = OCRHandler(ocr_engine=ocr_engine_used)
            ocr_texts = ocr_handler.extract_text_from_images(preprocessed_images)
            
            # Combine with existing text (for ocr_images_only)
            if extraction_method_used == "ocr_images_only" and result.raw_text:
                result.raw_text += "\n\n" + "\n\n".join(ocr_texts)
            else:
                result.raw_text = "\n\n".join(ocr_texts)
            
            result.metadata["ocr_engine"] = ocr_engine_used
            
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
        - multimodal: Send text + images together to vision LLM (default)
        - text_llm: Send text to text LLM
        - vision_llm: Send images to vision LLM
        - dual_llm: Send text to text LLM + images to vision LLM separately, then merge
        
        Args:
            extraction_result: Result from content extraction
            llm_mode: LLM processing mode (defaults to config)
        
        Returns:
            Dictionary with extracted metadata
        """
        llm_mode = llm_mode or LLM_PROCESSING_MODE
        
        if llm_mode == "text_llm":
            # Send text to text LLM (images are ignored in this mode)
            image_pages_bytes = extraction_result.metadata.get("image_pages_bytes", [])
            if image_pages_bytes:
                self.logger.warning(
                    f"text_llm mode: {len(image_pages_bytes)} image page(s) detected but will be ignored. "
                    f"Only text will be sent to text LLM. Consider using 'multimodal' or 'dual_llm' mode "
                    f"if image pages contain important information (e.g., signatures)."
                )
            
            if not extraction_result.raw_text:
                self.logger.warning(
                    "No text extracted for text_llm mode. If document has image pages, "
                    "consider using 'multimodal' or 'vision_llm' mode instead."
                )
                from ai.schema import SchemaValidator
                validator = SchemaValidator()
                return validator.get_empty_schema()
            
            # Validate text length (text LLM has limits)
            text_length = len(extraction_result.raw_text)
            max_text_length = 50000  # Approximate limit for text LLM
            if text_length > max_text_length:
                self.logger.warning(
                    f"Text length ({text_length} chars) exceeds recommended limit ({max_text_length} chars). "
                    f"Text will be truncated or may cause API errors. Consider using 'multimodal' mode instead."
                )
            
            try:
                metadata = self.gemini_client.extract_metadata_from_text(
                    extraction_result.raw_text
                )
                return metadata
            except LLMError as e:
                error_msg = str(e)
                # Provide helpful error message if images are available
                if image_pages_bytes:
                    self.logger.error(
                        f"Text LLM extraction failed. Document has {len(image_pages_bytes)} image page(s) "
                        f"that were not processed. Consider using 'multimodal' or 'dual_llm' mode instead.",
                        exc_info=True
                    )
                else:
                    self.logger.error("Text LLM extraction failed", exc_info=True)
                
                raise ExtractionError(
                    f"Failed to extract metadata using text LLM: {e}",
                    details={
                        "file_path": extraction_result.metadata.get("file_path", "unknown"),
                        "text_length": text_length,
                        "has_image_pages": len(image_pages_bytes) > 0,
                        "suggestion": "Try 'multimodal' or 'dual_llm' mode if document has image pages"
                    }
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

