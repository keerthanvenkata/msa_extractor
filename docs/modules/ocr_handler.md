# OCR Handler

**Module:** `extractors.ocr_handler`  
**Last Updated:** November 12, 2025

## Purpose

The `OCRHandler` class provides a unified interface for multiple OCR engines:
- **Tesseract OCR** (local, free)
- **Google Cloud Vision API** (cloud, high accuracy)
- **Gemini Vision API** (direct vision model)

## Supported Engines

### Tesseract OCR
- Free, open-source, local processing
- Requires Tesseract binary installation
- Good accuracy with preprocessing
- Works offline

### Google Cloud Vision API
- Cloud-based, high accuracy
- Handles complex layouts well
- Requires Google Cloud credentials
- Production-ready

### Gemini Vision API
- Direct vision model integration
- Excellent accuracy, understands context
- Single API call (no separate OCR step)
- Requires Gemini API key

## Usage

```python
from extractors.ocr_handler import OCRHandler

# Initialize with specific engine
handler = OCRHandler(ocr_engine="tesseract", preprocess=True)

# Extract text from single image
text = handler.extract_text_from_image(image_array)

# Extract text from multiple images
texts = handler.extract_text_from_images([image1, image2, image3])
```

## Configuration

- `OCR_ENGINE`: Engine to use ("tesseract", "gcv", "gemini_vision")
- `ENABLE_IMAGE_PREPROCESSING`: Whether to preprocess images before OCR

## Dependencies

- `pytesseract` (for Tesseract)
- `google-cloud-vision` (for GCV)
- `google-generativeai` (for Gemini Vision)
- `opencv-python`, `numpy`, `Pillow` (for image handling)

## Error Handling

- Validates engine availability on initialization
- Returns empty string on OCR failure
- Logs errors for debugging

