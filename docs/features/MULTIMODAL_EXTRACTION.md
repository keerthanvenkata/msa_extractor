# Multimodal Extraction Guide

## Overview

The MSA Metadata Extractor supports multimodal extraction, allowing text and images to be sent together to the Gemini Vision API. This is particularly useful for mixed PDFs where most pages are text-based but some pages (typically signature pages at the end) are image-based.

## Extraction Architecture

The system uses a redesigned architecture with:
- **5 Extraction Methods** (`EXTRACTION_METHOD`): Control how content is extracted from PDF pages
- **4 LLM Processing Modes** (`LLM_PROCESSING_MODE`): Control how extracted content is processed with LLMs

For a complete guide to the extraction architecture, see [EXTRACTION_ARCHITECTURE.md](../architecture/EXTRACTION_ARCHITECTURE.md).

## Multimodal Processing Mode

The `multimodal` LLM processing mode is configured via `LLM_PROCESSING_MODE=multimodal` environment variable.

**Recommended Configuration:**
```env
EXTRACTION_METHOD=hybrid
LLM_PROCESSING_MODE=multimodal
```

This combination:
- Extracts text from text-based pages
- Converts image pages to images
- Sends text + images together to the vision LLM in a single call
- **Use Case:** Best for extracting signatory information from signature pages
- **Output:** Metadata extracted using both text context and image analysis

## Configuration

Set in `.env` file:

```env
EXTRACTION_METHOD=hybrid
LLM_PROCESSING_MODE=multimodal
```

Or via environment variable:

```bash
export EXTRACTION_METHOD=hybrid
export LLM_PROCESSING_MODE=multimodal
```

## How Multimodal Mode Works

### Detection Flow

1. **PDF Type Detection:** System detects PDF as "text", "image", or "mixed"
2. **Image Page Check:** System checks for image pages in the document
3. **Signature Page Detection:** Uses heuristics to identify signature pages:
   - Last page or last 2 pages
   - Low text content (< 100 chars)
   - Signature-related keywords ("signature", "sign", "date", "authorized", etc.)
4. **Mixed Extraction:** If image pages found, switches to mixed extraction mode

### Extraction Process

1. **Text Pages:** Extracted using PyMuPDF (structured text with metadata)
2. **Image Pages:** Converted to PNG images at configured DPI (default: 300)
3. **Multimodal API Call:** 
   - Text content from text pages
   - Image bytes from image pages
   - Sent together to Gemini Vision API
4. **Metadata Extraction:** Vision model analyzes both text and images in context

## Example

For a PDF with:
- Pages 1-10: Text-based content
- Page 11: Image-based signature page

With `EXTRACTION_METHOD=hybrid` and `LLM_PROCESSING_MODE=multimodal`:

```
[INFO] PDF detected as text but has image pages. Using mixed extraction for multimodal mode.
[INFO] Page 11 detected as signature-based page
[INFO] Multimodal extraction: 32080 chars text, 1 image(s)
[INFO] Using multimodal extraction: 32080 chars text, 1 image(s)
```

**Result:** Successfully extracts signatory information from the signature page that would otherwise be missed.

## Benefits

1. **Better Accuracy:** Vision model can read signatures and handwritten text directly
2. **Context Preservation:** Text and images analyzed together for better understanding
3. **Automatic Detection:** System automatically detects image pages even in text-based PDFs
4. **Flexible:** Can be enabled/disabled via configuration

## Limitations

- **API Costs:** Multimodal extraction uses Vision API which may have different pricing
- **Processing Time:** Slightly slower than text-only extraction
- **Image Size:** Large images may increase processing time

## Best Practices

1. **Use `multimodal` processing mode** when you need signatory information
2. **Use `text_llm` processing mode** for general mixed PDFs where OCR is sufficient
3. **Use `text_direct` extraction method** when you don't need signature page information
4. **Monitor logs** to see which pages are detected as image pages

## Troubleshooting

### Issue: Signatory still shows "Not Found" in multimodal mode

**Possible causes:**
1. Image page not detected (check logs for "Page X detected as image-based")
2. Image quality too low (try increasing `PDF_PREPROCESSING_DPI`)
3. Signature page not in last 2 pages (system checks last 2 pages by default)

**Solutions:**
1. Check logs to verify image page detection
2. Increase `PDF_PREPROCESSING_DPI` in `.env` (e.g., `PDF_PREPROCESSING_DPI=400`)
3. Verify signature page is in last 2 pages of document

### Issue: Multimodal mode not being used

**Check:**
1. `LLM_PROCESSING_MODE` is set to `multimodal` in `.env`
2. `EXTRACTION_METHOD` is set to `hybrid` (or compatible method)
3. PDF has image pages (check logs)
4. Gemini Vision API key is configured correctly

