# Image Preprocessor

**Module:** `extractors.image_preprocessor`  
**Last Updated:** November 11, 2025

## Purpose

The `ImagePreprocessor` class applies OpenCV-based enhancements to scanned PDF pages before OCR. These operations increase text legibility and drastically improve recognition accuracy for Tesseract or Google Cloud Vision.

## Pipeline Steps

1. **Grayscale conversion** — normalises channel depth before processing.
2. **Deskew** (`deskew`) — detects rotation via contour analysis and corrects angles >0.5°.
3. **Denoise** (`denoise`) — uses Non-local Means filtering to remove speckle noise without blurring glyph edges.
4. **Enhance contrast** (`enhance_contrast`) — CLAHE (Contrast Limited Adaptive Histogram Equalization) lifts faint text without amplifying noise.
5. **Binarize** (`binarize`) — adaptive Gaussian thresholding generates crisp black/white masks suited for OCR engines.

Each step is toggleable through constructor flags and environment variables (`ENABLE_DESKEW`, `ENABLE_DENOISE`, etc.).

## Usage

```python
from extractors.image_preprocessor import ImagePreprocessor
preprocessor = ImagePreprocessor()
processed_image = preprocessor.preprocess(cv_image)
```

- Accepts and returns `numpy.ndarray` (OpenCV format – BGR for input, grayscale/binary for output).
- Can be instantiated once and reused across pages.

## Configuration

Controlled via `config.py` environment toggles:

| Setting | Env Var | Default |
|---------|---------|---------|
| Enable preprocessing | `ENABLE_IMAGE_PREPROCESSING` | `true` |
| Deskew | `ENABLE_DESKEW` | `true` |
| Denoise | `ENABLE_DENOISE` | `true` |
| Enhance contrast | `ENABLE_ENHANCE` | `true` |
| Binarize | `ENABLE_BINARIZE` | `true` |

## Dependencies

- `opencv-python`
- `numpy`

## Extension Ideas

- Add morphological operations (dilation/erosion) for dotted lines.
- Implement auto-cropping to remove page borders.
- Support multi-threaded preprocessing for large batches.
