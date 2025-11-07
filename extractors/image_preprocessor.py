"""
Image preprocessing module for OCR.

Provides image preprocessing functions to improve OCR accuracy:
- Deskew (rotation correction)
- Denoise (noise removal)
- Contrast enhancement
- Binarization (black/white conversion)
"""

import cv2
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Preprocess images for better OCR accuracy."""
    
    def __init__(self, enable_deskew: bool = True, enable_denoise: bool = True,
                 enable_enhance: bool = True, enable_binarize: bool = True):
        """
        Initialize image preprocessor.
        
        Args:
            enable_deskew: Enable deskewing (rotation correction)
            enable_denoise: Enable denoising
            enable_enhance: Enable contrast enhancement
            enable_binarize: Enable binarization (black/white conversion)
        """
        self.enable_deskew = enable_deskew
        self.enable_denoise = enable_denoise
        self.enable_enhance = enable_enhance
        self.enable_binarize = enable_binarize
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Apply full preprocessing pipeline.
        
        Args:
            image: Input image as numpy array (BGR format from OpenCV)
        
        Returns:
            Preprocessed image as numpy array
        """
        processed = image.copy()
        
        # Convert to grayscale if needed
        if len(processed.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        
        # Apply preprocessing steps in order
        if self.enable_deskew:
            processed = self.deskew(processed)
        
        if self.enable_denoise:
            processed = self.denoise(processed)
        
        if self.enable_enhance:
            processed = self.enhance_contrast(processed)
        
        if self.enable_binarize:
            processed = self.binarize(processed)
        
        return processed
    
    def deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Correct image rotation (deskew).
        
        Detects and corrects slight rotations in scanned documents.
        
        Args:
            image: Grayscale image as numpy array
        
        Returns:
            Deskewed image
        """
        try:
            # Convert to binary for edge detection
            # Use adaptive threshold to handle varying lighting
            binary = cv2.adaptiveThreshold(
                image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Find non-zero pixels (text regions)
            coords = np.column_stack(np.where(binary > 0))
            
            if len(coords) == 0:
                self.logger.warning("No text regions found for deskewing")
                return image
            
            # Get minimum area rectangle
            angle = cv2.minAreaRect(coords)[-1]
            
            # Correct angle
            # OpenCV returns angle in range [-90, 0)
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Rotate image if angle is significant (> 0.5 degrees)
            if abs(angle) > 0.5:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(
                    image, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                self.logger.debug(f"Deskewed image by {angle:.2f} degrees")
                return rotated
            
            return image
            
        except Exception as e:
            self.logger.warning(f"Deskewing failed: {e}, returning original image")
            return image
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise from scanned images.
        
        Uses Non-local Means Denoising for better results.
        
        Args:
            image: Grayscale image as numpy array
        
        Returns:
            Denoised image
        """
        try:
            # Apply Non-local Means Denoising
            # Parameters: h=10 (filter strength), templateWindowSize=7, searchWindowSize=21
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
            return denoised
        except Exception as e:
            self.logger.warning(f"Denoising failed: {e}, returning original image")
            return image
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance contrast and brightness.
        
        Uses CLAHE (Contrast Limited Adaptive Histogram Equalization)
        to improve text visibility.
        
        Args:
            image: Grayscale image as numpy array
        
        Returns:
            Enhanced image
        """
        try:
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            # clipLimit=2.0: contrast limiting threshold
            # tileGridSize=(8,8): size of grid for histogram equalization
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
            return enhanced
        except Exception as e:
            self.logger.warning(f"Contrast enhancement failed: {e}, returning original image")
            return image
    
    def binarize(self, image: np.ndarray) -> np.ndarray:
        """
        Convert image to black and white (binarization).
        
        Improves OCR accuracy by making text more distinct.
        Uses adaptive thresholding to handle varying lighting.
        
        Args:
            image: Grayscale image as numpy array
        
        Returns:
            Binary image (black and white)
        """
        try:
            # Apply adaptive thresholding
            # This works better than simple thresholding for varying lighting
            # ADAPTIVE_THRESH_GAUSSIAN_C: uses Gaussian-weighted sum
            # THRESH_BINARY: binary thresholding
            # 11: block size for calculating threshold
            # 2: constant subtracted from mean
            binary = cv2.adaptiveThreshold(
                image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            return binary
        except Exception as e:
            self.logger.warning(f"Binarization failed: {e}, returning original image")
            return image

