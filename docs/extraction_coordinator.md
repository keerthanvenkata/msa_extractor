# Extraction Coordinator

## Purpose

The `ExtractionCoordinator` class orchestrates the complete extraction pipeline:
1. Text extraction (PDF/DOCX)
2. OCR processing (for scanned PDFs)
3. LLM-based metadata extraction
4. Schema validation and normalization

This is the **main entry point** for the extraction system.

## Pipeline Flow

### For Text-Based Documents

```
Document → Text Extraction → Gemini Flash → Metadata
```

### For Image-Based Documents (OCR Strategy)

```
Document → Image Conversion → Preprocessing → OCR → Gemini Flash → Metadata
```

### For Image-Based Documents (Gemini Vision Strategy)

```
Document → Image Conversion → Gemini Vision → Metadata (direct)
```

## Key Methods

### `extract_metadata(file_path, strategy=None)`

Main entry point that:
- Detects document type
- Routes to appropriate extractor
- Handles OCR if needed
- Processes with LLM
- Returns structured metadata

**Returns**: Dictionary matching the metadata schema

## Usage

```python
from extractors.extraction_coordinator import ExtractionCoordinator

coordinator = ExtractionCoordinator()
metadata = coordinator.extract_metadata("/path/to/contract.pdf")
```

## Error Handling

- Validates configuration before processing
- Handles extraction errors gracefully
- Returns empty schema on failure (all fields = "Not Found")
- Logs errors for debugging

## Dependencies

- `StrategyFactory` (for extractor selection)
- `OCRHandler` (for OCR processing)
- `GeminiClient` (for LLM processing)
- All extractor modules

## Integration Points

- Used by `main.py` CLI
- Can be used by Streamlit UI
- Can be integrated into batch processing workflows

