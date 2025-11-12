# Extraction Coordinator

**Module:** `extractors.extraction_coordinator`  
**Last Updated:** November 12, 2025

## Purpose

`ExtractionCoordinator` orchestrates the complete extraction pipeline from document input to structured metadata output. It coordinates:

1. **Content Extraction**: Routes to appropriate extractor (PDF/DOCX)
2. **OCR Processing**: Runs OCR when needed based on extraction method
3. **LLM Processing**: Processes extracted content with Gemini based on `LLM_PROCESSING_MODE`
4. **Schema Validation**: Validates and normalizes extracted metadata

## Architecture

The coordinator uses the new two-tier architecture:
- **Extraction Methods** (`EXTRACTION_METHOD`): How content is extracted
- **LLM Processing Modes** (`LLM_PROCESSING_MODE`): How content is processed with LLMs

See [Extraction Architecture](../../architecture/EXTRACTION_ARCHITECTURE.md) for complete details.

## Main Workflow

```
1. extract_metadata(file_path)
   ├─> _extract_text(file_path)
   │   ├─> StrategyFactory.get_extractor()
   │   └─> extractor.extract()
   │
   └─> _process_with_llm(extraction_result, llm_mode)
       ├─> text_llm → gemini_client.extract_metadata_from_text()
       ├─> vision_llm → gemini_client.extract_metadata_from_image()
       ├─> multimodal → gemini_client.extract_metadata_multimodal()
       └─> dual_llm → Both text + vision, then merge
```

## LLM Processing Modes

The coordinator handles four LLM processing modes:

### 1. `text_llm` (Default)
- Sends all text (direct + OCR) to text LLM
- Uses `gemini_client.extract_metadata_from_text()`
- **Input**: `raw_text` from extraction result
- **Use Case**: Cost-effective, text-based extraction

### 2. `vision_llm`
- Sends all images to vision LLM
- Uses `gemini_client.extract_metadata_from_image()`
- **Input**: First image from `image_pages_bytes`
- **Use Case**: Vision-only extraction, complex layouts

### 3. `multimodal`
- Sends text + images together to vision LLM in single call
- Uses `gemini_client.extract_metadata_multimodal()`
- **Input**: `raw_text` + `image_pages_bytes`
- **Use Case**: Best for signatures, context preservation

### 4. `dual_llm`
- Sends text to text LLM and images to vision LLM separately
- Merges results intelligently
- **Input**: `raw_text` → text LLM, `image_pages_bytes` → vision LLM
- **Use Case**: When you want both text and vision analysis

## OCR Integration

When `EXTRACTION_METHOD` is `ocr_all` or `ocr_images_only`:

1. `PDFExtractor` prepares preprocessed images
2. Coordinator runs OCR using `OCRHandler`
3. OCR text is combined with direct text
4. Combined text is sent to text LLM

**Note**: OCR is performed by the coordinator, not the extractor. The extractor only prepares images.

## PDF Extraction Flow

For PDF files (`_extract_from_pdf`):

1. **Get Extractor**: Uses `StrategyFactory` to get appropriate extractor
2. **Extract Content**: Calls `extractor.extract(file_path)`
3. **Run OCR** (if needed):
   - Checks if `preprocessed_images` exist in metadata
   - Runs OCR using configured `OCR_ENGINE`
   - Combines OCR text with `raw_text`
   - Clears `preprocessed_images` from memory
4. **Return Result**: `ExtractedTextResult` ready for LLM processing

## DOCX Extraction Flow

For DOCX files (`_extract_from_docx`):

1. **Get Extractor**: Uses `DOCXExtractor`
2. **Extract Content**: Calls `extractor.extract(file_path)`
3. **Return Result**: `ExtractedTextResult` with text content

## Result Merging (Dual LLM Mode)

When `LLM_PROCESSING_MODE=dual_llm`:

1. Extract metadata from text using text LLM
2. Extract metadata from images using vision LLM
3. Merge results intelligently:
   - Prioritize non-empty values
   - Prefer values from vision LLM for visual elements (signatures, dates)
   - Combine lists/arrays when appropriate
   - Log conflicts for review

## Configuration

The coordinator respects:
- `EXTRACTION_METHOD`: Determines extraction approach
- `LLM_PROCESSING_MODE`: Determines LLM processing approach
- `OCR_ENGINE`: Which OCR engine to use (tesseract/gcv)

See [Configuration Guide](../setup/configuration.md) for all options.

## Dependencies

- **StrategyFactory**: Routes to appropriate extractor
- **GeminiClient**: Handles LLM API calls
- **OCRHandler**: Performs OCR operations
- **SchemaValidator**: Validates and normalizes metadata (via GeminiClient)

## Error Handling

- **FileError**: Raised for unsupported file types or missing files
- **ExtractionError**: Raised for extraction failures
- **LLMError**: Raised for LLM API failures (with retry logic)
- **OCRError**: Raised for OCR failures

All errors are logged with context and re-raised for caller handling.

## Related Modules

- **[Strategy Factory](strategy_factory.md)**: Extractor selection
- **[PDF Extractor](pdf_extractor.md)**: PDF content extraction
- **[DOCX Extractor](docx_extractor.md)**: DOCX content extraction
- **[Gemini Client](gemini_client.md)**: LLM API integration
- **[OCR Handler](../features/OCR_AND_SIGNATURES.md)**: OCR operations
