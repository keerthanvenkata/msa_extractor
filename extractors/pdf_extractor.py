"""
PDF text extraction module.

Handles both text-based and image-based PDFs:
- Text-based: Direct text extraction with PyMuPDF
- Image-based: Convert to images, preprocess, then OCR
"""

import fitz  # PyMuPDF
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image as PILImage
import io
import logging

from .base_extractor import BaseExtractor, ExtractedTextResult
from .image_preprocessor import ImagePreprocessor
from config import (
    PDF_PREPROCESSING_DPI,
    ENABLE_IMAGE_PREPROCESSING,
    ENABLE_DESKEW,
    ENABLE_DENOISE,
    ENABLE_ENHANCE,
    ENABLE_BINARIZE
)

logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractor):
    """Extract text from PDF files (text-based and image-based)."""
    
    def __init__(self, gemini_client=None):
        """
        Initialize PDF extractor.
        
        Args:
            gemini_client: Optional Gemini client for text processing
        """
        super().__init__()
        self.gemini_client = gemini_client
        self.preprocessor = ImagePreprocessor(
            enable_deskew=ENABLE_DESKEW,
            enable_denoise=ENABLE_DENOISE,
            enable_enhance=ENABLE_ENHANCE,
            enable_binarize=ENABLE_BINARIZE
        )
        self._cached_pdf_type = None  # Cache PDF type to avoid re-detection
    
    def extract(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            ExtractedTextResult with extracted text and metadata
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If PDF is invalid or encrypted
        """
        self._log_extraction_start(file_path)
        
        # Validate file
        self.validate_file(file_path)
        
        try:
            # Detect PDF type (use cached value if available)
            if self._cached_pdf_type is not None:
                pdf_type = self._cached_pdf_type
                self.logger.debug(f"Using cached PDF type: {pdf_type}")
            else:
                pdf_type = self._detect_pdf_type(file_path)
                self._cached_pdf_type = pdf_type  # Cache for this instance
            
            if pdf_type == "text":
                # Text-based PDF: extract text directly
                result = self._extract_text_based(file_path)
            elif pdf_type == "image":
                # Image-based PDF: convert to images and preprocess
                result = self._extract_image_based(file_path)
            else:  # mixed
                # Mixed PDF: handle both types
                result = self._extract_mixed(file_path)
            
            self._log_extraction_complete(file_path, result)
            return result
            
        except Exception as e:
            self._log_error(file_path, e)
            raise
    
    def _detect_pdf_type(self, file_path: str) -> str:
        """
        Detect if PDF is text-based, image-based, or mixed.
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            "text", "image", or "mixed"
        """
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            if total_pages == 0:
                doc.close()
                return "image"
            
            text_pages = 0
            min_text_length = 50  # Minimum characters to consider page as text-based
            
            # Sample first few pages and last page
            sample_pages = min(5, total_pages)
            pages_to_check = list(range(sample_pages))
            if total_pages > sample_pages:
                pages_to_check.append(total_pages - 1)  # Check last page too
            
            for page_num in pages_to_check:
                try:
                    page = doc.load_page(page_num)
                    text = page.get_text().strip()
                    
                    if len(text) > min_text_length:
                        text_pages += 1
                except Exception as e:
                    self.logger.warning(f"Error checking page {page_num}: {e}")
            
            doc.close()
            
            # Calculate ratio
            checked_pages = len(pages_to_check)
            text_ratio = text_pages / checked_pages if checked_pages > 0 else 0
            
            # Determine type
            if text_ratio > 0.8:
                return "text"
            elif text_ratio < 0.2:
                return "image"
            else:
                return "mixed"
                
        except Exception as e:
            self.logger.error(f"Error detecting PDF type: {e}")
            # Default to image-based if detection fails
            return "image"
    
    def _extract_text_based(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text from text-based PDF.
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            ExtractedTextResult with extracted text
        """
        doc = fitz.open(file_path)
        
        try:
            # Check if encrypted
            if doc.is_encrypted:
                raise ValueError("PDF is encrypted/password-protected")
            
            # Extract text blocks with metadata
            text_blocks = []
            full_text = []
            page_count = len(doc)
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                
                # Get text with structure
                text_dict = page.get_text("dict")
                
                # Extract text blocks
                for block in text_dict.get("blocks", []):
                    if "lines" in block:
                        block_text = []
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text = span.get("text", "")
                                if text.strip():
                                    block_text.append(text)
                                    full_text.append(text)
                                    
                                    # Store text block with metadata
                                    text_blocks.append({
                                        "text": text,
                                        "font_size": span.get("size", 0),
                                        "font_name": span.get("font", ""),
                                        "is_bold": "bold" in span.get("font", "").lower(),
                                        "is_italic": "italic" in span.get("font", "").lower(),
                                        "page_number": page_num + 1,
                                        "bbox": span.get("bbox", (0, 0, 0, 0))
                                    })
                        
                        # Add line breaks
                        if block_text:
                            full_text.append("\n")
            
            # Combine full text
            raw_text = " ".join(full_text)
            
            # Extract metadata
            metadata = doc.metadata
            
            result = ExtractedTextResult(
                raw_text=raw_text,
                structured_text=text_blocks,
                metadata={
                    "file_type": "pdf",
                    "is_scanned": False,
                    "page_count": page_count,
                    "extraction_method": "text",
                    "extraction_strategy": "pymupdf",
                    "pdf_metadata": metadata
                }
            )
            
            return result
            
        finally:
            doc.close()
    
    def _extract_image_based(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text from image-based PDF (scanned PDF).
        
        Converts PDF pages to images and preprocesses them.
        Note: OCR is handled separately by OCR handler.
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            ExtractedTextResult with preprocessed images (ready for OCR)
        """
        doc = fitz.open(file_path)
        
        try:
            if doc.is_encrypted:
                raise ValueError("PDF is encrypted/password-protected")
            
            page_count = len(doc)
            preprocessed_images = []
            
            # Convert each page to image and preprocess
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                
                # Render page as image
                mat = fitz.Matrix(PDF_PREPROCESSING_DPI / 72, PDF_PREPROCESSING_DPI / 72)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to numpy array
                img_data = pix.tobytes("ppm")
                pil_img = PILImage.open(io.BytesIO(img_data))
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                
                # Preprocess image if enabled
                if ENABLE_IMAGE_PREPROCESSING:
                    cv_img = self.preprocessor.preprocess(cv_img)
                
                preprocessed_images.append(cv_img)
            
            # Store images for OCR processing
            # Note: OCR will be handled by OCR handler
            result = ExtractedTextResult(
                raw_text="",  # Will be filled by OCR
                structured_text=[],
                metadata={
                    "file_type": "pdf",
                    "is_scanned": True,
                    "page_count": page_count,
                    "extraction_method": "ocr",
                    "extraction_strategy": "image_preprocessing",
                    "preprocessed_images": preprocessed_images,  # Store for OCR
                    "dpi": PDF_PREPROCESSING_DPI
                }
            )
            
            return result
            
        finally:
            doc.close()
    
    def _extract_mixed(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text from mixed PDF (some pages text, some images).
        
        Handles documents where most pages are text-based but some pages (typically
        signature pages at the end) are image-based. Extracts text from text pages
        and OCRs image pages, then combines both.
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            ExtractedTextResult with extracted text from both text and image pages
        """
        doc = fitz.open(file_path)
        
        try:
            if doc.is_encrypted:
                raise ValueError("PDF is encrypted/password-protected")
            
            page_count = len(doc)
            text_pages_text = []
            image_pages = []
            text_blocks = []
            min_text_length = 50  # Minimum characters to consider page as text-based
            
            # Process each page individually
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                
                # Try to extract text
                text = page.get_text().strip()
                
                if len(text) > min_text_length:
                    # Text-based page: extract text with structure
                    text_dict = page.get_text("dict")
                    
                    for block in text_dict.get("blocks", []):
                        if "lines" in block:
                            for line in block.get("lines", []):
                                for span in line.get("spans", []):
                                    span_text = span.get("text", "")
                                    if span_text.strip():
                                        text_pages_text.append(span_text)
                                        text_blocks.append({
                                            "text": span_text,
                                            "font_size": span.get("size", 0),
                                            "font_name": span.get("font", ""),
                                            "is_bold": "bold" in span.get("font", "").lower(),
                                            "is_italic": "italic" in span.get("font", "").lower(),
                                            "page_number": page_num + 1,
                                            "bbox": span.get("bbox", (0, 0, 0, 0))
                                        })
                    
                    # Add line break after page
                    if text_pages_text:
                        text_pages_text.append("\n")
                else:
                    # Image-based page: convert to image for OCR
                    self.logger.info(f"Page {page_num + 1} detected as image-based, will OCR")
                    
                    # Convert page to image
                    mat = fitz.Matrix(PDF_PREPROCESSING_DPI / 72, PDF_PREPROCESSING_DPI / 72)
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to numpy array
                    img_data = pix.tobytes("ppm")
                    pil_img = PILImage.open(io.BytesIO(img_data))
                    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    
                    # Preprocess if enabled
                    if ENABLE_IMAGE_PREPROCESSING:
                        cv_img = self.preprocessor.preprocess(cv_img)
                    
                    image_pages.append((page_num + 1, cv_img))
            
            # Extract metadata before closing
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            doc.close()
            
            # OCR image-based pages if any
            ocr_texts = []
            if image_pages:
                from .ocr_handler import OCRHandler
                from config import OCR_ENGINE
                
                self.logger.info(f"OCR'ing {len(image_pages)} image-based page(s)")
                ocr_handler = OCRHandler(ocr_engine=OCR_ENGINE)
                
                # Extract images (just the numpy arrays)
                images = [img for _, img in image_pages]
                ocr_texts = ocr_handler.extract_text_from_images(images)
                
                # Add OCR text with page markers
                for i, (page_num, _) in enumerate(image_pages):
                    if i < len(ocr_texts) and ocr_texts[i]:
                        text_pages_text.append(f"\n[Page {page_num} - OCR Text]\n")
                        text_pages_text.append(ocr_texts[i])
                        text_pages_text.append("\n")
            
            # Extract metadata before closing
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            doc.close()
            
            # Combine all text
            raw_text = " ".join(text_pages_text) if text_pages_text else ""
            
            result = ExtractedTextResult(
                raw_text=raw_text,
                structured_text=text_blocks,
                metadata={
                    "file_type": "pdf",
                    "is_scanned": len(image_pages) > 0,
                    "page_count": page_count,
                    "text_pages": page_count - len(image_pages),
                    "image_pages": len(image_pages),
                    "image_page_numbers": [page_num for page_num, _ in image_pages],
                    "extraction_method": "mixed",
                    "extraction_strategy": "pymupdf_with_ocr",
                    "pdf_metadata": metadata
                }
            )
            
            self.logger.info(
                f"Mixed PDF extraction complete: {page_count - len(image_pages)} text pages, "
                f"{len(image_pages)} image pages (pages {[p for p, _ in image_pages]})"
            )
            
            return result
            
        except Exception as e:
            doc.close()
            raise
    
    def pdf_to_images(self, file_path: str, dpi: int = None) -> List[np.ndarray]:
        """
        Convert PDF pages to images.
        
        Args:
            file_path: Path to PDF file
            dpi: Resolution for rendering (defaults to config value)
        
        Returns:
            List of preprocessed images as numpy arrays
        """
        if dpi is None:
            dpi = PDF_PREPROCESSING_DPI
        
        doc = fitz.open(file_path)
        images = []
        
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Render page as image
                mat = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to numpy array
                img_data = pix.tobytes("ppm")
                pil_img = PILImage.open(io.BytesIO(img_data))
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                
                # Preprocess if enabled
                if ENABLE_IMAGE_PREPROCESSING:
                    cv_img = self.preprocessor.preprocess(cv_img)
                
                images.append(cv_img)
            
            return images
            
        finally:
            doc.close()

