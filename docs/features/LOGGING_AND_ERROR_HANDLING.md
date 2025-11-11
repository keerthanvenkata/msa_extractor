# Logging and Error Handling Guide

**Date:** November 11, 2025  
**Status:** Implemented

---

## Overview

The project now has centralized logging and standardized error handling. This makes it easy to:
- Configure logging in one place
- Switch between text and JSON formats
- Control log levels per module
- Handle errors consistently
- Refactor logging later without breaking changes

---

## Logging Infrastructure

### Centralized Configuration

All logging is configured in:
- `config.py` - Logging settings (environment variables)
- `utils/logger.py` - Logging setup and formatters

### Features

1. **Console Logging** (default: enabled)
   - Human-readable format
   - Configurable format (text or JSON)

2. **File Logging** (default: enabled)
   - Location: `logs/msa_extractor_YYYY-MM-DD.log`
   - Daily rotation
   - Size limit: 10MB per file
   - Retention: 30 days
   - Configurable format (text or JSON)

3. **Module-Level Control**
   - Different log levels per module
   - Configurable via environment variables

4. **Structured Logging**
   - JSON format option for log aggregation tools
   - Includes timestamp, level, module, message, exception info

---

## Configuration

### Environment Variables

```bash
# Overall log level
LOG_LEVEL=INFO

# File logging
LOG_FILE_ENABLED=true
LOG_FILE_PATH=./logs
LOG_FILE_FORMAT=text              # text or json
LOG_FILE_ROTATION_DAYS=30
LOG_FILE_MAX_SIZE_MB=10

# Console logging
LOG_CONSOLE_ENABLED=true
LOG_CONSOLE_FORMAT=text           # text or json

# Module-specific levels
LOG_LEVEL_EXTRACTORS=DEBUG
LOG_LEVEL_AI=INFO
LOG_LEVEL_OCR=WARNING
```

### Default Settings

- **Console**: Enabled, INFO level, text format
- **File**: Enabled, INFO level, text format, 30-day retention
- **Module Levels**: 
  - `msa_extractor.extractors`: DEBUG
  - `msa_extractor.ai`: INFO
  - `msa_extractor.extractors.ocr_handler`: WARNING

---

## Usage

### Getting a Logger

```python
from utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Processing file", extra={"file_path": path})
logger.debug("Debug information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

### Logging with Context

```python
logger.info(
    "Extraction started",
    extra={
        "file_path": file_path,
        "strategy": strategy,
        "file_size": file_size
    }
)
```

### JSON Format Example

When `LOG_FILE_FORMAT=json` or `LOG_CONSOLE_FORMAT=json`:

```json
{
  "timestamp": "2025-01-07T14:30:45.123456",
  "level": "INFO",
  "module": "extractors.pdf_extractor",
  "message": "Extraction started",
  "file_path": "/path/to/file.pdf",
  "strategy": "auto"
}
```

---

## Error Handling

### Custom Exception Classes

```python
from utils.exceptions import (
    MSAExtractorError,      # Base exception
    ConfigurationError,     # Config issues
    FileError,              # File problems
    ExtractionError,        # Extraction failures
    OCRError,               # OCR failures
    LLMError,               # LLM API errors
    ValidationError         # Schema validation errors
)
```

### Error Handling Pattern

**For Unrecoverable Errors:**
```python
from utils.exceptions import FileError, ExtractionError

def extract(self, file_path: str) -> ExtractedTextResult:
    try:
        # ... extraction logic
    except FileNotFoundError as e:
        raise FileError(f"File not found: {file_path}", details={"file_path": file_path}) from e
    except Exception as e:
        self.logger.error("Extraction failed", exc_info=True, extra={"file_path": file_path})
        raise ExtractionError(f"Failed to extract from {file_path}") from e
```

**For Recoverable Errors:**
```python
from utils.exceptions import OCRError

def extract_with_fallback(self, file_path: str) -> ExtractedTextResult:
    try:
        return self._extract_primary(file_path)
    except OCRError as e:
        self.logger.warning(f"Primary extraction failed, trying fallback: {e}")
        return self._extract_fallback(file_path)
```

### Exception Details

Exceptions can include additional details:

```python
raise FileError(
    "File validation failed",
    details={
        "file_path": file_path,
        "file_size": file_size,
        "file_type": file_type
    }
)
```

---

## Migration Status

### ✅ Updated Modules

- `main.py` - Uses new logging and exceptions
- `config.py` - Uses ConfigurationError
- `extractors/base_extractor.py` - Uses new logging and FileError

### 🔄 Remaining Modules (Gradual Migration)

These modules still use `logging.getLogger(__name__)` but will work fine:
- `extractors/pdf_extractor.py`
- `extractors/docx_extractor.py`
- `extractors/ocr_handler.py`
- `extractors/gemini_vision_extractor.py`
- `extractors/extraction_coordinator.py`
- `extractors/strategy_factory.py`
- `ai/gemini_client.py`
- `ai/schema.py`
- Others

**Migration Pattern:**
```python
# Old
import logging
logger = logging.getLogger(__name__)

# New
from utils.logger import get_logger
logger = get_logger(__name__)
```

---

## Refactoring Considerations

### Easy to Change

1. **Format Switching**: Change `LOG_FILE_FORMAT` or `LOG_CONSOLE_FORMAT` to switch between text/JSON
2. **Output Toggle**: Set `LOG_FILE_ENABLED=false` or `LOG_CONSOLE_ENABLED=false` to disable
3. **Level Control**: Adjust `LOG_LEVELS` dictionary in `config.py`
4. **Handler Changes**: Modify `utils/logger.py` only

### Backward Compatibility

- Old `logging.getLogger(__name__)` still works
- Centralized logger wraps standard logging
- No breaking changes to existing code
- Gradual migration possible

### Testing

```python
# Mock logger for testing
from unittest.mock import Mock
from utils.logger import get_logger

logger = Mock()
# Use mock logger in tests
```

---

## Best Practices

1. **Use Structured Logging**: Include context in `extra` parameter
2. **Appropriate Levels**: 
   - DEBUG: Detailed diagnostic info
   - INFO: General informational messages
   - WARNING: Warning messages (recoverable issues)
   - ERROR: Error messages (unrecoverable issues)
3. **Exception Handling**: Use custom exceptions for better error tracking
4. **Log Context**: Include relevant context (file_path, strategy, etc.)
5. **Error Details**: Include details in exceptions for debugging

---

## Examples

### Logging Example

```python
from utils.logger import get_logger

logger = get_logger(__name__)

def process_file(file_path: str, strategy: str):
    logger.info(
        "Starting file processing",
        extra={
            "file_path": file_path,
            "strategy": strategy
        }
    )
    
    try:
        # ... processing
        logger.debug("Processing step 1", extra={"step": 1})
        # ... more processing
        logger.info("Processing complete", extra={"file_path": file_path})
    except Exception as e:
        logger.error(
            "Processing failed",
            exc_info=True,
            extra={"file_path": file_path, "strategy": strategy}
        )
        raise
```

### Error Handling Example

```python
from utils.exceptions import FileError, ExtractionError
from utils.logger import get_logger

logger = get_logger(__name__)

def extract_metadata(file_path: str) -> dict:
    # Validate file
    if not Path(file_path).exists():
        raise FileError(f"File not found: {file_path}", details={"file_path": file_path})
    
    try:
        # ... extraction
        return metadata
    except ValueError as e:
        logger.error("Invalid file format", exc_info=True, extra={"file_path": file_path})
        raise FileError(f"Invalid file format: {file_path}") from e
    except Exception as e:
        logger.error("Extraction failed", exc_info=True, extra={"file_path": file_path})
        raise ExtractionError(f"Failed to extract metadata from {file_path}") from e
```

---

## Next Steps

1. Gradually migrate remaining modules to use `get_logger()`
2. Update error handling in key modules to use custom exceptions
3. Add error recovery strategies where appropriate
4. Add logging tests
5. Document error handling patterns in coding guidelines

---

## References

- `utils/logger.py` - Logging implementation
- `utils/exceptions.py` - Exception classes
- `config.py` - Logging configuration
- `docs/LOGGING_AND_ERROR_HANDLING_PLAN.md` - Design document

