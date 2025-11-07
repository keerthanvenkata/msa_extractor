# Logging and Error Handling Plan

**Date:** 2025-01-07  
**Status:** Design Phase

---

## Current State

### Logging
- Basic `logging.basicConfig()` in `main.py`
- Each module creates logger with `logging.getLogger(__name__)`
- No centralized configuration
- No file logging
- No log rotation
- No structured logging

### Error Handling
- Inconsistent patterns:
  - Some methods return empty schema on error
  - Some methods raise exceptions
  - Some methods return empty string
  - No standard error types
  - No error recovery strategies

---

## Design Goals

1. **Centralized Configuration**: Single place to configure logging
2. **Easy Refactoring**: Configuration-based, dependency injection
3. **Structured Logging**: JSON format option for parsing
4. **File Logging**: With rotation
5. **Module-Level Control**: Different log levels per module
6. **Standardized Errors**: Custom exception classes
7. **Consistent Patterns**: Clear error handling strategy

---

## Logging Architecture

### Option 1: Centralized Logger Module (Recommended)

**Structure:**
```
utils/
  __init__.py
  logger.py          # Centralized logging configuration
  exceptions.py      # Custom exception classes
```

**Pros:**
- ✅ Single source of truth
- ✅ Easy to configure
- ✅ Easy to refactor
- ✅ Can switch between formats (text/JSON)
- ✅ Module-level control

**Cons:**
- ⚠️ Need to import from utils

### Option 2: Configuration-Based (Alternative)

**Structure:**
```
config.py            # Add logging config
utils/logger.py      # Logger factory
```

**Pros:**
- ✅ Configuration in config.py
- ✅ Environment variable support

**Cons:**
- ⚠️ Mixes concerns (config + logging)

**Recommendation:** Option 1 - Cleaner separation

---

## Logging Features

### 1. Log Levels Per Module
```python
LOG_LEVELS = {
    "msa_extractor": "INFO",
    "msa_extractor.extractors": "DEBUG",
    "msa_extractor.ai": "INFO",
    "msa_extractor.extractors.ocr_handler": "WARNING"
}
```

### 2. Output Formats
- **Console**: Human-readable format (default)
- **File**: Human-readable or JSON (configurable)
- **JSON**: Structured format for log aggregation tools

### 3. File Logging
- **Location**: `logs/` directory
- **Naming**: `msa_extractor_YYYY-MM-DD.log`
- **Rotation**: Daily rotation, keep 30 days
- **Size Limit**: 10MB per file

### 4. Log Format
```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [MODULE] - Message
```

**Example:**
```
[2025-01-07 14:30:45] [INFO] [extractors.pdf_extractor] - Starting extraction for: contract.pdf
[2025-01-07 14:30:46] [DEBUG] [extractors.pdf_extractor] - Detected PDF type: text
[2025-01-07 14:30:47] [INFO] [extractors.pdf_extractor] - Extraction complete: 5 pages, 5000 chars
```

---

## Error Handling Strategy

### Error Categories

1. **Unrecoverable Errors** → Raise Exceptions
   - File not found
   - Invalid file format
   - Configuration errors
   - API authentication failures

2. **Recoverable Errors** → Return Result Pattern
   - OCR failures (can retry)
   - LLM parsing errors (can normalize)
   - Partial extraction failures

3. **Warnings** → Log and Continue
   - Schema validation warnings
   - Missing optional fields
   - Performance issues

### Custom Exception Classes

```python
# Base exception
class MSAExtractorError(Exception):
    """Base exception for MSA Extractor"""

# Specific exceptions
class ConfigurationError(MSAExtractorError):
    """Configuration-related errors"""

class FileError(MSAExtractorError):
    """File-related errors (not found, invalid, etc.)"""

class ExtractionError(MSAExtractorError):
    """Text extraction errors"""

class OCRError(MSAExtractorError):
    """OCR-related errors"""

class LLMError(MSAExtractorError):
    """LLM API errors"""

class ValidationError(MSAExtractorError):
    """Schema validation errors"""
```

### Error Handling Pattern

**For Unrecoverable Errors:**
```python
def extract(self, file_path: str) -> ExtractedTextResult:
    try:
        # ... extraction logic
    except FileNotFoundError as e:
        raise FileError(f"File not found: {file_path}") from e
    except Exception as e:
        self.logger.error(f"Extraction failed: {e}", exc_info=True)
        raise ExtractionError(f"Failed to extract from {file_path}") from e
```

**For Recoverable Errors:**
```python
def extract_with_fallback(self, file_path: str) -> ExtractedTextResult:
    try:
        return self._extract_primary(file_path)
    except OCRError as e:
        self.logger.warning(f"Primary extraction failed, trying fallback: {e}")
        return self._extract_fallback(file_path)
```

---

## Implementation Plan

### Phase 1: Logging Infrastructure
1. Create `utils/logger.py` with centralized configuration
2. Create `utils/exceptions.py` with custom exceptions
3. Update `config.py` with logging settings
4. Replace all `logging.getLogger()` calls with centralized logger

### Phase 2: Error Handling Standardization
1. Define error handling strategy
2. Create custom exception classes
3. Update error handling in key modules
4. Add error recovery where appropriate

### Phase 3: Integration
1. Update all modules to use new logging
2. Update all modules to use custom exceptions
3. Add error handling tests
4. Document error handling patterns

---

## Configuration Options

### Environment Variables
```bash
LOG_LEVEL=INFO                    # Overall log level
LOG_FILE_ENABLED=true             # Enable file logging
LOG_FILE_PATH=./logs              # Log file directory
LOG_FILE_FORMAT=text              # text or json
LOG_FILE_ROTATION_DAYS=30        # Keep logs for 30 days
LOG_FILE_MAX_SIZE_MB=10           # Max file size
LOG_CONSOLE_ENABLED=true          # Enable console logging
LOG_CONSOLE_FORMAT=text           # text or json
```

### Config.py Settings
```python
# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_ENABLED = os.getenv("LOG_FILE_ENABLED", "true").lower() == "true"
LOG_FILE_PATH = Path(os.getenv("LOG_FILE_PATH", BASE_DIR / "logs"))
LOG_FILE_FORMAT = os.getenv("LOG_FILE_FORMAT", "text")  # text or json
LOG_FILE_ROTATION_DAYS = int(os.getenv("LOG_FILE_ROTATION_DAYS", "30"))
LOG_FILE_MAX_SIZE_MB = int(os.getenv("LOG_FILE_MAX_SIZE_MB", "10"))
LOG_CONSOLE_ENABLED = os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true"
LOG_CONSOLE_FORMAT = os.getenv("LOG_CONSOLE_FORMAT", "text")  # text or json

# Module-specific log levels
LOG_LEVELS = {
    "msa_extractor": LOG_LEVEL,
    "msa_extractor.extractors": "DEBUG",
    "msa_extractor.ai": "INFO",
    "msa_extractor.extractors.ocr_handler": "WARNING"
}
```

---

## Refactoring Considerations

### Easy to Change Later
1. **Format Switching**: Change `LOG_FILE_FORMAT` to switch between text/JSON
2. **Output Switching**: Toggle `LOG_FILE_ENABLED` / `LOG_CONSOLE_ENABLED`
3. **Level Control**: Adjust `LOG_LEVELS` dictionary
4. **Handler Changes**: Modify `utils/logger.py` only

### Dependency Injection
- Logger passed to classes (optional, falls back to module logger)
- Allows testing with mock loggers
- Allows different loggers for different contexts

### Backward Compatibility
- Keep `logging.getLogger(__name__)` working
- Centralized logger wraps standard logging
- No breaking changes to existing code

---

## Example Usage

### Before (Current)
```python
import logging
logger = logging.getLogger(__name__)

def extract(self, file_path: str):
    logger.info(f"Extracting from {file_path}")
    try:
        # ... logic
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
```

### After (New)
```python
from utils.logger import get_logger
from utils.exceptions import ExtractionError, FileError

logger = get_logger(__name__)

def extract(self, file_path: str) -> ExtractedTextResult:
    logger.info("Starting extraction", extra={"file_path": file_path})
    try:
        # ... logic
    except FileNotFoundError as e:
        raise FileError(f"File not found: {file_path}") from e
    except Exception as e:
        logger.error("Extraction failed", exc_info=True, extra={"file_path": file_path})
        raise ExtractionError(f"Failed to extract from {file_path}") from e
```

---

## Benefits

1. **Centralized**: Single place to configure logging
2. **Flexible**: Easy to change formats, levels, outputs
3. **Structured**: JSON format for log aggregation
4. **Maintainable**: Clear error types and patterns
5. **Testable**: Can inject mock loggers
6. **Production-Ready**: File rotation, size limits, retention

---

## Next Steps

1. Create `utils/logger.py` with centralized configuration
2. Create `utils/exceptions.py` with custom exceptions
3. Update `config.py` with logging settings
4. Update key modules to use new logging
5. Standardize error handling patterns
6. Add tests for logging and error handling

