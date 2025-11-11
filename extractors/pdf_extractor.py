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

from .base_extractor import BaseExtractor, ExtractedTextResult
from .image_preprocessor import ImagePreprocessor
from utils.logger import get_logger
from utils.exceptions import FileError, ExtractionError
from config import (
    PDF_PREPROCESSING_DPI,
    ENABLE_IMAGE_PREPROCESSING,
    ENABLE_DESKEW,
    ENABLE_DENOISE,
    ENABLE_ENHANCE,
    ENABLE_BINARIZE,
    EXTRACTION_MODE
)

logger = get_logger(__name__)


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
                # However, if multimodal mode is enabled, check for image pages
                # (especially signature pages at the end that might be missed)
                if EXTRACTION_MODE == "multimodal" and self._has_image_pages(file_path):
                    self.logger.info(
                        "PDF detected as text but has image pages. Using mixed extraction for multimodal mode."
                    )
                    result = self._extract_mixed(file_path)
                else:
                    result = self._extract_text_based(file_path)
            elif pdf_type == "image":
                # Image-based PDF: convert to images and preprocess
                result = self._extract_image_based(file_path)
            else:  # mixed
                # Mixed PDF: handle both types
                result = self._extract_mixed(file_path)
            
            self._log_extraction_complete(file_path, result)
            return result
            
        except (FileError, ExtractionError):
            # Re-raise custom exceptions
            raise
        except Exception as e:
            self._log_error(file_path, e)
            raise ExtractionError(
                f"Failed to extract from PDF: {e}",
                details={"file_path": file_path}
            ) from e
    
    def _detect_pdf_type(self, file_path: str) -> str:
        """
        Detect if PDF is text-based, image-based, or mixed.
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            "text", "image", or "mixed"
        """
        doc = None
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            if total_pages == 0:
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
        finally:
            # Ensure document is always closed, even if exception occurs
            if doc is not None:
                doc.close()
    
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
                raise FileError(
                    "PDF is encrypted/password-protected",
                    details={"file_path": file_path}
                )
            
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
                raise FileError(
                    "PDF is encrypted/password-protected",
                    details={"file_path": file_path}
                )
            
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
    
    def _has_image_pages(self, file_path: str) -> bool:
        """
        Check if PDF has any image-based pages (especially useful for detecting
        signature pages at the end that might be missed by type detection).
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            True if any image pages are found
        """
        doc = None
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            min_text_length = 50
            
            # Check last 2 pages (where signatures typically are)
            pages_to_check = []
            if total_pages >= 2:
                pages_to_check = [total_pages - 2, total_pages - 1]
            elif total_pages == 1:
                pages_to_check = [0]
            
            for page_num in pages_to_check:
                try:
                    page = doc.load_page(page_num)
                    text = page.get_text().strip()
                    
                    # If page has very little text, it's likely an image page
                    if len(text) < min_text_length:
                        return True
                except Exception:
                    # If we can't read the page, assume it might be an image
                    return True
            
            return False
        except Exception as e:
            self.logger.warning(f"Error checking for image pages: {e}")
            return False
        finally:
            if doc is not None:
                doc.close()
    
    def _is_signature_page(self, page, page_num: int, total_pages: int) -> bool:
        """
        Detect if a page is likely a signature page.
        
        Heuristics:
        - Last page or last few pages
        - Low text content
        - Keywords like "signature", "sign", "date", "authorized"
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-indexed)
            total_pages: Total number of pages
        
        Returns:
            True if likely a signature page
        """
        # Check if it's one of the last 2 pages
        is_last_pages = (page_num + 1) >= (total_pages - 1)
        
        # Get text and check for signature-related keywords
        text = page.get_text().lower()
        signature_keywords = ["signature", "sign", "signed", "date", "authorized", 
                            "signatory", "witness", "notary"]
        has_signature_keywords = any(keyword in text for keyword in signature_keywords)
        
        # Low text content (less than 100 chars) suggests image-based signature page
        low_text = len(text.strip()) < 100
        
        return is_last_pages and (has_signature_keywords or low_text)
    
    def _extract_mixed(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text from mixed PDF (some pages text, some images).
        
        Handles documents where most pages are text-based but some pages (typically
        signature pages at the end) are image-based. Supports different extraction modes:
        - text_only: Extract text only, ignore image pages
        - image_only: Extract from images only (OCR or vision)
        - text_ocr: Extract text + OCR text from image pages (default)
        - text_image: Extract text + send image pages directly to vision model
        - multimodal: Send text + images together to vision model (best for signatory pages)
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            ExtractedTextResult with extracted text from both text and image pages
        """
        doc = fitz.open(file_path)
        
        try:
            if doc.is_encrypted:
                raise FileError(
                    "PDF is encrypted/password-protected",
                    details={"file_path": file_path}
                )
            
            page_count = len(doc)
            text_pages_text = []
            image_pages = []  # List of (page_num, cv_img) tuples
            image_pages_bytes = []  # List of (page_num, img_bytes) tuples for multimodal
            text_blocks = []
            min_text_length = 50  # Minimum characters to consider page as text-based
            
            # Process each page individually
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                
                # Try to extract text
                text = page.get_text().strip()
                
                if len(text) > min_text_length:
                    # Text-based page: extract text with structure
                    if EXTRACTION_MODE != "image_only":
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
                    # Image-based page: convert to image
                    is_signature = self._is_signature_page(page, page_num, page_count)
                    page_type = "signature" if is_signature else "image"
                    self.logger.info(
                        f"Page {page_num + 1} detected as {page_type}-based page"
                    )
                    
                    # Convert page to image
                    mat = fitz.Matrix(PDF_PREPROCESSING_DPI / 72, PDF_PREPROCESSING_DPI / 72)
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to bytes for multimodal mode
                    img_bytes = pix.tobytes("png")
                    image_pages_bytes.append((page_num + 1, img_bytes))
                    
                    # Convert to numpy array for OCR mode
                    img_data = pix.tobytes("ppm")
                    pil_img = PILImage.open(io.BytesIO(img_data))
                    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    
                    # Preprocess if enabled
                    if ENABLE_IMAGE_PREPROCESSING:
                        cv_img = self.preprocessor.preprocess(cv_img)
                    
                    image_pages.append((page_num + 1, cv_img))
            
            # Extract metadata before closing
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            # Handle different extraction modes
            raw_text = ""
            extraction_strategy = "pymupdf_with_ocr"
            
            if EXTRACTION_MODE == "text_only":
                # Extract text only, ignore image pages
                raw_text = " ".join(text_pages_text) if text_pages_text else ""
                extraction_strategy = "pymupdf_text_only"
                self.logger.info(f"Ignoring {len(image_pages)} image page(s) (text_only mode)")
                
            elif EXTRACTION_MODE == "image_only":
                # Extract from images only (OCR or vision)
                from .ocr_handler import OCRHandler
                from config import OCR_ENGINE
                
                if image_pages:
                    self.logger.info(f"OCR'ing {len(image_pages)} image-based page(s)")
                    ocr_handler = OCRHandler(ocr_engine=OCR_ENGINE)
                    images = [img for _, img in image_pages]
                    ocr_texts = ocr_handler.extract_text_from_images(images)
                    raw_text = "\n\n".join(ocr_texts)
                    extraction_strategy = f"ocr_{OCR_ENGINE}"
                else:
                    raw_text = ""
                    self.logger.warning("No image pages found for image_only mode")
                    
            elif EXTRACTION_MODE == "text_ocr":
                # Extract text + OCR text from image pages (default)
                raw_text = " ".join(text_pages_text) if text_pages_text else ""
                
                if image_pages:
                    from .ocr_handler import OCRHandler
                    from config import OCR_ENGINE
                    
                    self.logger.info(f"OCR'ing {len(image_pages)} image-based page(s)")
                    ocr_handler = OCRHandler(ocr_engine=OCR_ENGINE)
                    images = [img for _, img in image_pages]
                    ocr_texts = ocr_handler.extract_text_from_images(images)
                    
                    # Add OCR text with page markers
                    for i, (page_num, _) in enumerate(image_pages):
                        if i < len(ocr_texts) and ocr_texts[i]:
                            raw_text += f"\n[Page {page_num} - OCR Text]\n"
                            raw_text += ocr_texts[i]
                            raw_text += "\n"
                    
                    extraction_strategy = "pymupdf_with_ocr"
                    
            elif EXTRACTION_MODE == "multimodal":
                # Send text + images together to vision model (best for signatory pages)
                if not self.gemini_client:
                    raise ExtractionError(
                        "Gemini client required for multimodal extraction mode",
                        details={"file_path": file_path}
                    )
                
                # Combine text from text pages
                text_content = " ".join(text_pages_text) if text_pages_text else ""
                
                # Get image bytes for multimodal input
                img_bytes_list = [img_bytes for _, img_bytes in image_pages_bytes]
                
                if img_bytes_list:
                    self.logger.info(
                        f"Multimodal extraction: {len(text_content)} chars text, "
                        f"{len(img_bytes_list)} image(s)"
                    )
                    # Store for later use in extraction coordinator
                    # The actual multimodal extraction will be done in the coordinator
                    raw_text = text_content
                    extraction_strategy = "multimodal"
                else:
                    # No image pages, just use text
                    raw_text = text_content
                    extraction_strategy = "pymupdf_text_only"
                    self.logger.info("No image pages, using text-only extraction")
                    
            else:  # text_image mode (default fallback to text_ocr)
                # Extract text + send image pages directly to vision model
                raw_text = " ".join(text_pages_text) if text_pages_text else ""
                extraction_strategy = "pymupdf_with_ocr"
                self.logger.warning(
                    f"Unknown extraction mode '{EXTRACTION_MODE}', using text_ocr"
                )
            
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
                    "extraction_strategy": extraction_strategy,
                    "extraction_mode": EXTRACTION_MODE,
                    "pdf_metadata": metadata,
                    # Store image bytes for multimodal mode
                    "image_pages_bytes": image_pages_bytes if EXTRACTION_MODE == "multimodal" else None
                }
            )
            
            self.logger.info(
                f"Mixed PDF extraction complete ({EXTRACTION_MODE}): "
                f"{page_count - len(image_pages)} text pages, "
                f"{len(image_pages)} image pages (pages {[p for p, _ in image_pages]})"
            )
            
            return result
            
        finally:
            # Ensure document is always closed, even if exception occurs
            if 'doc' in locals() and doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass  # Ignore errors when closing already-closed document
    
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

