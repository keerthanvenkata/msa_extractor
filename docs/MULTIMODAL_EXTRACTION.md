# Multimodal Extraction Guide

## Overview

The MSA Metadata Extractor supports multimodal extraction, allowing text and images to be sent together to the Gemini Vision API. This is particularly useful for mixed PDFs where most pages are text-based but some pages (typically signature pages at the end) are image-based.

## Extraction Modes

The system supports five extraction modes, configurable via `EXTRACTION_MODE` environment variable:

### 1. `text_only`
- **Description:** Extract text only, ignore image pages
- **Use Case:** When you only need text-based information and want to skip signature pages
- **Output:** Text from text-based pages only

### 2. `image_only`
- **Description:** Extract from images only (OCR or vision)
- **Use Case:** For fully scanned/image-based documents
- **Output:** OCR text from all image pages

### 3. `text_ocr` (Default)
- **Description:** Extract text + OCR text from image pages
- **Use Case:** Standard mixed PDFs where you want all text content
- **Output:** Combined text from text pages and OCR'd image pages

### 4. `multimodal` ⭐ Recommended for Signature Pages
- **Description:** Send text + images together to vision model
- **Use Case:** Best for extracting signatory information from signature pages
- **Output:** Metadata extracted using both text context and image analysis
- **How it works:**
  1. Extracts text from text-based pages
  2. Detects image pages (especially signature pages at the end)
  3. Sends text + image bytes together to Gemini Vision API
  4. Vision model analyzes both text and images in context

### 5. `text_image`
- **Description:** Extract text + send image pages directly to vision model
- **Use Case:** Similar to multimodal but processes images separately
- **Output:** Text extraction + separate image analysis

## Configuration

Set in `.env` file:

```env
EXTRACTION_MODE=multimodal
```

Or via environment variable:

```bash
export EXTRACTION_MODE=multimodal
```

## How Multimodal Mode Works

### Detection Flow

1. **PDF Type Detection:** System detects PDF as "text", "image", or "mixed"
2. **Image Page Check:** If `EXTRACTION_MODE=multimodal` and PDF is detected as "text", system checks last 2 pages for image pages
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

With `EXTRACTION_MODE=multimodal`:

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

1. **Use `multimodal` mode** when you need signatory information
2. **Use `text_ocr` mode** for general mixed PDFs where OCR is sufficient
3. **Use `text_only` mode** when you don't need signature page information
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
1. `EXTRACTION_MODE` is set to `multimodal` in `.env`
2. PDF has image pages (check logs)
3. Gemini Vision API key is configured correctly

