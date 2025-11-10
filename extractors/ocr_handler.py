"""
OCR handler module for multiple OCR engines.

Supports:
- Tesseract OCR (local, free)
- Google Cloud Vision API (cloud, high accuracy)
- Gemini Vision API (direct vision model)
"""

from typing import List, Optional, Dict, Any
import numpy as np

from config import OCR_ENGINE, GCV_CREDENTIALS_PATH, GEMINI_API_KEY
from utils.logger import get_logger
from utils.exceptions import ConfigurationError, OCRError

logger = get_logger(__name__)


class OCRHandler:
    """Handle OCR operations with multiple backends."""
    
    def __init__(self, ocr_engine: str = None, preprocess: bool = True):
        """
        Initialize OCR handler.
        
        Args:
            ocr_engine: OCR engine to use ("tesseract", "gcv", "gemini_vision")
                       If None, uses config default
            preprocess: Whether to preprocess images (handled by ImagePreprocessor)
        """
        self.ocr_engine = ocr_engine or OCR_ENGINE
        self.preprocess = preprocess
        self.logger = get_logger(self.__class__.__module__)
        
        # Initialize engine-specific clients
        self._tesseract_available = False
        self._gcv_client = None
        self._gemini_client = None
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the selected OCR engine."""
        if self.ocr_engine == "tesseract":
            self._init_tesseract()
        elif self.ocr_engine == "gcv":
            self._init_gcv()
        elif self.ocr_engine == "gemini_vision":
            self._init_gemini_vision()
        else:
            raise ConfigurationError(
                f"Unknown OCR engine: {self.ocr_engine}",
                details={"ocr_engine": self.ocr_engine}
            )
    
    def _init_tesseract(self):
        """Initialize Tesseract OCR."""
        try:
            import pytesseract
            # Check if Tesseract is available
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
            self.logger.info("Tesseract OCR initialized successfully")
        except Exception as e:
            self.logger.error("Tesseract OCR not available", exc_info=True)
            raise OCRError(
                "Tesseract OCR not found. Please install Tesseract and ensure it's in PATH. "
                "See docs/windows_ocr_setup.md for installation instructions.",
                details={"ocr_engine": "tesseract", "error": str(e)}
            ) from e
    
    def _init_gcv(self):
        """Initialize Google Cloud Vision API."""
        try:
            from google.cloud import vision
            
            # Initialize client
            if GCV_CREDENTIALS_PATH:
                import os
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCV_CREDENTIALS_PATH
            
            self._gcv_client = vision.ImageAnnotatorClient()
            self.logger.info("Google Cloud Vision API initialized successfully")
        except Exception as e:
            self.logger.error("Google Cloud Vision not available", exc_info=True)
            raise OCRError(
                "Google Cloud Vision API not configured. "
                "Please set GCV_CREDENTIALS_PATH or configure application default credentials.",
                details={"ocr_engine": "gcv", "error": str(e)}
            ) from e
    
    def _init_gemini_vision(self):
        """Initialize Gemini Vision API."""
        try:
            import google.generativeai as genai
            
            if not GEMINI_API_KEY:
                raise ConfigurationError("GEMINI_API_KEY not set")
            
            genai.configure(api_key=GEMINI_API_KEY)
            self._gemini_client = genai
            self.logger.info("Gemini Vision API initialized successfully")
        except ConfigurationError:
            raise
        except Exception as e:
            self.logger.error("Gemini Vision API not available", exc_info=True)
            raise OCRError(
                "Gemini Vision API not configured. Please set GEMINI_API_KEY in environment.",
                details={"ocr_engine": "gemini_vision", "error": str(e)}
            ) from e
    
    def extract_text_from_image(self, image: np.ndarray) -> str:
        """
        Extract text from a single image.
        
        Args:
            image: Image as numpy array (OpenCV format)
        
        Returns:
            Extracted text as string
        """
        if self.ocr_engine == "tesseract":
            return self._extract_with_tesseract(image)
        elif self.ocr_engine == "gcv":
            return self._extract_with_gcv(image)
        elif self.ocr_engine == "gemini_vision":
            return self._extract_with_gemini_vision(image)
        else:
            raise ConfigurationError(
                f"Unknown OCR engine: {self.ocr_engine}",
                details={"ocr_engine": self.ocr_engine}
            )
    
    def extract_text_from_images(self, images: List[np.ndarray]) -> List[str]:
        """
        Extract text from multiple images.
        
        Args:
            images: List of images as numpy arrays
        
        Returns:
            List of extracted text strings
        """
        results = []
        for i, image in enumerate(images):
            try:
                text = self.extract_text_from_image(image)
                results.append(text)
                self.logger.debug(f"Extracted text from image {i+1}/{len(images)}")
            except Exception as e:
                self.logger.error(f"Error extracting text from image {i+1}: {e}")
                results.append("")  # Return empty string on error
        
        return results
    
    def _extract_with_tesseract(self, image: np.ndarray) -> str:
        """Extract text using Tesseract OCR."""
        import pytesseract
        import cv2
        from PIL import Image as PILImage
        
        # Convert numpy array to PIL Image
        if len(image.shape) == 2:  # Grayscale
            pil_image = PILImage.fromarray(image)
        else:  # BGR
            pil_image = PILImage.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Run OCR
        text = pytesseract.image_to_string(pil_image, lang='eng')
        return text.strip()
    
    def _extract_with_gcv(self, image: np.ndarray) -> str:
        """Extract text using Google Cloud Vision API."""
        from google.cloud import vision
        from PIL import Image as PILImage
        import io
        
        # Convert numpy array to bytes
        if len(image.shape) == 2:  # Grayscale
            pil_image = PILImage.fromarray(image)
        else:  # BGR
            import cv2
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = PILImage.fromarray(rgb_image)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Create Vision API image
        vision_image = vision.Image(content=img_bytes.read())
        
        # Perform text detection
        response = self._gcv_client.text_detection(image=vision_image)
        texts = response.text_annotations
        
        if texts:
            # First annotation contains all detected text
            return texts[0].description.strip()
        else:
            return ""
    
    def _extract_with_gemini_vision(self, image: np.ndarray) -> str:
        """
        Extract text using Gemini Vision API.
        
        Note: Gemini Vision can do more than just OCR - it can understand context.
        This method returns raw text extraction. For structured extraction, use
        GeminiVisionExtractor directly.
        """
        from PIL import Image as PILImage
        import io
        
        # Convert numpy array to PIL Image
        if len(image.shape) == 2:  # Grayscale
            pil_image = PILImage.fromarray(image)
        else:  # BGR
            import cv2
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = PILImage.fromarray(rgb_image)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Use Gemini Vision to extract text
        from config import GEMINI_VISION_MODEL
        model = self._gemini_client.GenerativeModel(GEMINI_VISION_MODEL)
        
        response = model.generate_content([
            "Extract all text from this image. Return only the text, no formatting.",
            {
                "mime_type": "image/png",
                "data": img_bytes.getvalue()
            }
        ])
        
        return response.text.strip() if response.text else ""

