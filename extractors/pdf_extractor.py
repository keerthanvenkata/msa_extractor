"""
PDF text extraction module - Redesigned Architecture.

Handles PDFs with new extraction method and LLM processing mode system:
- EXTRACTION_METHOD: How to extract content (text_direct, ocr_all, ocr_images_only, vision_all, hybrid)
- LLM_PROCESSING_MODE: How to process with LLM (text_llm, vision_llm, multimodal, dual_llm)
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
    EXTRACTION_METHOD,
    LLM_PROCESSING_MODE,
    OCR_ENGINE
)

logger = get_logger(__name__)


class PDFExtractor(BaseExtractor):
    """
    Extract content from PDF files using new extraction architecture.
    
    Supports:
    - Text pages: Direct text extraction
    - Image-with-text pages: OCR extraction
    - Pure image pages: Image conversion
    - Any combination of the above
    """
    
    def __init__(self, gemini_client=None):
        """
        Initialize PDF extractor.
        
        Args:
            gemini_client: Optional Gemini client (needed for vision/multimodal modes)
        """
        super().__init__()
        self.gemini_client = gemini_client
        self.preprocessor = ImagePreprocessor(
            enable_deskew=ENABLE_DESKEW,
            enable_denoise=ENABLE_DENOISE,
            enable_enhance=ENABLE_ENHANCE,
            enable_binarize=ENABLE_BINARIZE
        )
        self._cached_pdf_type = None
    
    def extract(self, file_path: str) -> ExtractedTextResult:
        """
        Extract content from PDF based on EXTRACTION_METHOD.
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            ExtractedTextResult with content ready for LLM processing
        """
        self._log_extraction_start(file_path)
        self.validate_file(file_path)
        
        # Route to appropriate extraction method
        if EXTRACTION_METHOD == "text_direct":
            return self._extract_text_direct(file_path)
        elif EXTRACTION_METHOD == "ocr_all":
            return self._extract_ocr_all(file_path)
        elif EXTRACTION_METHOD == "ocr_images_only":
            return self._extract_ocr_images_only(file_path)
        elif EXTRACTION_METHOD == "vision_all":
            return self._extract_vision_all(file_path)
        elif EXTRACTION_METHOD == "hybrid":
            return self._extract_hybrid(file_path)
        else:
            raise ExtractionError(
                f"Unknown extraction method: {EXTRACTION_METHOD}",
                details={"file_path": file_path, "method": EXTRACTION_METHOD}
            )
    
    def _extract_text_direct(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text directly from text pages, ignore image pages.
        
        EXTRACTION_METHOD=text_direct
        """
        doc = fitz.open(file_path)
        try:
            if doc.is_encrypted:
                raise FileError("PDF is encrypted", details={"file_path": file_path})
            
            page_count = len(doc)
            text_blocks = []
            all_text = []
            min_text_length = 50
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                text = page.get_text().strip()
                
                if len(text) > min_text_length:
                    # Text page: extract structured text
                    text_dict = page.get_text("dict")
                    for block in text_dict.get("blocks", []):
                        if "lines" in block:
                            for line in block.get("lines", []):
                                for span in line.get("spans", []):
                                    span_text = span.get("text", "")
                                    if span_text.strip():
                                        all_text.append(span_text)
                                        text_blocks.append({
                                            "text": span_text,
                                            "font_size": span.get("size", 0),
                                            "page_number": page_num + 1
                                        })
                    all_text.append("\n")
            
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            return ExtractedTextResult(
                raw_text=" ".join(all_text),
                structured_text=text_blocks,
                metadata={
                    "file_type": "pdf",
                    "is_scanned": False,
                    "page_count": page_count,
                    "extraction_method": "text_direct",
                    "llm_processing_mode": LLM_PROCESSING_MODE,
                    "pdf_metadata": metadata
                }
            )
        finally:
            doc.close()
    
    def _extract_ocr_all(self, file_path: str) -> ExtractedTextResult:
        """
        Convert all pages to images and run OCR on all pages.
        
        EXTRACTION_METHOD=ocr_all
        OCR_ENGINE determines which OCR to use (tesseract/gcv)
        """
        doc = fitz.open(file_path)
        try:
            if doc.is_encrypted:
                raise FileError("PDF is encrypted", details={"file_path": file_path})
            
            page_count = len(doc)
            preprocessed_images = []
            
            # Convert all pages to images
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                mat = fitz.Matrix(PDF_PREPROCESSING_DPI / 72, PDF_PREPROCESSING_DPI / 72)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to numpy array for OCR
                img_data = pix.tobytes("ppm")
                pil_img = PILImage.open(io.BytesIO(img_data))
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                
                # Preprocess if enabled
                if ENABLE_IMAGE_PREPROCESSING:
                    cv_img = self.preprocessor.preprocess(cv_img)
                
                preprocessed_images.append(cv_img)
            
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            return ExtractedTextResult(
                raw_text="",  # Will be filled by OCR handler
                structured_text=[],
                metadata={
                    "file_type": "pdf",
                    "is_scanned": True,
                    "page_count": page_count,
                    "extraction_method": "ocr_all",
                    "llm_processing_mode": LLM_PROCESSING_MODE,
                    "preprocessed_images": preprocessed_images,
                    "ocr_engine": OCR_ENGINE,
                    "pdf_metadata": metadata,
                    "dpi": PDF_PREPROCESSING_DPI
                }
            )
        finally:
            doc.close()
    
    def _extract_ocr_images_only(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text from text pages + OCR only image pages.
        
        EXTRACTION_METHOD=ocr_images_only
        """
        doc = fitz.open(file_path)
        try:
            if doc.is_encrypted:
                raise FileError("PDF is encrypted", details={"file_path": file_path})
            
            page_count = len(doc)
            text_pages_text = []
            text_blocks = []
            image_pages = []  # For OCR
            min_text_length = 50
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                text = page.get_text().strip()
                
                if len(text) > min_text_length:
                    # Text page: extract text directly
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
                                            "page_number": page_num + 1
                                        })
                    text_pages_text.append("\n")
                else:
                    # Image page: convert to image for OCR
                    mat = fitz.Matrix(PDF_PREPROCESSING_DPI / 72, PDF_PREPROCESSING_DPI / 72)
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("ppm")
                    pil_img = PILImage.open(io.BytesIO(img_data))
                    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    
                    if ENABLE_IMAGE_PREPROCESSING:
                        cv_img = self.preprocessor.preprocess(cv_img)
                    
                    image_pages.append((page_num + 1, cv_img))
            
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            # Combine text from text pages
            raw_text = " ".join(text_pages_text) if text_pages_text else ""
            
            return ExtractedTextResult(
                raw_text=raw_text,
                structured_text=text_blocks,
                metadata={
                    "file_type": "pdf",
                    "is_scanned": len(image_pages) > 0,
                    "page_count": page_count,
                    "extraction_method": "ocr_images_only",
                    "llm_processing_mode": LLM_PROCESSING_MODE,
                    "preprocessed_images": [img for _, img in image_pages],
                    "ocr_engine": OCR_ENGINE,
                    "image_page_numbers": [pnum for pnum, _ in image_pages],
                    "pdf_metadata": metadata,
                    "dpi": PDF_PREPROCESSING_DPI
                }
            )
        finally:
            doc.close()
    
    def _extract_vision_all(self, file_path: str) -> ExtractedTextResult:
        """
        Convert all pages to images (no OCR, for vision LLM).
        
        EXTRACTION_METHOD=vision_all
        All pages converted to images, sent to vision LLM
        """
        doc = fitz.open(file_path)
        try:
            if doc.is_encrypted:
                raise FileError("PDF is encrypted", details={"file_path": file_path})
            
            page_count = len(doc)
            image_pages_bytes = []  # List of (page_num, img_bytes)
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                mat = fitz.Matrix(PDF_PREPROCESSING_DPI / 72, PDF_PREPROCESSING_DPI / 72)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                image_pages_bytes.append((page_num + 1, img_bytes))
            
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            return ExtractedTextResult(
                raw_text="",  # No text for vision_all
                structured_text=[],
                metadata={
                    "file_type": "pdf",
                    "is_scanned": True,
                    "page_count": page_count,
                    "extraction_method": "vision_all",
                    "llm_processing_mode": LLM_PROCESSING_MODE,
                    "image_pages_bytes": image_pages_bytes,
                    "pdf_metadata": metadata,
                    "dpi": PDF_PREPROCESSING_DPI
                }
            )
        finally:
            doc.close()
    
    def _extract_hybrid(self, file_path: str) -> ExtractedTextResult:
        """
        Extract text from text pages + convert image pages to images.
        Flexible: content prepared based on LLM_PROCESSING_MODE.
        
        EXTRACTION_METHOD=hybrid
        - If LLM_PROCESSING_MODE=text_llm: Extract text + OCR images
        - If LLM_PROCESSING_MODE=vision_llm: Convert all to images
        - If LLM_PROCESSING_MODE=multimodal: Extract text + convert images (send together)
        - If LLM_PROCESSING_MODE=dual_llm: Extract text + convert images (send separately)
        """
        doc = fitz.open(file_path)
        try:
            if doc.is_encrypted:
                raise FileError("PDF is encrypted", details={"file_path": file_path})
            
            page_count = len(doc)
            text_pages_text = []
            text_blocks = []
            image_pages = []  # For OCR (if text_llm)
            image_pages_bytes = []  # For vision/multimodal
            min_text_length = 50
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                text = page.get_text().strip()
                
                if len(text) > min_text_length:
                    # Text page
                    if LLM_PROCESSING_MODE == "vision_llm":
                        # Convert even text pages to images for vision_llm
                        mat = fitz.Matrix(PDF_PREPROCESSING_DPI / 72, PDF_PREPROCESSING_DPI / 72)
                        pix = page.get_pixmap(matrix=mat)
                        img_bytes = pix.tobytes("png")
                        image_pages_bytes.append((page_num + 1, img_bytes))
                    else:
                        # Extract text directly
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
                                                "page_number": page_num + 1
                                            })
                        text_pages_text.append("\n")
                else:
                    # Image page: convert to image
                    mat = fitz.Matrix(PDF_PREPROCESSING_DPI / 72, PDF_PREPROCESSING_DPI / 72)
                    pix = page.get_pixmap(matrix=mat)
                    img_bytes = pix.tobytes("png")
                    image_pages_bytes.append((page_num + 1, img_bytes))
                    
                    # Also prepare for OCR if text_llm mode
                    if LLM_PROCESSING_MODE == "text_llm":
                        img_data = pix.tobytes("ppm")
                        pil_img = PILImage.open(io.BytesIO(img_data))
                        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                        if ENABLE_IMAGE_PREPROCESSING:
                            cv_img = self.preprocessor.preprocess(cv_img)
                        image_pages.append((page_num + 1, cv_img))
            
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            raw_text = " ".join(text_pages_text) if text_pages_text else ""
            
            return ExtractedTextResult(
                raw_text=raw_text,
                structured_text=text_blocks,
                metadata={
                    "file_type": "pdf",
                    "is_scanned": len(image_pages_bytes) > 0,
                    "page_count": page_count,
                    "extraction_method": "hybrid",
                    "llm_processing_mode": LLM_PROCESSING_MODE,
                    "preprocessed_images": [img for _, img in image_pages] if image_pages else None,
                    "image_pages_bytes": image_pages_bytes if image_pages_bytes else None,
                    "ocr_engine": OCR_ENGINE if LLM_PROCESSING_MODE == "text_llm" and image_pages else None,
                    "image_page_numbers": [pnum for pnum, _ in image_pages_bytes] if image_pages_bytes else [],
                    "pdf_metadata": metadata,
                    "dpi": PDF_PREPROCESSING_DPI
                }
            )
        finally:
            doc.close()
    
    def _detect_pdf_type(self, file_path: str) -> str:
        """Detect if PDF is text-based, image-based, or mixed."""
        doc = fitz.open(file_path)
        try:
            if doc.is_encrypted:
                return "unknown"
            
            page_count = len(doc)
            text_pages = 0
            image_pages = 0
            min_text_length = 50
            
            # Sample first 3 pages and last page
            sample_pages = [0, 1, 2] if page_count > 3 else list(range(page_count))
            if page_count > 3:
                sample_pages.append(page_count - 1)
            
            for page_num in sample_pages:
                try:
                    page = doc.load_page(page_num)
                    text = page.get_text().strip()
                    if len(text) > min_text_length:
                        text_pages += 1
                    else:
                        image_pages += 1
                except Exception:
                    image_pages += 1
            
            if text_pages == 0:
                return "image"
            elif image_pages == 0:
                return "text"
            else:
                return "mixed"
        finally:
            doc.close()
    
    def _has_image_pages(self, file_path: str) -> bool:
        """Check if PDF has image pages (for hybrid mode detection)."""
        doc = fitz.open(file_path)
        try:
            total_pages = len(doc)
            min_text_length = 50
            pages_to_check = [total_pages - 1] if total_pages > 0 else []
            if total_pages >= 2:
                pages_to_check.append(total_pages - 2)
            
            for page_num in pages_to_check:
                page = doc.load_page(page_num)
                text = page.get_text().strip()
                if len(text) < min_text_length:
                    return True
            return False
        finally:
            doc.close()

