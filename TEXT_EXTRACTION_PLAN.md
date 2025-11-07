# Text Extraction System Plan

## Overview

This plan outlines the implementation of a robust text extraction system that handles:
- **Electronically created PDFs** (text-based documents)
- **Scanned PDFs** (image-based documents requiring OCR)
- **DOCX files** (Microsoft Word documents)
- **Header/Title detection** and structure preservation
- **Accurate text extraction** with formatting awareness
- **Multiple extraction strategies** - users can choose their preferred pipeline

## Feasibility Assessment

### ✅ YES, it's feasible to build an accurate PDF text extraction system

**Why:**
1. **PyMuPDF** provides rich text metadata (font size, style, position) enabling header detection
2. **OCR libraries** (Tesseract, Google Vision) can handle scanned documents
3. **Heuristic-based detection** can identify headers using font properties
4. **python-docx** preserves structure better than PDF extraction for DOCX files

**Accuracy Considerations:**
- Electronically created PDFs: **High accuracy** (90-95%+) - text is directly extractable
- Scanned PDFs: **Moderate to high accuracy** (80-90%) - depends on image quality and OCR
- Header detection: **Good accuracy** (85-90%) - using font size/style heuristics
- Structure preservation: **Moderate** - PDFs lose some structure, DOCX preserves better

## Architecture Design

### Module Structure

```
extractors/
├── base_extractor.py      # Abstract base class for all extractors
├── pdf_extractor.py       # PDF extraction (text + OCR fallback)
├── docx_extractor.py      # DOCX extraction
├── ocr_handler.py         # OCR wrapper (Tesseract/Google Vision/Gemini Vision)
├── text_analyzer.py       # Header detection and structure analysis
├── image_preprocessor.py  # OpenCV image preprocessing for OCR
└── strategy_factory.py   # Factory for selecting extraction strategy
```

### Extraction Strategies

The system supports multiple extraction strategies that users can configure based on document type:

#### For Text-Based Documents (Electronically Created PDFs & DOCX)

**Strategy 1: Text Extraction + Gemini Flash (Text LLM)**
- **PDF**: PyMuPDF extracts text with font properties
- **DOCX**: python-docx extracts text with style information
- **Processing**: Gemini Flash (text model) processes extracted text for metadata
- **Best for**: Electronically created PDFs and DOCX files
- **Pros**: Fast text extraction, preserves formatting, cost-effective LLM processing
- **Cons**: Doesn't work for scanned/image-based documents
- **Use case**: Standard contracts, digitally created documents

#### For Image-Based Documents (Scanned PDFs)

**Strategy 2: Direct Gemini Vision API**
- Send PDF pages/images directly to Gemini Vision model
- Single API call handles OCR + text extraction + understanding
- **Best for**: Scanned PDFs, image-based documents
- **Pros**: Single API, excellent accuracy, understands context and structure
- **Cons**: API costs, requires internet, rate limits
- **Use case**: Scanned contracts, image PDFs, high-accuracy requirements

**Strategy 3: Google Cloud Vision OCR + Gemini Flash (Text LLM)**
- Convert PDF pages to images using PyMuPDF
- OpenCV preprocesses images (deskew, denoise, enhance) - optional
- Google Cloud Vision API performs OCR
- Gemini Flash (text model) processes OCR-extracted text for metadata
- **Best for**: Scanned PDFs requiring high OCR accuracy
- **Pros**: Very accurate OCR, handles complex layouts, cost-effective LLM processing
- **Cons**: API costs (GCV), requires internet, Google Cloud setup
- **Use case**: Production environments, complex layouts, high volume

**Strategy 4: Tesseract OCR + Gemini Flash (Text LLM)**
- Convert PDF pages to images using PyMuPDF
- OpenCV preprocesses images (deskew, denoise, enhance) - recommended
- Tesseract performs OCR on preprocessed images
- Gemini Flash (text model) processes OCR-extracted text for metadata
- **Best for**: Scanned PDFs, local processing, cost-effective
- **Pros**: Free OCR, local processing, offline capable, good accuracy with preprocessing
- **Cons**: Requires Tesseract installation, slower than cloud OCR, more complex setup
- **Use case**: Development, testing, offline processing, budget-conscious production

#### Strategy Selection Logic

**Auto Mode (Recommended):**
1. Detect document type (text-based vs image-based)
2. For text-based: Use Strategy 1 (Text Extraction + Gemini Flash)
3. For image-based: Use configured OCR strategy (Strategy 2, 3, or 4)
4. Fallback: If text extraction fails, automatically switch to OCR strategy

### Data Structures

**ExtractedTextResult:**
```python
{
    "raw_text": str,                    # Plain text without structure
    "structured_text": list,            # List of TextBlock objects
    "headers": list,                    # List of Header objects
    "metadata": {
        "file_type": str,               # "pdf" or "docx"
        "is_scanned": bool,             # True if OCR was used
        "page_count": int,
        "extraction_method": str,       # "text", "ocr", "gemini_vision", etc.
        "extraction_strategy": str,     # Strategy used: "gemini_vision", "tesseract", "gcv", "pymupdf"
        "confidence": float             # Overall confidence score (0-1)
    }
}
```

**TextBlock:**
```python
{
    "text": str,
    "type": str,                        # "header", "title", "body", "footer"
    "level": int,                       # Header level (1-6, 0 for body)
    "font_size": float,
    "font_name": str,
    "is_bold": bool,
    "is_italic": bool,
    "page_number": int,
    "bbox": tuple,                      # (x0, y0, x1, y1)
}
```

## Implementation Plan

### Phase 1: Base Infrastructure

**1.1 Create Base Extractor Class** (`extractors/base_extractor.py`)
- Abstract base class defining interface
- Common methods: `extract()`, `validate_file()`, `get_metadata()`
- Error handling and logging
- Strategy selection support

**1.2 Create Strategy Factory** (`extractors/strategy_factory.py`)
- Factory pattern for selecting extraction strategy
- Strategy registration and selection
- Configuration-based strategy selection
- Fallback strategy handling

**1.3 Create Text Analyzer** (`extractors/text_analyzer.py`)
- Header detection heuristics
- Font analysis utilities
- Structure classification logic

### Phase 2: PDF Extraction (Text-Based) + Gemini Flash

**2.1 PDF Text Extractor** (`extractors/pdf_extractor.py`)

**Core Functionality:**
- Use PyMuPDF to extract text with font properties
- Extract text blocks with metadata:
  - Font size, name, style (bold/italic)
  - Position (bounding box)
  - Page number
- **Output**: Extracted text → passed to Gemini Flash (text LLM) for metadata extraction

**Implementation Steps:**
1. Open PDF with `fitz.open()`
2. Iterate through pages
3. Use `page.get_text("dict")` to get structured text with properties
4. Extract spans with font information
5. Classify text blocks (header vs body) using heuristics
6. Combine extracted text into full document text
7. **Pass to Gemini Flash** (text LLM) for metadata extraction
8. Return structured result with metadata

**Header Detection Heuristics:**
- **Font Size Analysis:**
  - Calculate median font size for body text
  - Headers typically 1.2x - 2.5x larger than body
  - Top 10-15% of font sizes likely headers
  
- **Position Analysis:**
  - Headers often at top of page or section
  - More whitespace above/below headers
  
- **Style Analysis:**
  - Bold text more likely to be headers
  - Centered text often titles/headers
  
- **Pattern Matching:**
  - Section numbers (e.g., "Section 12", "Article 3")
  - All caps text often headers
  - Short lines (1-2 words) at start of block

**Code Structure:**
```python
class PDFExtractor(BaseExtractor):
    def __init__(self, gemini_client=None):
        # Initialize Gemini Flash client for text processing
        self.gemini_client = gemini_client
    
    def extract(self, file_path: str) -> ExtractedTextResult:
        # 1. Detect if PDF has text or is scanned
        # 2. If text-based: extract with PyMuPDF
        # 3. Analyze text blocks for headers
        # 4. Combine text for LLM processing
        # 5. Pass to Gemini Flash (text LLM) for metadata extraction
        # 6. Structure the output
        pass
    
    def _extract_text_blocks(self, doc) -> list:
        # Extract text with font properties
        pass
    
    def _detect_scanned_pdf(self, doc) -> bool:
        # Check if PDF has extractable text
        # If no text or very little text, likely scanned
        pass
    
    def _process_with_gemini_flash(self, text: str) -> dict:
        # Send extracted text to Gemini Flash (text LLM)
        # Extract metadata according to schema
        pass
```

### Phase 3: OCR Integration (Scanned PDFs)

**3.1 Image Preprocessor** (`extractors/image_preprocessor.py`)

**OpenCV Image Preprocessing:**
- Deskew images (rotate to correct orientation)
- Denoise (remove noise from scanned images)
- Enhance contrast and brightness
- Binarization (convert to black/white for better OCR)
- Resize for optimal OCR performance

**Code Structure:**
```python
class ImagePreprocessor:
    def __init__(self):
        # Initialize OpenCV
        pass
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        # Apply preprocessing pipeline
        pass
    
    def deskew(self, image: np.ndarray) -> np.ndarray:
        # Correct image rotation
        pass
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        # Remove noise
        pass
```

**3.2 OCR Handler** (`extractors/ocr_handler.py`)

**Supported OCR Engines:**
1. **Tesseract OCR** (pytesseract)
   - Free, open-source, local
   - Pros: No API costs, works offline, good accuracy with preprocessing
   - Cons: Requires Tesseract installation, slower than cloud OCR
   - Output: Extracted text → passed to Gemini Flash (text LLM)
   
2. **Google Cloud Vision API**
   - Cloud-based, high accuracy
   - Pros: Very accurate, handles complex layouts, production-ready
   - Cons: Requires API key, costs per page, needs internet
   - Output: Extracted text → passed to Gemini Flash (text LLM)
   
3. **Gemini Vision API** (Direct)
   - Direct vision model for OCR + understanding in one call
   - Pros: Excellent accuracy, understands context, single API, no separate OCR step
   - Cons: API costs, requires internet, rate limits
   - Output: Direct structured output (no separate text LLM step needed)

**Implementation Strategy:**
- Support all three engines
- User selects via configuration
- Factory pattern for engine selection
- Preprocessing with OpenCV before Tesseract/GCV (optional, configurable)
- **Note**: Tesseract and GCV output text → Gemini Flash processes it
- **Note**: Gemini Vision outputs structured data directly (no text LLM step)

**Code Structure:**
```python
class OCRHandler:
    def __init__(self, ocr_engine: str = "tesseract", preprocess: bool = True):
        # Initialize OCR engine
        # Initialize image preprocessor if needed
        pass
    
    def extract_text_from_image(self, image_path: str) -> str:
        # Preprocess image if enabled
        # Run OCR and return text
        pass
    
    def extract_text_with_layout(self, image_path: str) -> list:
        # Return text with position information
        pass
    
    def _extract_with_tesseract(self, image: np.ndarray) -> str:
        # Tesseract OCR
        pass
    
    def _extract_with_gcv(self, image: np.ndarray) -> str:
        # Google Cloud Vision OCR
        pass
    
    def _extract_with_gemini_vision(self, image: np.ndarray) -> str:
        # Gemini Vision API OCR
        pass
```

**3.3 Gemini Vision Integration** (`extractors/gemini_vision_extractor.py`)

**Direct Gemini Vision API for PDF/Image Processing:**
- Send PDF pages or images directly to Gemini Vision model
- Model performs OCR + text extraction + understanding in one call
- Can extract structured information directly (no separate text LLM step)
- Best for: Scanned PDFs, image-based documents, high accuracy requirements
- **Note**: This is a complete solution - no need for separate OCR or text LLM steps

**Code Structure:**
```python
class GeminiVisionExtractor:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        # Initialize Gemini Vision client
        pass
    
    def extract_from_pdf(self, pdf_path: str) -> ExtractedTextResult:
        # Convert PDF pages to images using PyMuPDF
        # Send each page to Gemini Vision
        # Extract text + structure + metadata in one call
        pass
    
    def extract_from_image(self, image_path: str) -> ExtractedTextResult:
        # Send image to Gemini Vision
        # Extract text + structure + metadata
        pass
    
    def extract_with_metadata_prompt(self, image: bytes, prompt: str) -> dict:
        # Send image + prompt to Gemini Vision
        # Extract structured metadata directly
        pass
```

**3.4 PDF OCR Integration** (`extractors/pdf_extractor.py`)

**For Image-Based PDFs:**
- Detect scanned PDFs (no extractable text)
- Convert PDF pages to images using PyMuPDF
- Select OCR strategy based on configuration:
  - **Gemini Vision** (direct): Single API call, no separate text LLM needed
  - **Tesseract + Gemini Flash**: OCR → text → Gemini Flash (text LLM)
  - **Google Cloud Vision + Gemini Flash**: OCR → text → Gemini Flash (text LLM)
- Reconstruct text with approximate structure
- Note: OCR loses precise formatting, but text is extractable

**For Text-Based PDFs:**
- Extract text directly with PyMuPDF (preserves font properties)
- Pass extracted text to Gemini Flash (text LLM) for metadata extraction
- No OCR needed

### Phase 4: DOCX Extraction + Gemini Flash

**4.1 DOCX Extractor** (`extractors/docx_extractor.py`)

**Advantages of DOCX:**
- Better structure preservation than PDF
- Native header styles (Heading 1, Heading 2, etc.)
- Paragraph-level formatting information

**Implementation:**
1. Use python-docx to parse document
2. Iterate through paragraphs
3. Check paragraph style (Heading 1, Heading 2, Normal, etc.)
4. Extract text with style information
5. Preserve structure better than PDF
6. **Combine extracted text**
7. **Pass to Gemini Flash** (text LLM) for metadata extraction
8. Return structured result with metadata

**Code Structure:**
```python
class DOCXExtractor(BaseExtractor):
    def __init__(self, gemini_client=None):
        # Initialize Gemini Flash client for text processing
        self.gemini_client = gemini_client
    
    def extract(self, file_path: str) -> ExtractedTextResult:
        # 1. Open DOCX with python-docx
        # 2. Extract paragraphs with styles
        # 3. Classify headers based on style names
        # 4. Combine text for LLM processing
        # 5. Pass to Gemini Flash (text LLM) for metadata extraction
        # 6. Structure the output
        pass
    
    def _classify_paragraph(self, paragraph) -> TextBlock:
        # Check paragraph.style.name
        # "Heading 1" -> level 1 header
        # "Heading 2" -> level 2 header
        # etc.
        pass
    
    def _process_with_gemini_flash(self, text: str) -> dict:
        # Send extracted text to Gemini Flash (text LLM)
        # Extract metadata according to schema
        pass
```

### Phase 5: Text Analysis & Structure

**5.1 Header Detection Logic** (`extractors/text_analyzer.py`)

**Heuristic Rules:**
1. **Font Size Threshold:**
   - Calculate font size distribution
   - Identify outliers (larger sizes = headers)
   
2. **Style Indicators:**
   - Bold text more likely header
   - Italic less likely (often emphasis)
   
3. **Position Indicators:**
   - Text at top of page/section
   - Centered text
   - More whitespace around
   
4. **Content Patterns:**
   - Section numbers ("Section 12", "Article 3.1")
   - All caps
   - Short lines (1-3 words)
   
5. **Hierarchy Detection:**
   - Multiple header levels
   - Larger font = higher level
   - Sequential numbering indicates hierarchy

**Implementation:**
```python
class TextAnalyzer:
    def detect_headers(self, text_blocks: list) -> list:
        # Apply heuristics to classify headers
        pass
    
    def assign_header_levels(self, headers: list) -> list:
        # Assign hierarchical levels (1-6)
        pass
    
    def structure_text(self, blocks: list) -> dict:
        # Organize text into hierarchical structure
        pass
```

## Accuracy Improvements

### For Electronically Created PDFs:
- ✅ Use PyMuPDF's rich metadata (font properties)
- ✅ Analyze font size distributions
- ✅ Check style attributes (bold, italic)
- ✅ Consider position and whitespace
- **Expected Accuracy: 85-95%** for header detection

### For Scanned PDFs:
- ✅ Use high-quality OCR (Tesseract 4.0+ or Google Vision)
- ✅ Pre-process images (deskew, denoise)
- ⚠️ OCR loses precise formatting (font sizes approximate)
- ⚠️ Header detection less accurate (rely on position/patterns)
- **Expected Accuracy: 70-85%** for header detection

### For DOCX Files:
- ✅ Use native style information (Heading 1, Heading 2, etc.)
- ✅ Preserve exact structure
- **Expected Accuracy: 95%+** for header detection

## Error Handling & Edge Cases

1. **No extractable text in PDF:**
   - Detect and fall back to OCR
   - Log warning about scanned document

2. **Mixed PDFs (some pages scanned, some text):**
   - Extract text where possible
   - Use OCR for scanned pages
   - Combine results

3. **Poor quality scanned PDFs:**
   - Log quality warnings
   - Return extracted text with confidence flags
   - Allow manual review

4. **Unusual formatting:**
   - Fall back to basic text extraction
   - Log formatting issues
   - Return raw text if structure detection fails

5. **Encrypted/Password-protected PDFs:**
   - Detect and raise clear error
   - Provide helpful error message

## Testing Strategy

1. **Unit Tests:**
   - Test header detection heuristics
   - Test text extraction from sample PDFs/DOCX
   - Test OCR integration
   - Test edge cases (empty files, corrupted files)

2. **Integration Tests:**
   - Test full extraction pipeline
   - Test with various PDF types (text, scanned, mixed)
   - Test with various DOCX formats

3. **Sample Documents:**
   - Create test suite with:
     - Electronically created PDFs
     - Scanned PDFs (various qualities)
     - DOCX files with different styles
     - Edge cases (minimal text, unusual formatting)

## Dependencies to Add

**For OCR and Image Processing:**
```
# Tesseract OCR (optional - for Strategy 2)
pytesseract==0.3.10

# OpenCV for image preprocessing (optional - for Strategy 2)
opencv-python==4.8.1.78

# Pillow for image processing (required for OCR strategies)
Pillow==10.1.0

# Google Cloud Vision (optional - for Strategy 3)
google-cloud-vision==3.4.5

# NumPy for image processing (required for OpenCV)
numpy==1.24.3
```

**Note:** 
- Tesseract binary must be installed separately:
  - Windows: Download from GitHub releases
  - macOS: `brew install tesseract`
  - Linux: `apt-get install tesseract-ocr`
- Google Cloud Vision requires service account credentials
- Gemini Vision uses existing `google-generativeai` package

## Configuration

**Extraction Strategy Selection** (via `config.py`):

```python
# Extraction strategy configuration
EXTRACTION_STRATEGY = os.getenv("EXTRACTION_STRATEGY", "auto")
# Options: "auto", "text_extraction", "gemini_vision", "tesseract", "gcv"

# Auto mode: 
#   - Text-based PDFs/DOCX → Text Extraction + Gemini Flash
#   - Image-based PDFs → Use configured OCR strategy
# text_extraction: Text Extraction + Gemini Flash (for text-based docs only)
# gemini_vision: Gemini Vision API directly (for image-based docs)
# tesseract: Tesseract OCR + Gemini Flash (for image-based docs)
# gcv: Google Cloud Vision OCR + Gemini Flash (for image-based docs)

# OCR Engine (for image-based PDFs when not using Gemini Vision)
OCR_ENGINE = os.getenv("OCR_ENGINE", "tesseract")
# Options: "tesseract", "gcv"
# Note: "gemini_vision" is handled separately (no OCR step needed)

# Image Preprocessing (for Tesseract and GCV OCR)
ENABLE_IMAGE_PREPROCESSING = os.getenv("ENABLE_IMAGE_PREPROCESSING", "true").lower() == "true"
# Applies OpenCV preprocessing (deskew, denoise, enhance) before OCR

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Required for all Gemini strategies
GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash")  # For text LLM
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-flash")  # For vision LLM

# Google Cloud Vision Configuration (for Strategy 3)
GCV_CREDENTIALS_PATH = os.getenv("GCV_CREDENTIALS_PATH", "")
GCV_PROJECT_ID = os.getenv("GCV_PROJECT_ID", "")
```

## Implementation Order

1. ✅ Base extractor class
2. ✅ Strategy factory for extraction method selection
3. ✅ Text analyzer (header detection heuristics)
4. ✅ Image preprocessor (OpenCV)
5. ✅ PDF extractor (text-based with PyMuPDF)
6. ✅ OCR handler (Tesseract, Google Cloud Vision, Gemini Vision)
7. ✅ Gemini Vision extractor (direct API integration)
8. ✅ DOCX extractor
9. ✅ PDF OCR integration with strategy selection
10. ✅ Configuration management
11. ✅ Testing and refinement

## Strategy Comparison

### For Text-Based Documents (PDF/DOCX)

| Strategy | Accuracy | Speed | Cost | Offline | Setup Complexity |
|----------|----------|-------|------|---------|------------------|
| **Text Extraction + Gemini Flash** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 💰 | ✅* | ⭐⭐ |

*Text extraction works offline; Gemini Flash requires internet

### For Image-Based Documents (Scanned PDFs)

| Strategy | Accuracy | Speed | Cost | Offline | Setup Complexity |
|----------|----------|-------|------|---------|------------------|
| **Gemini Vision** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 💰💰 | ❌ | ⭐⭐ |
| **Tesseract OCR + Gemini Flash** | ⭐⭐⭐ | ⭐⭐ | 💰 | ✅* | ⭐⭐⭐ |
| **Google Cloud Vision + Gemini Flash** | ⭐⭐⭐⭐ | ⭐⭐⭐ | 💰💰 | ❌ | ⭐⭐⭐ |

*OCR works offline; Gemini Flash requires internet

**Recommendations:**

**For Text-Based Documents:**
- **All cases**: Text Extraction + Gemini Flash (fast, accurate, cost-effective)

**For Image-Based Documents:**
- **Development/Testing**: Tesseract OCR + Gemini Flash (free OCR, local processing)
- **Production (High Volume)**: Google Cloud Vision OCR + Gemini Flash (best OCR accuracy)
- **Production (Simple Setup)**: Gemini Vision (single API, excellent results, no separate OCR step)
- **Budget-Conscious**: Tesseract OCR + Gemini Flash (free OCR, good accuracy with preprocessing)

## Future Enhancements (Phase 2)

- Machine learning-based header detection
- Better OCR pre-processing (advanced image enhancement)
- Multi-column layout handling
- Table extraction and preservation
- Confidence scoring for extracted text
- Hybrid strategies (combine multiple OCR engines)
- Caching for repeated document processing

## Summary

**Feasibility: ✅ YES**

- Electronically created PDFs: **High accuracy** achievable
- Scanned PDFs: **Moderate-high accuracy** with OCR (varies by strategy)
- Header detection: **Good accuracy** with heuristics
- DOCX files: **Very high accuracy** with native styles

**Key Features:**
- ✅ Multiple extraction strategies (user-selectable)
- ✅ Direct Gemini Vision API support
- ✅ OpenCV image preprocessing for better OCR
- ✅ Modular architecture (easy to add new strategies)
- ✅ Configuration-based strategy selection
- ✅ Automatic fallback for scanned documents

The system will be modular, allowing easy improvements and extensions. Users can choose their preferred extraction strategy based on accuracy, cost, and setup requirements. Header detection will use multiple heuristics for robustness, and OCR integration provides fallback for scanned documents.

