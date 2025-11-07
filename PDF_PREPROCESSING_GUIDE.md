# PDF Preprocessing Guide

## Overview

PDF preprocessing is the first step before text extraction. The approach depends on whether the PDF is **text-based** (electronically created) or **image-based** (scanned). This guide outlines the preprocessing steps for each type.

## PDF Type Detection

### Step 1: Determine PDF Type

Before preprocessing, we need to detect the PDF type:

**Text-Based PDF:**
- Contains selectable text
- Created digitally (Word, LaTeX, etc.)
- Can extract text directly with PyMuPDF
- **Preprocessing**: Minimal (validation only)

**Image-Based PDF (Scanned):**
- Contains images of pages
- No selectable text
- Requires OCR to extract text
- **Preprocessing**: Convert to images → Image preprocessing → OCR

### Detection Logic

```python
def detect_pdf_type(pdf_path: str) -> str:
    """
    Detect if PDF is text-based or image-based.
    
    Returns:
        "text" - Text-based PDF
        "image" - Image-based PDF
        "mixed" - Some pages have text, some are images
    """
    import fitz
    
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    text_pages = 0
    
    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        text = page.get_text().strip()
        
        # If page has substantial text (> 50 chars), it's text-based
        if len(text) > 50:
            text_pages += 1
    
    doc.close()
    
    # Calculate ratio
    text_ratio = text_pages / total_pages if total_pages > 0 else 0
    
    if text_ratio > 0.8:
        return "text"
    elif text_ratio < 0.2:
        return "image"
    else:
        return "mixed"
```

## Preprocessing for Text-Based PDFs

### Minimal Preprocessing Required

For text-based PDFs, preprocessing is minimal:

1. **PDF Validation**
   - Check if PDF is valid and readable
   - Detect encryption/password protection
   - Check for corruption

2. **Metadata Extraction** (Optional)
   - Extract PDF metadata (title, author, creation date)
   - Get page count
   - Check PDF version

3. **Text Encoding** (Handled by PyMuPDF)
   - PyMuPDF handles encoding automatically
   - No manual encoding conversion needed

### Code Example

```python
def preprocess_text_pdf(pdf_path: str) -> dict:
    """
    Preprocess text-based PDF.
    
    Returns:
        dict with PDF metadata and validation status
    """
    import fitz
    
    try:
        doc = fitz.open(pdf_path)
        
        # Check if encrypted
        if doc.is_encrypted:
            raise ValueError("PDF is encrypted/password-protected")
        
        # Extract metadata
        metadata = {
            "page_count": len(doc),
            "is_encrypted": doc.is_encrypted,
            "pdf_version": doc.pdf_version(),
            "metadata": doc.metadata
        }
        
        # Validate text extraction
        first_page = doc.load_page(0)
        sample_text = first_page.get_text().strip()
        
        if len(sample_text) < 10:
            # Very little text, might be image-based
            metadata["warning"] = "PDF has minimal text, might be image-based"
        
        doc.close()
        
        return {
            "status": "valid",
            "type": "text",
            **metadata
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

## Preprocessing for Image-Based PDFs

### Step-by-Step Process

For image-based PDFs, preprocessing involves multiple steps:

### Step 1: Convert PDF Pages to Images

Use PyMuPDF to render each page as an image:

```python
def pdf_to_images(pdf_path: str, dpi: int = 300) -> list:
    """
    Convert PDF pages to images.
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for image rendering (300 is optimal for OCR)
    
    Returns:
        List of PIL Image objects
    """
    import fitz
    from PIL import Image
    import io
    
    doc = fitz.open(pdf_path)
    images = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Render page as image (pixmap)
        # DPI 300 is optimal for OCR (balance between quality and size)
        mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is default DPI
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        images.append(img)
    
    doc.close()
    return images
```

**DPI Recommendations:**
- **300 DPI**: Optimal for OCR (good balance of quality and file size)
- **150 DPI**: Faster, lower quality (acceptable for simple documents)
- **600 DPI**: Higher quality, larger files (for very small text)

### Step 2: Image Preprocessing (OpenCV)

Apply image preprocessing to improve OCR accuracy:

```python
import cv2
import numpy as np
from PIL import Image

class ImagePreprocessor:
    """Preprocess images for better OCR accuracy."""
    
    def __init__(self, enable_deskew=True, enable_denoise=True, 
                 enable_enhance=True, enable_binarize=True):
        self.enable_deskew = enable_deskew
        self.enable_denoise = enable_denoise
        self.enable_enhance = enable_enhance
        self.enable_binarize = enable_binarize
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Apply full preprocessing pipeline.
        
        Args:
            image: Input image as numpy array (BGR format from OpenCV)
        
        Returns:
            Preprocessed image as numpy array
        """
        processed = image.copy()
        
        # Convert to grayscale
        if len(processed.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        
        # Apply preprocessing steps
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
        """
        # Convert to binary for edge detection
        coords = np.column_stack(np.where(image > 0))
        
        if len(coords) == 0:
            return image
        
        # Get minimum area rectangle
        angle = cv2.minAreaRect(coords)[-1]
        
        # Correct angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Rotate image if angle is significant (> 0.5 degrees)
        if abs(angle) > 0.5:
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            image = cv2.warpAffine(image, M, (w, h), 
                                  flags=cv2.INTER_CUBIC, 
                                  borderMode=cv2.BORDER_REPLICATE)
        
        return image
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise from scanned images.
        
        Uses Non-local Means Denoising for better results.
        """
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        return denoised
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance contrast and brightness.
        
        Improves text visibility.
        """
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        return enhanced
    
    def binarize(self, image: np.ndarray) -> np.ndarray:
        """
        Convert image to black and white (binarization).
        
        Improves OCR accuracy by making text more distinct.
        """
        # Apply adaptive thresholding
        # This works better than simple thresholding for varying lighting
        binary = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        return binary
```

### Step 3: Preprocessing Pipeline

Complete preprocessing pipeline for image-based PDFs:

```python
def preprocess_image_pdf(pdf_path: str, dpi: int = 300, 
                        enable_preprocessing: bool = True) -> list:
    """
    Complete preprocessing for image-based PDFs.
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for image rendering
        enable_preprocessing: Whether to apply OpenCV preprocessing
    
    Returns:
        List of preprocessed images (numpy arrays)
    """
    import fitz
    import cv2
    import numpy as np
    from PIL import Image
    import io
    
    # Step 1: Convert PDF to images
    doc = fitz.open(pdf_path)
    images = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Render page as image
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to numpy array (for OpenCV)
        img_data = pix.tobytes("ppm")
        pil_img = Image.open(io.BytesIO(img_data))
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # Step 2: Apply image preprocessing (if enabled)
        if enable_preprocessing:
            preprocessor = ImagePreprocessor()
            cv_img = preprocessor.preprocess(cv_img)
        
        images.append(cv_img)
    
    doc.close()
    return images
```

## When to Use Each Preprocessing Step

### For Text-Based PDFs:
- ✅ **PDF Validation**: Always
- ✅ **Metadata Extraction**: Optional (for logging)
- ❌ **Image Conversion**: Not needed
- ❌ **Image Preprocessing**: Not needed
- ❌ **OCR**: Not needed

### For Image-Based PDFs:
- ✅ **PDF Validation**: Always
- ✅ **Image Conversion**: Always (required for OCR)
- ✅ **Image Preprocessing**: Recommended (improves OCR accuracy)
  - **Deskew**: Use if documents might be rotated
  - **Denoise**: Use for scanned documents with noise
  - **Enhance Contrast**: Use for faded or low-contrast documents
  - **Binarize**: Use for color/gray documents (converts to B&W)
- ✅ **OCR**: Required (Tesseract, Google Cloud Vision, or Gemini Vision)

## Configuration

Add to `config.py`:

```python
# PDF Preprocessing Configuration
PDF_PREPROCESSING_DPI = int(os.getenv("PDF_PREPROCESSING_DPI", "300"))
# DPI for rendering PDF pages as images (150, 300, 600)
# Higher DPI = better quality but larger files

ENABLE_IMAGE_PREPROCESSING = os.getenv("ENABLE_IMAGE_PREPROCESSING", "true").lower() == "true"
# Enable OpenCV preprocessing for scanned PDFs

ENABLE_DESKEW = os.getenv("ENABLE_DESKEW", "true").lower() == "true"
ENABLE_DENOISE = os.getenv("ENABLE_DENOISE", "true").lower() == "true"
ENABLE_ENHANCE = os.getenv("ENABLE_ENHANCE", "true").lower() == "true"
ENABLE_BINARIZE = os.getenv("ENABLE_BINARIZE", "true").lower() == "true"
# Individual preprocessing steps (can be toggled)
```

## Performance Considerations

### Text-Based PDFs:
- **Fast**: Direct text extraction (milliseconds per page)
- **No preprocessing overhead**

### Image-Based PDFs:
- **Slower**: Image conversion + preprocessing + OCR
- **Processing time per page:**
  - Image conversion: ~100-500ms (depends on DPI)
  - Image preprocessing: ~50-200ms (depends on image size)
  - OCR: ~1-5 seconds (depends on OCR engine and image quality)

### Optimization Tips:
1. **Use appropriate DPI**: 300 DPI is usually sufficient
2. **Disable unnecessary preprocessing**: If documents are already high quality
3. **Process pages in parallel**: For multi-page documents
4. **Cache preprocessed images**: If processing same PDF multiple times

## Error Handling

```python
def safe_preprocess_pdf(pdf_path: str) -> dict:
    """
    Safely preprocess PDF with error handling.
    
    Returns:
        dict with preprocessing results or error information
    """
    try:
        # Step 1: Detect PDF type
        pdf_type = detect_pdf_type(pdf_path)
        
        if pdf_type == "text":
            # Text-based: minimal preprocessing
            result = preprocess_text_pdf(pdf_path)
            result["preprocessing_steps"] = ["validation"]
            
        elif pdf_type == "image":
            # Image-based: full preprocessing
            images = preprocess_image_pdf(pdf_path)
            result = {
                "status": "success",
                "type": "image",
                "page_count": len(images),
                "preprocessing_steps": [
                    "pdf_to_images",
                    "deskew",
                    "denoise",
                    "enhance_contrast",
                    "binarize"
                ]
            }
            
        else:  # mixed
            # Handle mixed PDFs (some pages text, some images)
            result = {
                "status": "success",
                "type": "mixed",
                "preprocessing_steps": ["validation", "mixed_processing"]
            }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "type": "unknown"
        }
```

## Summary

**Text-Based PDFs:**
1. Validate PDF (check encryption, corruption)
2. Extract text directly (no preprocessing needed)

**Image-Based PDFs:**
1. Validate PDF
2. Convert PDF pages to images (300 DPI recommended)
3. Apply image preprocessing (deskew, denoise, enhance, binarize)
4. Run OCR on preprocessed images

**Key Points:**
- Text-based PDFs: Minimal preprocessing (validation only)
- Image-based PDFs: Full preprocessing pipeline (convert → preprocess → OCR)
- Image preprocessing significantly improves OCR accuracy
- DPI 300 is optimal for OCR (balance of quality and speed)
- Preprocessing steps are configurable (can be enabled/disabled)

