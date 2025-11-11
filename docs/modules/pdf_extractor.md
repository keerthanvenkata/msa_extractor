# PDF Extractor

**Module:** `extractors.pdf_extractor`  
**Last Updated:** January 7, 2025

## Purpose

`PDFExtractor` extracts content from PDF files using the new extraction architecture. It supports multiple extraction methods configured via `EXTRACTION_METHOD`:

- **Text pages**: Direct text extraction using PyMuPDF
- **Image-with-text pages**: OCR extraction after preprocessing
- **Pure image pages**: Image conversion for vision LLM
- **Any combination**: Flexible handling of mixed PDFs

## Architecture

The extractor uses a two-tier system:
1. **Content Extraction** (`EXTRACTION_METHOD`): How to extract content from pages
2. **LLM Processing** (`LLM_PROCESSING_MODE`): How to process extracted content (handled by `ExtractionCoordinator`)

See [Extraction Architecture](../../architecture/EXTRACTION_ARCHITECTURE.md) for complete details.

## Extraction Methods

The `extract()` method routes to one of five extraction methods based on `EXTRACTION_METHOD`:

### 1. `text_direct` (`_extract_text_direct`)
- Extracts text directly from text-based pages
- Ignores image pages completely
- **Use Case**: Text-only PDFs, skip signatures
- **Output**: Text from text pages only

### 2. `ocr_all` (`_extract_ocr_all`)
- Converts all pages to images
- Runs OCR on all pages (even text pages)
- Preprocesses images before OCR
- **Use Case**: When you want OCR on everything
- **Output**: OCR text from all pages

### 3. `ocr_images_only` (`_extract_ocr_images_only`)
- Extracts text directly from text pages
- Runs OCR only on image pages
- Preprocesses image pages before OCR
- **Use Case**: Mixed PDFs with scanned pages
- **Output**: Combined text from text pages + OCR from image pages

### 4. `vision_all` (`_extract_vision_all`)
- Converts all pages to PNG images
- No OCR performed
- Images ready for vision LLM
- **Use Case**: Pure vision extraction, complex layouts
- **Output**: Image bytes for all pages

### 5. `hybrid` (`_extract_hybrid`) - Default
- Extracts text from text pages
- Converts image pages to images
- Prepares content based on `LLM_PROCESSING_MODE`
- Can convert text pages to images if `LLM_PROCESSING_MODE=vision_llm`
- **Use Case**: Flexible handling of mixed PDFs
- **Output**: Text + images, ready for any LLM processing mode

## Workflow

```
1. validate_file() - Inherited from BaseExtractor
2. Route based on EXTRACTION_METHOD:
   - text_direct → _extract_text_direct()
   - ocr_all → _extract_ocr_all()
   - ocr_images_only → _extract_ocr_images_only()
   - vision_all → _extract_vision_all()
   - hybrid → _extract_hybrid()
3. Return ExtractedTextResult with:
   - raw_text: Combined text content
   - image_pages_bytes: List of image bytes (if applicable)
   - metadata: Extraction metadata
```

## PDF Type Detection

The extractor includes helper methods for PDF analysis:

- **`_detect_pdf_type(file_path)`**: Samples pages to classify as `text`, `image`, or `mixed`
- **`_has_image_pages(file_path)`**: Checks if PDF contains image pages (useful for hybrid mode)

These are used internally by `_extract_hybrid()` to determine processing strategy.

## Metadata Keys

| Key | Description | Example Values |
|-----|-------------|----------------|
| `file_type` | Always `"pdf"` | `"pdf"` |
| `page_count` | Total pages processed | `15` |
| `extraction_method` | EXTRACTION_METHOD used | `"hybrid"`, `"ocr_images_only"` |
| `llm_processing_mode` | LLM_PROCESSING_MODE (if set) | `"multimodal"`, `"text_llm"` |
| `pdf_type` | Detected PDF type | `"text"`, `"image"`, `"mixed"` |
| `has_image_pages` | Whether PDF contains image pages | `True`, `False` |
| `preprocessed_images` | List of numpy arrays (OCR methods only) | `[array(...), ...]` |
| `image_pages_bytes` | List of PNG bytes (vision/multimodal) | `[bytes(...), ...]` |
| `pdf_metadata` | Raw PDF metadata when available | `{"title": "...", ...}` |

## Configuration

### Extraction Method
Set `EXTRACTION_METHOD` in `.env`:
```env
EXTRACTION_METHOD=hybrid  # Default
```

### Image Preprocessing
- `PDF_PREPROCESSING_DPI`: Render resolution (default: 300)
- `ENABLE_IMAGE_PREPROCESSING`: Master switch (default: true)
- `ENABLE_DESKEW`: Correct rotation (default: true)
- `ENABLE_DENOISE`: Remove noise (default: true)
- `ENABLE_ENHANCE`: Contrast enhancement (default: true)
- `ENABLE_BINARIZE`: Binarization (default: true)

See [Configuration Guide](../setup/configuration.md) for all options.

## Dependencies

- **PyMuPDF (fitz)**: PDF parsing and rendering
- **Pillow**: Image format conversions
- **opencv-python, numpy**: Image processing
- **Internal modules**: `BaseExtractor`, `ImagePreprocessor`

## Resource Management

All PDF documents are properly closed using `finally` blocks:
- `_extract_text_direct()`: Ensures document closure
- `_extract_ocr_all()`: Ensures document closure
- `_extract_ocr_images_only()`: Ensures document closure
- `_extract_vision_all()`: Ensures document closure
- `_extract_hybrid()`: Ensures document closure
- `_detect_pdf_type()`: Ensures document closure

## Related Modules

- **[Extraction Coordinator](extraction_coordinator.md)**: Orchestrates full pipeline
- **[Strategy Factory](strategy_factory.md)**: Routes to appropriate extractor
- **[Image Preprocessor](image_preprocessor.md)**: Preprocesses images for OCR
- **[OCR Handler](../features/OCR_AND_SIGNATURES.md)**: Performs OCR operations
- **[Base Extractor](base_extractor.md)**: Abstract base class

## Extension Points

1. **Custom extraction methods**: Add new `_extract_*` methods and route in `extract()`
2. **Page-level processing**: Enhance `_extract_hybrid()` for per-page strategies
3. **Streaming**: Implement streaming for very large PDFs
4. **Caching**: Cache PDF type detection results across runs
