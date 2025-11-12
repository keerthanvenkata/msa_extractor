# Base Extractor

**Module:** `extractors.base_extractor`  
**Last Updated:** November 12, 2025

## Purpose

Defines the abstract interface for all document extractors (`PDFExtractor`, `DOCXExtractor`, `GeminiVisionExtractor`). Centralizes validation, logging, and result shaping so downstream modules stay consistent.

## Key Components

### `BaseExtractor` (Abstract Class)

Abstract base class that all extractors inherit from:

- **`extract(file_path: str)`** — Abstract method that concrete extractors must implement
- **`validate_file(file_path: str)`** — Shared file existence/size validation
- **`get_metadata(file_path: str)`** — Basic file metadata (paths, sizes, timestamps)
- **`_log_extraction_start(file_path)`** — Standardized logging hook
- **`_log_extraction_complete(file_path, result)`** — Standardized logging hook
- **`_log_error(file_path, error)`** — Standardized error logging

### `ExtractedTextResult` (Data Class)

Result structure returned by all extractors:

- **`raw_text`**: Combined text content (string)
- **`structured_text`**: Structured text with spans (list)
- **`headers`**: Detected headers (list)
- **`metadata`**: Extraction metadata (dict)
  - `file_type`: Document type ("pdf", "docx")
  - `page_count`: Number of pages
  - `extraction_method`: EXTRACTION_METHOD used
  - `llm_processing_mode`: LLM_PROCESSING_MODE (if applicable)
  - `preprocessed_images`: List of numpy arrays (OCR methods)
  - `image_pages_bytes`: List of PNG bytes (vision methods)
  - Additional extractor-specific metadata

- **`to_dict()`**: Converts result to dictionary for serialization

## Extension Guidelines

1. **Always call `validate_file()`** — Call it at the start of every `extract()` implementation
2. **Populate metadata consistently** — Always include:
   - `file_type`: Document type
   - `page_count`: Number of pages processed
   - `extraction_method`: EXTRACTION_METHOD used
   - `llm_processing_mode`: LLM_PROCESSING_MODE (if set)
3. **Log with context** — Use `_log_extraction_*` helpers instead of custom messages
4. **Return `ExtractedTextResult`** — Even if producing intermediate artifacts (e.g., images), store them in `metadata` and keep `raw_text` accurate
5. **Handle resources** — Ensure file handles and resources are properly closed (use `finally` blocks)

## Dependencies

- Standard library only (`logging`, `pathlib`, `abc`)
- `utils.logger`: For logging
- `utils.exceptions`: For custom exceptions (`FileError`)
- No side effects — safe to import in any environment

## Related Modules

- **[PDF Extractor](pdf_extractor.md)**: PDF extraction implementation
- **[DOCX Extractor](docx_extractor.md)**: DOCX extraction implementation
- **[Gemini Vision Extractor](gemini_vision_extractor.md)**: Pure vision extraction
