# Strategy Factory

## Purpose

The `StrategyFactory` class selects and instantiates the appropriate extractor based on:
- File type (PDF vs DOCX)
- Configuration (`EXTRACTION_STRATEGY`)
- Document type detection (text-based vs image-based PDFs)

## Strategy Selection

### Auto Mode (Default)

1. **DOCX files**: Always use `DOCXExtractor`
2. **PDF files**:
   - Detect PDF type (text vs image vs mixed)
   - Text-based → `PDFExtractor` (text extraction + Gemini Flash)
   - Image-based → Use configured OCR strategy:
     - If `OCR_ENGINE == "gemini_vision"` → `GeminiVisionExtractor`
     - Otherwise → `PDFExtractor` with OCR handler

### Manual Strategy Selection

- `text_extraction`: Force text extraction (PDFExtractor)
- `gemini_vision`: Force Gemini Vision API (GeminiVisionExtractor)
- `tesseract`: Force Tesseract OCR + Gemini Flash
- `gcv`: Force Google Cloud Vision OCR + Gemini Flash

## Usage

```python
from extractors.strategy_factory import StrategyFactory

factory = StrategyFactory(gemini_client=gemini_client)
extractor = factory.get_extractor("/path/to/file.pdf", strategy="auto")
result = extractor.extract("/path/to/file.pdf")
```

## Dependencies

- `PDFExtractor`
- `DOCXExtractor`
- `GeminiVisionExtractor` (optional, for vision strategy)
- `OCRHandler` (optional, for OCR strategies)

## Extension Points

- Add new file type handlers (e.g., `.txt`, `.rtf`)
- Add custom strategy selection logic
- Add strategy-specific configuration options

