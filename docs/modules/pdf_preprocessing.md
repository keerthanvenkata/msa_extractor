# PDF Preprocessing

## Overview

PDF preprocessing adapts to two primary document types:

- **Text-based PDFs** — digitally generated, contain embedded text
- **Image-based PDFs** — scanned images, require OCR

Auto-detection routes documents through the correct pipeline to maximise extraction accuracy.

## Detection

```python
from extractors.pdf_extractor import PDFExtractor
pdf_type = extractor._detect_pdf_type("/path/to/file.pdf")  # returns text/image/mixed
```

- Samples a subset of pages and checks text length via PyMuPDF
- Returns `"text"`, `"image"`, or `"mixed"`
- Default fallback is `"image"` when detection fails (safest for OCR)

## Text-Based PDFs

1. Validate file (size, readability, encryption)
2. Extract span-level data with PyMuPDF
3. Populate `structured_text` with font metadata for header detection
4. Forward combined text to Gemini Flash for schema extraction

_No additional preprocessing required beyond validation._

## Image-Based PDFs

1. Render each page at configurable DPI (`PDF_PREPROCESSING_DPI`, default 300)
2. Convert to OpenCV matrices (`numpy.ndarray`)
3. Apply optional preprocessing pipeline (toggle via `ENABLE_IMAGE_PREPROCESSING`):

   | Step | Goal |
   |------|------|
   | Deskew | Correct rotation | 
   | Denoise | Remove speckle artefacts |
   | Enhance contrast | Highlight faint text |
   | Binarize | Produce crisp black/white masks |

4. Pass processed images to OCR engine (Tesseract, Google Cloud Vision, or Gemini Vision)
5. Feed OCR text into Gemini Flash (unless using Gemini Vision directly)

## Mixed PDFs

- Current behaviour: treat as text-based, issue warning
- Planned enhancement: per-page branching (`text` pages direct extraction, `image` pages through OCR)

## Configuration Cheat Sheet

```env
PDF_PREPROCESSING_DPI=300
ENABLE_IMAGE_PREPROCESSING=true
ENABLE_DESKEW=true
ENABLE_DENOISE=true
ENABLE_ENHANCE=true
ENABLE_BINARIZE=true
```

Tune these values in `.env` or environment variables to balance accuracy vs performance.

## Performance Tips

- **DPI 300** offers the best balance; raise to 600 only for tiny fonts
- Disable preprocessing steps if scans are already clean to save time
- Batch preprocessing is parallelisable because each page is independent

## Related Modules

- [`PDFExtractor`](pdf_extractor.md)
- [`ImagePreprocessor`](image_preprocessor.md)
- OCR handlers (Tesseract/GCV/Gemini Vision — coming soon)
