# Gemini Vision Extractor

**Module:** `extractors.gemini_vision_extractor`  
**Last Updated:** November 12, 2025

## Purpose

The `GeminiVisionExtractor` class provides direct integration with Gemini Vision API for image-based PDFs. Unlike the OCR + text LLM pipeline, this extractor uses Gemini Vision to:
- Extract text from images
- Extract structured metadata directly
- All in a single API call per page

## Workflow

1. Convert PDF pages to images (using PyMuPDF at configured DPI)
2. Send each page image to Gemini Vision API
3. Extract metadata from first page (or combine from all pages)
4. Extract raw text from all pages
5. Return combined result

## Advantages

- **Single API call**: No separate OCR step needed
- **Context understanding**: Gemini Vision understands document structure
- **High accuracy**: Excellent for complex layouts
- **Direct metadata**: Can extract metadata directly without text LLM step

## Limitations

- **API costs**: More expensive than local OCR
- **Rate limits**: Subject to Gemini API rate limits
- **Multi-page handling**: Currently extracts metadata from first page only (can be enhanced)

## Configuration

- `GEMINI_API_KEY`: Required
- `GEMINI_VISION_MODEL`: Model to use (default: `gemini-1.5-flash`)
- `PDF_PREPROCESSING_DPI`: Image rendering resolution (default: 300)

## Usage

```python
from extractors.gemini_vision_extractor import GeminiVisionExtractor

extractor = GeminiVisionExtractor(gemini_client=gemini_client)
result = extractor.extract("/path/to/scanned.pdf")
metadata = result.metadata.get("extracted_metadata", {})
```

## Dependencies

- `google-generativeai` (Gemini API client)
- `PyMuPDF` (PDF to image conversion)
- `Pillow` (image handling)

## Future Enhancements

- Multi-page metadata aggregation
- Confidence scoring per field
- Page-level metadata extraction with merging logic

