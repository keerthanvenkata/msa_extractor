# OCR and Signature Extraction

## Can Tesseract OCR Extract Signatures?

### Short Answer
**Tesseract OCR can extract printed/typed text near signatures, but cannot read handwritten signatures themselves.**

### Detailed Explanation

#### What OCR Can Extract:
1. **Printed/typed names** - Text that appears near signature lines (e.g., "John Doe" printed above a signature line)
2. **Signature labels** - Text like "Signature:", "Authorized Signatory:", "Date:"
3. **Dates** - Typed dates near signatures
4. **Company names** - Printed company names and titles
5. **Witness information** - Printed witness names and information

#### What OCR Cannot Extract:
1. **Handwritten signatures** - The actual signature strokes/curves are not readable by OCR
2. **Handwritten text** - Cursive or handwritten names are typically not readable
3. **Low-quality images** - Blurry or low-resolution signature images
4. **Complex backgrounds** - Signatures on complex backgrounds may not be detected

### Best Approach for Signature Extraction

For extracting signatory information from signature pages, we recommend:

1. **Multimodal Mode** (Recommended):
   - Uses Gemini Vision API which can analyze images directly
   - Can read both printed text AND handwritten signatures
   - Better context understanding
   - Can identify signature locations and extract surrounding text

2. **OCR Mode** (Fallback):
   - Extracts printed/typed text near signatures
   - May miss handwritten signatures
   - Good for typed signature blocks

### Example Scenarios

#### Scenario 1: Typed Signature Block
```
Signature: John Doe
Title: VP of Operations
Date: 2025-03-14
```
**OCR Result:** ✅ Can extract all information

#### Scenario 2: Handwritten Signature
```
Signature: [handwritten signature]
Name: John Doe (printed)
Date: 2025-03-14 (printed)
```
**OCR Result:** ✅ Can extract printed name and date, ❌ Cannot read handwritten signature

#### Scenario 3: Pure Image Signature Page
```
[Image of signature page with handwritten signatures]
```
**OCR Result:** ⚠️ May extract some text if present, but handwritten signatures not readable

**Multimodal Result:** ✅ Can analyze image and extract signatory information

## Current Implementation

### Text + OCR Mode (`text_ocr`)
When a PDF has both text pages and image pages:
1. Text pages are extracted directly
2. Image pages are converted to images
3. OCR is run on image pages
4. OCR text is appended to the extracted text
5. Combined text is sent to text LLM

**Use Case:** When you want to extract all text content, including text from image pages, before sending to the text LLM.

### Multimodal Mode (`multimodal`)
When a PDF has both text pages and image pages:
1. Text pages are extracted directly
2. Image pages are converted to images
3. Text + images are sent together to Gemini Vision API
4. Vision model analyzes both text and images in context

**Use Case:** Best for signature pages where you need to extract signatory information.

## Handling Pure Images (No Text)

### Current Behavior
When an image page has no extractable text:
- OCR returns empty string
- System logs: `[Page X - Image Page (No extractable text found)]`
- Page is documented in the extracted text

### Future Enhancement
For pure images without text, we plan to:
1. Document image presence
2. Add image dimensions (width x height)
3. Add image metadata (format, size, etc.)
4. Optionally store image thumbnails

**Status:** 📋 Planned for future iteration

## Recommendations

1. **For Signature Pages:**
   - Use `multimodal` mode for best results
   - Vision API can read both printed and handwritten text
   - Better context understanding

2. **For General Mixed PDFs:**
   - Use `text_ocr` mode
   - OCR extracts text from image pages
   - Combined text sent to text LLM

3. **For Fully Scanned Documents:**
   - Use `image_only` mode
   - OCR all pages
   - Send OCR text to text LLM

4. **For Text-Only Documents:**
   - Use `text_only` mode
   - Skip image processing
   - Fastest extraction

## Configuration

Set in `.env`:
```env
EXTRACTION_MODE=multimodal  # For signature pages
# or
EXTRACTION_MODE=text_ocr    # For general mixed PDFs
```

## Troubleshooting

### Issue: Signatory information not extracted from signature page

**Possible causes:**
1. Using `text_only` mode (skips image pages)
2. Using `text_ocr` mode with handwritten signatures (OCR can't read handwriting)
3. Image quality too low
4. Signature page not detected

**Solutions:**
1. Use `multimodal` mode for signature pages
2. Check image quality (increase `PDF_PREPROCESSING_DPI`)
3. Verify signature page is detected (check logs)
4. Ensure signature page is in last 2 pages (system checks last 2 pages by default)

### Issue: OCR returns empty for image page

**Possible causes:**
1. Pure image with no text
2. Image quality too low
3. Handwritten text (not readable by OCR)
4. Complex background

**Solutions:**
1. Use `multimodal` mode instead of OCR
2. Increase image preprocessing (enable `ENABLE_IMAGE_PREPROCESSING`)
3. Increase DPI (`PDF_PREPROCESSING_DPI=400`)
4. Check if image has any text at all (may be pure image)

