"""
Gemini Vision extractor for direct image-based extraction.

Uses Gemini Vision API to extract text and metadata directly from PDF pages/images.
"""

import fitz  # PyMuPDF
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image as PILImage
import io

from .base_extractor import BaseExtractor, ExtractedTextResult
from utils.logger import get_logger
from utils.exceptions import FileError, ExtractionError, LLMError
from config import PDF_PREPROCESSING_DPI, GEMINI_VISION_MODEL

logger = get_logger(__name__)


class GeminiVisionExtractor(BaseExtractor):
    """Extract text and metadata directly from images using Gemini Vision API."""
    
    def __init__(self, gemini_client=None):
        """
        Initialize Gemini Vision extractor.
        
        Args:
            gemini_client: Optional Gemini client (will be created if needed)
        """
        super().__init__()
        self.gemini_client = gemini_client
        if not self.gemini_client:
            try:
                from ai.gemini_client import GeminiClient
                self.gemini_client = GeminiClient()
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")
                raise
    
    def extract(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text and metadata from PDF using Gemini Vision.
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            ExtractedTextResult with extracted text and metadata
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If PDF is invalid
        """
        self._log_extraction_start(file_path)
        
        # Validate file
        self.validate_file(file_path)
        
        try:
            doc = fitz.open(file_path)
            
            if doc.is_encrypted:
                raise FileError(
                    "PDF is encrypted/password-protected",
                    details={"file_path": file_path}
                )
            
            page_count = len(doc)
            all_text = []
            all_metadata = []
            
            # Process each page
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                
                # Convert page to image
                mat = fitz.Matrix(PDF_PREPROCESSING_DPI / 72, PDF_PREPROCESSING_DPI / 72)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to bytes
                img_data = pix.tobytes("png")
                
                # Extract metadata from image using Gemini Vision
                # Extract metadata from first 3 pages (cover + first 2 content pages)
                # to catch metadata that might be on later pages (e.g., signature pages)
                if page_num < 3:
                    # Extract metadata from first 3 pages
                    metadata = self.gemini_client.extract_metadata_from_image(
                        img_data, 
                        image_mime_type="image/png"
                    )
                else:
                    # For subsequent pages, just extract text
                    metadata = {}
                
                # For text extraction, we can also get raw text
                # Note: Gemini Vision can extract text, but for full document text
                # we might want to combine all pages
                all_metadata.append(metadata)
                
                # Extract text from image (for raw text)
                # We'll use a simpler prompt for text extraction
                text = self._extract_text_from_image(img_data)
                if text:
                    all_text.append(text)
            
            # Combine results - merge metadata from first 3 pages intelligently
            # Prefer non-empty values, with later pages taking precedence for conflicts
            combined_metadata = {}
            if all_metadata:
                from ai.schema import SchemaValidator
                validator = SchemaValidator()
                
                # Start with empty schema
                combined_metadata = validator.get_empty_schema()
                
                # Merge metadata from all pages (first 3 pages)
                # Later pages override earlier ones for the same field
                for page_metadata in all_metadata:
                    if page_metadata:
                        for category, fields in page_metadata.items():
                            if isinstance(fields, dict):
                                for field_name, value in fields.items():
                                    # Only update if value is not empty and not "Not Found"
                                    if value and value != "Not Found":
                                        if category not in combined_metadata:
                                            combined_metadata[category] = {}
                                        combined_metadata[category][field_name] = value
            
            # Combine text from all pages
            raw_text = "\n\n".join(all_text)
            
            result = ExtractedTextResult(
                raw_text=raw_text,
                structured_text=[],
                headers=[],
                metadata={
                    "file_type": "pdf",
                    "is_scanned": True,
                    "page_count": page_count,
                    "extraction_method": "gemini_vision",
                    "extraction_strategy": "gemini_vision",
                    "extracted_metadata": combined_metadata
                }
            )
            
            self._log_extraction_complete(file_path, result)
            return result
            
        except Exception as e:
            self._log_error(file_path, e)
            raise
        finally:
            # Ensure document is always closed, even if exception occurs
            if 'doc' in locals() and doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass  # Ignore errors when closing already-closed document
    
    def _extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Extract raw text from image using Gemini Vision.
        
        Args:
            image_bytes: Image data as bytes
        
        Returns:
            Extracted text
        """
        try:
            import google.generativeai as genai
            from config import GEMINI_VISION_MODEL
            
            model = genai.GenerativeModel(GEMINI_VISION_MODEL)
            
            response = model.generate_content([
                "Extract all text from this image. Return only the text, no formatting or analysis.",
                {
                    "mime_type": "image/png",
                    "data": image_bytes
                }
            ])
            
            return response.text.strip() if response.text else ""
            
        except Exception as e:
            self.logger.warning(f"Error extracting text from image: {e}")
            return ""

