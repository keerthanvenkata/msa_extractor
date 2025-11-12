# Extraction Modes & Strategies Guide

> **⚠️ DEPRECATED:** This document describes the legacy extraction system.  
> **👉 See [EXTRACTION_ARCHITECTURE.md](../architecture/EXTRACTION_ARCHITECTURE.md) for the current architecture.**  
> **Last Updated:** November 12, 2025 (Marked as deprecated)

## Overview

**This document is kept for reference only.** The extraction system has been redesigned with a clearer architecture. See [EXTRACTION_ARCHITECTURE.md](../architecture/EXTRACTION_ARCHITECTURE.md) for the current system.

The legacy system supported multiple extraction modes and strategies, which have been replaced by:
- **Extraction Methods** (`EXTRACTION_METHOD`): How to extract content from PDF pages
- **LLM Processing Modes** (`LLM_PROCESSING_MODE`): How to process extracted content with LLMs

## Migration Guide

| Old Config | New Config |
|------------|------------|
| `EXTRACTION_MODE=text_only` | `EXTRACTION_METHOD=text_direct` + `LLM_PROCESSING_MODE=text_llm` |
| `EXTRACTION_MODE=image_only` | `EXTRACTION_METHOD=ocr_all` + `LLM_PROCESSING_MODE=text_llm` |
| `EXTRACTION_MODE=text_ocr` | `EXTRACTION_METHOD=ocr_images_only` + `LLM_PROCESSING_MODE=text_llm` |
| `EXTRACTION_MODE=multimodal` | `EXTRACTION_METHOD=hybrid` + `LLM_PROCESSING_MODE=multimodal` |
| `EXTRACTION_STRATEGY=gemini_vision` | `EXTRACTION_METHOD=vision_all` + `LLM_PROCESSING_MODE=vision_llm` |

---

## Legacy Documentation (For Reference Only)

The MSA Metadata Extractor supports multiple extraction modes and strategies, allowing you to choose the best approach for different document types and use cases.

## Extraction Modes (`EXTRACTION_MODE`)

Extraction modes control how mixed PDFs (text + image pages) are processed. Set via `EXTRACTION_MODE` environment variable.

### 1. `text_only`
- **Description:** Extract text only, ignore image pages
- **LLM Used:** Text LLM (Gemini Flash/Pro)
- **Input:** Text from text-based pages only
- **Use Case:** When you only need text-based information and want to skip signature pages
- **Output:** Text from text-based pages only
- **Image Pages:** Ignored

### 2. `image_only`
- **Description:** Extract from images only (OCR or vision)
- **LLM Used:** Depends on OCR engine:
  - If `OCR_ENGINE=tesseract` or `gcv`: OCR text → Text LLM
  - If `OCR_ENGINE=gemini_vision`: Vision LLM directly
- **Input:** Images from all pages
- **Use Case:** For fully scanned/image-based documents
- **Output:** OCR text or vision-extracted metadata from all image pages
- **Text Pages:** Ignored

### 3. `text_ocr` (Default)
- **Description:** Extract text + OCR text from image pages
- **LLM Used:** Text LLM (Gemini Flash/Pro)
- **Input:** Combined text from text pages + OCR text from image pages
- **Use Case:** Standard mixed PDFs where you want all text content
- **Output:** Combined text from text pages and OCR'd image pages
- **Image Pages:** OCR'd and text appended

### 4. `multimodal` ⭐ Recommended for Signature Pages
- **Description:** Send text + images together to vision model
- **LLM Used:** Vision LLM (Gemini Vision)
- **Input:** Text from text pages + image bytes from image pages (sent together)
- **Use Case:** Best for extracting signatory information from signature pages
- **Output:** Metadata extracted using both text context and image analysis
- **Image Pages:** Sent as images to vision model along with text
- **How it works:**
  1. Extracts text from text-based pages
  2. Detects image pages (especially signature pages at the end)
  3. Sends text + image bytes together to Gemini Vision API
  4. Vision model analyzes both text and images in context

### 5. `text_image`
- **Description:** Extract text + send image pages directly to vision model (separately)
- **LLM Used:** Vision LLM (Gemini Vision) for images, Text LLM for text
- **Input:** Text from text pages (sent to text LLM) + images from image pages (sent to vision LLM)
- **Use Case:** Similar to multimodal but processes images separately
- **Output:** Text extraction + separate image analysis
- **Image Pages:** Sent separately to vision model

## Extraction Strategies (`EXTRACTION_STRATEGY`)

Extraction strategies control the overall extraction approach for the entire document. Set via `EXTRACTION_STRATEGY` environment variable.

### 1. `auto` (Default)
- **Description:** Automatically detects PDF type and selects appropriate strategy
- **Text PDFs:** Uses text extraction + Text LLM
- **Image PDFs:** Uses OCR (or Gemini Vision if `OCR_ENGINE=gemini_vision`) + Text LLM
- **Mixed PDFs:** Uses text extraction (respects `EXTRACTION_MODE`)

### 2. `text_extraction`
- **Description:** Force text extraction strategy
- **All PDFs:** Uses PyMuPDF text extraction + Text LLM
- **Image Pages:** Handled according to `EXTRACTION_MODE`

### 3. `gemini_vision` ⭐ Pure Vision Mode
- **Description:** Use Gemini Vision API directly for all pages
- **All PDFs:** Converts all pages to images → sends to Vision LLM
- **LLM Used:** Vision LLM only (Gemini Vision)
- **Input:** Images only (no text extraction)
- **Use Case:** 
  - Fully scanned/image-based documents
  - When you want vision-only extraction
  - Complex layouts that benefit from vision understanding
- **Output:** Metadata extracted directly from images
- **How it works:**
  1. Converts all PDF pages to images
  2. Sends each page image to Gemini Vision API
  3. Extracts metadata from first 3 pages (cover + first 2 content pages)
  4. Merges metadata intelligently
  5. Returns combined result

### 4. `tesseract`
- **Description:** Force Tesseract OCR for image-based PDFs
- **Image PDFs:** Uses Tesseract OCR → Text LLM
- **Text PDFs:** Uses text extraction → Text LLM

### 5. `gcv`
- **Description:** Force Google Cloud Vision OCR for image-based PDFs
- **Image PDFs:** Uses GCV OCR → Text LLM
- **Text PDFs:** Uses text extraction → Text LLM

## Vision-Only Extraction

### Option 1: `EXTRACTION_STRATEGY=gemini_vision` (Pure Vision)
**Best for:** Fully image-based documents, complex layouts, vision-only extraction

```env
EXTRACTION_STRATEGY=gemini_vision
```

**How it works:**
- Converts all PDF pages to images
- Sends images directly to Gemini Vision API
- Extracts metadata from images (no text extraction step)
- No OCR involved - pure vision model

**Advantages:**
- ✅ Pure vision extraction - no text extraction needed
- ✅ Excellent for complex layouts
- ✅ Can read handwritten text and signatures
- ✅ Direct metadata extraction from images
- ✅ Single API call per page

**Limitations:**
- ⚠️ More expensive (Vision API costs)
- ⚠️ Rate limits apply
- ⚠️ Currently extracts metadata from first 3 pages only

### Option 2: `EXTRACTION_MODE=image_only` + `OCR_ENGINE=gemini_vision`
**Best for:** Image-only extraction with OCR fallback option

```env
EXTRACTION_MODE=image_only
OCR_ENGINE=gemini_vision
```

**How it works:**
- Extracts only from image pages
- Uses Gemini Vision for OCR (extracts text from images)
- Sends OCR text to Text LLM for metadata extraction

**Note:** This still uses Text LLM after OCR, not pure vision extraction.

## Mode vs Strategy Comparison

| Mode/Strategy | Text Pages | Image Pages | LLM Used | Pure Vision? |
|--------------|------------|-------------|----------|--------------|
| `text_only` | ✅ Extract | ❌ Ignore | Text LLM | ❌ |
| `image_only` | ❌ Ignore | ✅ OCR/Vision | Text/Vision LLM | ⚠️ Depends on OCR_ENGINE |
| `text_ocr` | ✅ Extract | ✅ OCR | Text LLM | ❌ |
| `multimodal` | ✅ Extract | ✅ Vision | Vision LLM | ✅ (text + images) |
| `text_image` | ✅ Extract | ✅ Vision | Vision LLM | ⚠️ (separate calls) |
| `gemini_vision` (strategy) | ✅ Convert to images | ✅ Images | Vision LLM | ✅ (pure vision) |

## Recommendations

### For Signature Pages
```env
EXTRACTION_MODE=multimodal
```
- Sends text + images together
- Best for extracting signatory information

### For Fully Scanned Documents
```env
EXTRACTION_STRATEGY=gemini_vision
```
- Pure vision extraction
- No OCR needed
- Best for complex layouts

### For Mixed PDFs (General)
```env
EXTRACTION_MODE=text_ocr
```
- OCR image pages
- Combine with text
- Cost-effective

### For Text-Only Documents
```env
EXTRACTION_MODE=text_only
```
- Fastest extraction
- Skip image processing

## Configuration Examples

### Pure Vision Extraction (All Images)
```env
EXTRACTION_STRATEGY=gemini_vision
GEMINI_VISION_MODEL=gemini-2.5-pro
```

### Multimodal (Text + Images Together)
```env
EXTRACTION_MODE=multimodal
GEMINI_VISION_MODEL=gemini-2.5-pro
```

### Image-Only with Vision OCR
```env
EXTRACTION_MODE=image_only
OCR_ENGINE=gemini_vision
GEMINI_VISION_MODEL=gemini-2.5-pro
```

### Standard Mixed PDF
```env
EXTRACTION_MODE=text_ocr
OCR_ENGINE=tesseract
```

## Troubleshooting

### Issue: Vision mode not being used

**Check:**
1. `EXTRACTION_STRATEGY=gemini_vision` is set (for pure vision)
2. `EXTRACTION_MODE=multimodal` is set (for multimodal)
3. `OCR_ENGINE=gemini_vision` is set (for image_only with vision)
4. Gemini Vision API key is configured correctly
5. `GEMINI_VISION_MODEL` is set correctly

### Issue: Want pure vision but getting OCR

**Solution:**
- Use `EXTRACTION_STRATEGY=gemini_vision` instead of `EXTRACTION_MODE=image_only`
- This forces pure vision extraction without OCR step

### Issue: Vision extraction too expensive

**Solutions:**
1. Use `EXTRACTION_MODE=text_ocr` with `OCR_ENGINE=tesseract` (local OCR)
2. Use `EXTRACTION_MODE=text_only` if you don't need image pages
3. Limit pages sent to vision (currently first 3 pages for metadata)

## Summary

- **5 Extraction Modes:** Control how mixed PDFs are processed
- **5 Extraction Strategies:** Control overall extraction approach
- **Pure Vision:** Use `EXTRACTION_STRATEGY=gemini_vision` for vision-only extraction
- **Multimodal:** Use `EXTRACTION_MODE=multimodal` for text + images together
- **Default:** `EXTRACTION_MODE=text_ocr` with `EXTRACTION_STRATEGY=auto`

