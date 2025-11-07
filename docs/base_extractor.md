# Base Extractor

## Purpose

Defines the abstract interface for all document extractors (`PDFExtractor`, `DOCXExtractor`, future OCR-based extractors). Centralises validation, logging, and result shaping so downstream modules stay consistent.

## Key Components

- `BaseExtractor` (abstract class)
  - `extract(file_path: str)` — contract that concrete extractors implement.
  - `validate_file()` — shared file existence/size guard.
  - `get_metadata()` — basic file metadata (paths, sizes, timestamps).
  - `_log_extraction_start/complete/error()` — standardised logging hooks.
- `ExtractedTextResult`
  - Stores `raw_text`, structured spans, detected headers, and metadata describing extraction strategy and confidence.
  - `to_dict()` helper keeps API/UI layers decoupled from internal objects.

## Extension Guidelines

1. **Never skip `validate_file()`** — call it at the start of every `extract()` implementation.
2. **Populate metadata consistently** — always include `file_type`, `page_count`, `extraction_method`, and `extraction_strategy` so downstream processors can branch correctly.
3. **Log with context** — use `_log_extraction_*` helpers instead of custom messages to keep telemetry uniform.
4. **Return `ExtractedTextResult`** — even if a module produces intermediate artefacts (e.g., images for OCR), store them under `metadata` and keep `raw_text` accurate.

## Dependencies

- Standard library only (logging, pathlib, abc)
- No side effects — safe to import in any environment

## Related Modules

- [`pdf_extractor`](pdf_extractor.md)
- `docx_extractor` (planned)
- OCR handlers (planned)
