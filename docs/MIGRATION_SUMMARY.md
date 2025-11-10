# Logging and Error Handling Migration Summary

**Date:** 2025-01-07  
**Status:** ✅ Complete

---

## Migration Overview

All modules have been successfully migrated to use centralized logging and custom exception classes.

---

## Modules Migrated

### ✅ Core Modules
- `main.py` - CLI entry point
- `config.py` - Configuration and validation
- `extractors/base_extractor.py` - Base extractor class
- `extractors/pdf_extractor.py` - PDF extraction
- `extractors/docx_extractor.py` - DOCX extraction
- `extractors/extraction_coordinator.py` - Pipeline orchestration
- `extractors/strategy_factory.py` - Strategy selection
- `extractors/ocr_handler.py` - OCR operations
- `extractors/gemini_vision_extractor.py` - Gemini Vision extraction
- `extractors/image_preprocessor.py` - Image preprocessing
- `extractors/text_analyzer.py` - Text analysis
- `ai/gemini_client.py` - Gemini API client
- `ai/schema.py` - Schema validation

### ✅ Infrastructure
- `utils/logger.py` - Centralized logging
- `utils/exceptions.py` - Custom exceptions
- `utils/__init__.py` - Module exports

---

## Changes Made

### Logging Migration

**Before:**
```python
import logging
logger = logging.getLogger(__name__)
```

**After:**
```python
from utils.logger import get_logger
logger = get_logger(__name__)
```

### Error Handling Migration

**Before:**
```python
raise ValueError("Error message")
raise FileNotFoundError("File not found")
raise RuntimeError("Runtime error")
```

**After:**
```python
from utils.exceptions import FileError, ExtractionError, ConfigurationError, OCRError, LLMError

raise FileError("File not found", details={"file_path": path})
raise ConfigurationError("Config error", details={"key": value})
raise ExtractionError("Extraction failed", details={"file_path": path})
```

---

## Error Handling Patterns

### Unrecoverable Errors → Raise Exceptions

**File Errors:**
- File not found → `FileError`
- Invalid file format → `FileError`
- Encrypted PDF → `FileError`
- Unsupported file type → `FileError`

**Configuration Errors:**
- Missing API key → `ConfigurationError`
- Invalid strategy → `ConfigurationError`
- Unknown OCR engine → `ConfigurationError`

**Extraction Errors:**
- PDF parsing failure → `ExtractionError`
- DOCX parsing failure → `ExtractionError`
- General extraction failure → `ExtractionError`

**OCR Errors:**
- Tesseract not found → `OCRError`
- GCV not configured → `OCRError`
- OCR operation failed → `OCRError`

**LLM Errors:**
- API authentication failure → `LLMError`
- API call failure → `LLMError`
- Response parsing failure → `LLMError` (or return empty schema as fallback)

### Recoverable Errors → Return Fallback

**JSON Parsing Errors:**
- LLM returns invalid JSON → Return empty schema (logged as error)

**Empty Text:**
- No text extracted → Return empty schema (logged as warning)

---

## Exception Details

All custom exceptions support a `details` dictionary for additional context:

```python
raise FileError(
    "File not found",
    details={
        "file_path": file_path,
        "file_size": file_size,
        "file_type": file_type
    }
)
```

This makes debugging easier and provides structured error information.

---

## Logging Features

### Console Logging
- **Format**: Human-readable text (default) or JSON
- **Level**: Configurable per module
- **Enabled**: By default

### File Logging
- **Location**: `logs/msa_extractor_YYYY-MM-DD.log`
- **Format**: Human-readable text (default) or JSON
- **Rotation**: Daily + size-based (10MB)
- **Retention**: 30 days
- **Enabled**: By default

### Module-Level Control
- Different log levels per module
- Configurable via environment variables
- Default: DEBUG for extractors, INFO for AI, WARNING for OCR

---

## Configuration

All logging settings are in `config.py` and can be controlled via environment variables:

```bash
LOG_LEVEL=INFO
LOG_FILE_ENABLED=true
LOG_FILE_FORMAT=text
LOG_CONSOLE_ENABLED=true
LOG_CONSOLE_FORMAT=text
LOG_LEVEL_EXTRACTORS=DEBUG
LOG_LEVEL_AI=INFO
LOG_LEVEL_OCR=WARNING
```

---

## Benefits

1. **Centralized Configuration**: Single place to configure logging
2. **Easy Refactoring**: Change format/output in one place
3. **Structured Logging**: JSON format option for log aggregation
4. **Better Error Tracking**: Custom exceptions with details
5. **Consistent Patterns**: Standardized error handling
6. **Production-Ready**: File rotation, size limits, retention

---

## Testing

All modules pass linting. The migration is complete and ready for testing.

---

## Next Steps

1. Test logging output (console and file)
2. Test error handling with various error scenarios
3. Verify log rotation works correctly
4. Test JSON format output
5. Verify module-level log levels work correctly

---

## Notes

- Old `logging.getLogger(__name__)` still works (backward compatible)
- Gradual migration was possible without breaking changes
- All custom exceptions inherit from `MSAExtractorError` for easy catching
- Exception details are logged automatically when using structured logging

