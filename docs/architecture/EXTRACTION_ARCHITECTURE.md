# Extraction Architecture - Redesign

**Last Updated:** November 12, 2025

## Overview

The extraction system has been redesigned to provide clear separation between:
1. **Content Extraction** - How to extract content from PDF pages
2. **LLM Processing** - How to process extracted content with LLMs

## PDF Page Types

PDFs can contain three types of pages:
- **Text Pages**: Native text that can be extracted directly
- **Image-with-Text Pages**: Scanned pages with text (requires OCR)
- **Pure Image Pages**: Images without extractable text (signatures, diagrams, etc.)

## Content Extraction Methods

### 1. `text_direct`
- Extract text directly from text-based pages
- Ignore image pages
- **Use Case**: Text-only PDFs, skip signatures

### 2. `ocr_all`
- Convert all pages to images
- Run OCR on all pages (even text pages)
- **Use Case**: When you want OCR on everything

### 3. `ocr_images_only`
- Extract text directly from text pages
- Run OCR only on image pages
- **Use Case**: Mixed PDFs with scanned pages

### 4. `vision_all`
- Convert all pages to images
- Send all images to vision LLM (no OCR)
- **Use Case**: Pure vision extraction, complex layouts

### 5. `hybrid` (Default)
- Extract text from text pages
- Convert image pages to images
- Process based on LLM processing mode
- **Use Case**: Flexible handling of mixed PDFs

## LLM Processing Modes

### 1. `text_llm`
- Send all text (direct + OCR) to text LLM
- **Use Case**: Cost-effective, text-based extraction

### 2. `vision_llm`
- Send all images to vision LLM
- **Use Case**: Vision-only extraction, complex layouts

### 3. `multimodal`
- Send text + images together to vision LLM in single call
- **Use Case**: Best for signatures, context preservation

### 4. `dual_llm`
- Send text to text LLM
- Send images to vision LLM separately
- Merge results intelligently
- **Use Case**: When you want both text and vision analysis

## Configuration Variables

### `EXTRACTION_METHOD`
Controls how content is extracted from PDF:
- `text_direct` - Extract text only, ignore images
- `ocr_all` - OCR all pages (convert to images first)
- `ocr_images_only` - Extract text + OCR image pages
- `vision_all` - Convert all pages to images
- `hybrid` - Extract text + convert image pages (default)

### `LLM_PROCESSING_MODE`
Controls how extracted content is processed:
- `multimodal` - Send text + images together to vision LLM (default)
- `text_llm` - Send text to text LLM
- `vision_llm` - Send images to vision LLM
- `dual_llm` - Send text to text LLM + images to vision LLM separately

### `OCR_ENGINE`
OCR engine to use when OCR is needed:
- `tesseract` - Tesseract OCR (default, local)
- `gcv` - Google Cloud Vision OCR
- Note: `vision_all` and `multimodal` don't use OCR

## Complete Flow Matrix

| Extraction Method | LLM Processing Mode | Text Pages | Image Pages | OCR Used? | LLM Used |
|-------------------|---------------------|-----------|-------------|-----------|----------|
| `text_direct` | `text_llm` | ✅ Extract | ❌ Ignore | ❌ | Text LLM |
| `ocr_all` | `text_llm` | ✅ OCR | ✅ OCR | ✅ | Text LLM |
| `ocr_images_only` | `text_llm` | ✅ Extract | ✅ OCR | ✅ | Text LLM |
| `vision_all` | `vision_llm` | ✅ Convert | ✅ Convert | ❌ | Vision LLM |
| `hybrid` | `text_llm` | ✅ Extract | ✅ Convert | ❌ | Text LLM |
| `hybrid` | `vision_llm` | ✅ Convert | ✅ Convert | ❌ | Vision LLM |
| `hybrid` | `multimodal` | ✅ Extract | ✅ Convert | ❌ | Vision LLM (text+images) |
| `hybrid` | `dual_llm` | ✅ Extract | ✅ Convert | ❌ | Text LLM + Vision LLM |

## Common Use Cases

**Note:** Default configuration is `EXTRACTION_METHOD=hybrid` + `LLM_PROCESSING_MODE=multimodal` (best for mixed PDFs with signature pages).

### 1. Text-Only PDF → Vision LLM
```env
EXTRACTION_METHOD=vision_all
LLM_PROCESSING_MODE=vision_llm
```
Converts all pages to images → sends to vision LLM

### 2. Mixed PDF → OCR Image Pages → Text LLM
```env
EXTRACTION_METHOD=ocr_images_only
LLM_PROCESSING_MODE=text_llm
OCR_ENGINE=tesseract
```
Extract text + OCR images → combine → text LLM

### 3. Mixed PDF → Text + Images → Multimodal Vision LLM
```env
EXTRACTION_METHOD=hybrid
LLM_PROCESSING_MODE=multimodal
```
Extract text + convert images → send together to vision LLM

### 4. Mixed PDF → Text to Text LLM + Images to Vision LLM
```env
EXTRACTION_METHOD=hybrid
LLM_PROCESSING_MODE=dual_llm
```
Extract text → text LLM, Convert images → vision LLM, merge results

### 5. Fully Scanned PDF → OCR → Text LLM
```env
EXTRACTION_METHOD=ocr_all
LLM_PROCESSING_MODE=text_llm
OCR_ENGINE=tesseract
```
OCR all pages → text LLM

### 6. Fully Scanned PDF → Vision LLM Direct
```env
EXTRACTION_METHOD=vision_all
LLM_PROCESSING_MODE=vision_llm
```
Convert all to images → vision LLM (no OCR)

## Migration from Old System

| Old Config | New Config |
|------------|------------|
| `EXTRACTION_MODE=text_only` | `EXTRACTION_METHOD=text_direct` + `LLM_PROCESSING_MODE=text_llm` |
| `EXTRACTION_MODE=image_only` | `EXTRACTION_METHOD=ocr_all` + `LLM_PROCESSING_MODE=text_llm` |
| `EXTRACTION_MODE=text_ocr` | `EXTRACTION_METHOD=ocr_images_only` + `LLM_PROCESSING_MODE=text_llm` |
| `EXTRACTION_MODE=multimodal` | `EXTRACTION_METHOD=hybrid` + `LLM_PROCESSING_MODE=multimodal` |
| `EXTRACTION_STRATEGY=gemini_vision` | `EXTRACTION_METHOD=vision_all` + `LLM_PROCESSING_MODE=vision_llm` |

## Benefits of New Architecture

1. **Clear Separation**: Extraction vs Processing are separate concerns
2. **More Flexibility**: Can combine any extraction method with any processing mode
3. **Better Naming**: Method names clearly indicate what they do
4. **Easier to Understand**: No confusion between "mode" and "strategy"
5. **Future-Proof**: Easy to add new extraction methods or processing modes

