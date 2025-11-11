# Strategy Factory

**Module:** `extractors.strategy_factory`  
**Last Updated:** November 11, 2025

## Purpose

`StrategyFactory` selects and creates the appropriate extractor based on file type and `EXTRACTION_METHOD`. It acts as a router, determining which extractor to use for each document.

## Architecture

The factory uses the new extraction architecture:
- **File Type**: Determines extractor class (PDF vs DOCX)
- **EXTRACTION_METHOD**: Determines specific extractor instance (for PDFs)

See [Extraction Architecture](../../architecture/EXTRACTION_ARCHITECTURE.md) for complete details.

## Extractor Selection

### PDF Files

Routing based on `EXTRACTION_METHOD`:

| EXTRACTION_METHOD | Extractor Class | Notes |
|-------------------|-----------------|-------|
| `vision_all` | `GeminiVisionExtractor` | Pure vision extraction |
| `text_direct` | `PDFExtractor` | Text-only extraction |
| `ocr_all` | `PDFExtractor` | OCR all pages |
| `ocr_images_only` | `PDFExtractor` | OCR image pages only |
| `hybrid` | `PDFExtractor` | Flexible extraction (default) |

### DOCX Files

Always uses `DOCXExtractor` regardless of `EXTRACTION_METHOD`.

## Methods

### `get_extractor(file_path, strategy=None)`

Returns the appropriate extractor instance for the file.

**Parameters:**
- `file_path`: Path to document file
- `strategy`: **Legacy parameter** (ignored, use `EXTRACTION_METHOD` instead)

**Returns:**
- `BaseExtractor` instance (PDFExtractor, DOCXExtractor, or GeminiVisionExtractor)

**Example:**
```python
factory = StrategyFactory(gemini_client=client)
extractor = factory.get_extractor("contract.pdf")
result = extractor.extract("contract.pdf")
```

### `extract_with_strategy(file_path, strategy=None)`

Convenience method that gets extractor and extracts in one call.

**Parameters:**
- `file_path`: Path to document file
- `strategy`: **Legacy parameter** (ignored)

**Returns:**
- `ExtractedTextResult` with extracted content

## Configuration

The factory respects:
- `EXTRACTION_METHOD`: Determines which extractor to use for PDFs
- `GEMINI_API_KEY`: Required for `GeminiVisionExtractor`

See [Configuration Guide](../setup/configuration.md) for all options.

## Dependencies

- **PDFExtractor**: For most PDF extraction methods
- **DOCXExtractor**: For DOCX files
- **GeminiVisionExtractor**: For `vision_all` method
- **GeminiClient**: Passed to extractors that need it

## Error Handling

- **FileError**: Raised for unsupported file types
- **ConfigurationError**: Raised for missing required configuration

## Related Modules

- **[PDF Extractor](pdf_extractor.md)**: Main PDF extraction
- **[DOCX Extractor](docx_extractor.md)**: DOCX extraction
- **[Gemini Vision Extractor](gemini_vision_extractor.md)**: Pure vision extraction
- **[Extraction Coordinator](extraction_coordinator.md)**: Uses factory to get extractors
