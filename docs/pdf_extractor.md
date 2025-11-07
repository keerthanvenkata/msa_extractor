# PDF Extractor

## Purpose

`PDFExtractor` normalises PDF ingestion across three scenarios:

1. **Text-based PDFs** — extract structured text (with fonts/positions) using PyMuPDF.
2. **Image-based PDFs** — render pages to images, apply preprocessing, defer OCR to configured engine.
3. **Mixed PDFs** — provide best-effort extraction while warning about image-heavy pages.

## Workflow

1. `validate_file()` inherited from `BaseExtractor` ensures readable input.
2. `_detect_pdf_type()` samples pages to classify the document as `text`, `image`, or `mixed`.
3. Branch:**
   - **Text PDFs:** `_extract_text_based()`
     - `page.get_text("dict")` → span-level metadata (font size, font name, bbox)
     - Combines spans into `raw_text` and enriches `structured_text` for header detection.
   - **Image PDFs:** `_extract_image_based()`
     - Renders each page at configurable DPI (`PDF_PREPROCESSING_DPI`)
     - Converts to OpenCV matrices and runs `ImagePreprocessor`
     - Stores processed images in `metadata['preprocessed_images']` for downstream OCR.
   - **Mixed PDFs:** currently defaults to text-based extraction with warning; per-page handling planned.
4. Returns an `ExtractedTextResult` with strategy metadata so post-processing knows which path ran.

## Metadata Keys

| Key | Description |
|-----|-------------|
| `file_type` | Always `"pdf"` |
| `is_scanned` | `True` for image-based paths |
| `page_count` | Total pages processed |
| `extraction_method` | `"text"` or `"ocr"` |
| `extraction_strategy` | `"pymupdf"`, `"image_preprocessing"`, etc. |
| `pdf_metadata` | Raw PDF metadata when available |
| `preprocessed_images` | List of numpy arrays ready for OCR (image PDFs only) |

## Configuration Touchpoints

- DPI via `PDF_PREPROCESSING_DPI`
- Preprocessing toggles via `ENABLE_*` flags
- Strategy selection via `EXTRACTION_STRATEGY`/`OCR_ENGINE`

## Dependencies

- `PyMuPDF (fitz)` — PDF parsing and rendering
- `Pillow` — intermediate conversions from PyMuPDF to numpy arrays
- `opencv-python`, `numpy` — image handling
- Internal modules: `BaseExtractor`, `ImagePreprocessor`

## Extension Hooks

- Per-page strategy selection for mixed PDFs
- Direct integration with OCR handler to immediately run Tesseract/GCV
- Streaming extraction for very large PDFs
