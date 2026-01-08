# ADR-0008: Hybrid Extraction Method as Default

**Status:** Accepted  
**Date:** November 2025 (estimated)  
**Deciders:** Development Team  
**Tags:** extraction, default, pdf

## Context

Multiple content extraction methods available:
- `text_direct`: Extract text only, ignore images
- `ocr_all`: OCR all pages
- `ocr_images_only`: Extract text + OCR image pages
- `vision_all`: Convert all pages to images
- `hybrid`: Extract text from text pages, convert image pages to images

Need to choose a default that handles the most common use case: mixed PDFs with both text and image pages.

## Decision

Chose **`hybrid`** as the default extraction method.

## Consequences

### Positive
- **Handles mixed PDFs**: Works with both text and image pages
- **Efficient**: Uses native text extraction when possible (faster than OCR)
- **Flexible**: Image pages can be processed by LLM or OCR as needed
- **Best balance**: Optimal combination of speed and accuracy
- **Signature support**: Image pages (signatures) are preserved for LLM processing

### Negative
- **More complex**: Requires page type detection
- **Slightly slower**: More processing steps than text_direct

### Neutral
- **Configurable**: Users can override for specific use cases
- **LLM mode dependent**: Works with any LLM processing mode

## Alternatives Considered

1. **`text_direct` as default**:
   - Pros: Fastest, simplest
   - Cons: Misses image pages (signatures, scanned pages)
   - **Rejected** - Too limiting, misses important content

2. **`ocr_all` as default**:
   - Pros: Handles all pages uniformly
   - Cons: Slower, wastes native text extraction
   - **Rejected** - Inefficient for text-based PDFs

3. **`ocr_images_only` as default**:
   - Pros: Handles mixed PDFs
   - Cons: Requires OCR setup, slower than hybrid
   - **Rejected** - Hybrid is more flexible (can use LLM or OCR)

## Implementation Notes

- Default: `EXTRACTION_METHOD=hybrid`
- Detects page types (text vs image) automatically
- Text pages: Extract native text
- Image pages: Convert to images for LLM or OCR processing
- Works optimally with `multimodal` LLM processing mode

