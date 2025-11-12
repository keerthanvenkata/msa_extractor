# Issues, TODOs, and Optimizations

This document tracks all identified issues, bugs, TODOs, and optimization opportunities in the MSA Metadata Extractor codebase.

**Last Updated:** November 12, 2025  
**Status:** Active tracking

---

## 🔴 Critical Bugs

### BUG-001: Strategy Check Logic Error
**Location:** `extractors/extraction_coordinator.py:64`

**Problem:**
The code checks the global `EXTRACTION_STRATEGY` config instead of the actual strategy used for extraction. This causes incorrect behavior when a strategy is passed as a parameter that differs from the config.

**Current Code:**
```python
if extraction_result.metadata.get("is_scanned") and EXTRACTION_STRATEGY == "gemini_vision":
```

**Should Be:**
```python
if extraction_result.metadata.get("is_scanned") and extraction_result.metadata.get("extraction_strategy") == "gemini_vision":
```

**Impact:** High - May skip LLM processing incorrectly or process unnecessarily, leading to incorrect results or wasted API calls.

**Priority:** P0 - Must fix before production

**Status:** 🟢 Fixed (2025-01-07)

---

### BUG-002: PDF Type Detection Duplication
**Location:** 
- `extractors/strategy_factory.py:84` (`_get_auto_strategy_extractor`)
- `extractors/pdf_extractor.py:72` (`extract`)

**Problem:**
`_detect_pdf_type()` is called twice for the same file:
1. Once in `StrategyFactory._get_auto_strategy_extractor()` to determine which extractor to use
2. Again in `PDFExtractor.extract()` to determine extraction method

This opens the PDF twice and reads pages twice, which is inefficient.

**Impact:** Medium - Performance degradation, especially for large PDFs

**Priority:** P1 - Should fix soon

**Proposed Fix:**
- Option 1: Pass `pdf_type` as parameter from factory to extractor
- Option 2: Cache result in a file-level cache (e.g., using `functools.lru_cache`)
- Option 3: Store `pdf_type` in a temporary attribute after first detection

**Status:** 🟢 Fixed (2025-01-07)

---

### BUG-003: Gemini Vision - Metadata Only from First Page
**Location:** `extractors/gemini_vision_extractor.py:84-92`

**Problem:**
When using Gemini Vision strategy, metadata is only extracted from the first page. For multi-page contracts, metadata might be on later pages (e.g., signature pages, appendices).

**Current Behavior:**
- Page 0: Extracts metadata
- Pages 1+: Only extracts text

**Impact:** Medium - May miss metadata on later pages

**Priority:** P1 - Should fix soon

**Proposed Fix:**
- Option 1: Extract metadata from all pages and merge intelligently
- Option 2: Extract metadata from first 3 pages (cover + first 2 content pages)
- Option 3: Document limitation and add config option for page selection

**Status:** 🟢 Fixed (2025-01-07)

---

### BUG-004: Resource Management - Document Accessed After Close
**Location:** `extractors/pdf_extractor.py:306-443` (`_extract_mixed`)

**Problem:**
In `_extract_mixed` method:
1. Document closed on line 388
2. Document accessed again on line 411 (`doc.metadata`) after being closed
3. Document closed again on line 413 (double close)
4. Exception handler also closes document (could be triple close)

**Impact:** Critical - Resource leak, potential crashes, undefined behavior

**Priority:** P0 - Must fix before production

**Status:** 🟢 Fixed (2025-01-07) - Removed duplicate metadata extraction and close, moved to finally block

---

### BUG-005: Resource Management - Document Not Closed on Exception
**Location:** 
- `extractors/pdf_extractor.py:104-160` (`_detect_pdf_type`)
- `extractors/gemini_vision_extractor.py:61-158` (`extract`)

**Problem:**
- `_detect_pdf_type`: Document not closed in exception handler
- `gemini_vision_extractor.extract`: Document closed in try block, not in finally

**Impact:** Medium - Resource leak if exception occurs

**Priority:** P1 - Should fix soon

**Status:** 🟢 Fixed (2025-01-07) - Added finally blocks to ensure document is always closed

---

### BUG-006: Schema Validation After Normalization is Ineffective
**Location:** 
- `ai/gemini_client.py:77-86` (`extract_metadata_from_text`)
- `ai/gemini_client.py:127-133` (`extract_metadata_from_image`)

**Problem:**
The `normalize()` method fills all missing fields with "Not Found", so `validate()` called after normalization will always pass. This prevents detection of incomplete or malformed responses from the LLM. Validation should occur before normalization to detect what the LLM actually returned versus what fields are being filled in as defaults.

**Current Code:**
```python
metadata = self.schema_validator.normalize(metadata)  # Fills all missing fields
is_valid, error = self.schema_validator.validate(metadata)  # Always passes!
```

**Should Be:**
```python
is_valid, error = self.schema_validator.validate(metadata)  # Check raw LLM response
if not is_valid:
    self.logger.warning("LLM returned incomplete data")
metadata = self.schema_validator.normalize(metadata)  # Then fill missing fields
```

**Impact:** High - Cannot detect incomplete LLM responses, leading to silent failures

**Priority:** P0 - Must fix before production

**Status:** 🟢 Fixed (2025-01-07) - Validation now occurs before normalization in both methods

---

## 🟡 Performance Issues

### PERF-001: Multiple GeminiClient Instances
**Location:**
- `extractors/extraction_coordinator.py:33` (creates GeminiClient)
- `extractors/gemini_vision_extractor.py:36` (creates GeminiClient if None)
- `extractors/pdf_extractor.py:43` (stores reference)
- `extractors/docx_extractor.py:31` (stores reference)

**Problem:**
Multiple `GeminiClient` instances can be created, each with its own `SchemaValidator` instance. This is memory inefficient.

**Impact:** Low - Memory usage, but not critical for typical use cases

**Priority:** P2 - Nice to have

**Proposed Fix:**
- Use singleton pattern for GeminiClient
- Or use dependency injection to pass single instance through

**Status:** 🟡 Open

---

### PERF-002: Multiple SchemaValidator Instances
**Location:**
- `ai/gemini_client.py:43` (creates SchemaValidator)
- `main.py:51` (creates SchemaValidator)
- `ai/schema.py:124` (convenience function creates new instance)

**Problem:**
Multiple `SchemaValidator` instances are created, each building the JSON Schema from scratch.

**Impact:** Low - Memory and CPU usage, but not critical

**Priority:** P2 - Nice to have

**Proposed Fix:**
- Make SchemaValidator a singleton
- Or reuse validator instance from GeminiClient

**Status:** 🟡 Open

---

### PERF-003: Images Stored in Memory After OCR
**Location:** `extractors/extraction_coordinator.py:115`

**Problem:**
Preprocessed images are stored in `result.metadata["preprocessed_images"]` and kept in memory even after OCR is complete. For large PDFs (100+ pages), this can consume significant memory (~100MB+).

**Impact:** Medium - Memory usage for large PDFs

**Priority:** P1 - Should fix for large document support

**Proposed Fix:**
- Clear `preprocessed_images` from metadata after OCR completes
- Or store images to temporary files instead of memory

**Status:** 🟢 Fixed (2025-01-07)

---

### PERF-004: Full Text Stored in Memory
**Location:** `extractors/pdf_extractor.py:202`

**Problem:**
Full text is stored in memory as a string. For very large PDFs (100+ pages), this could be large (~100KB+).

**Impact:** Low - For typical contracts, but could be issue for very large files

**Priority:** P3 - Future enhancement

**Proposed Fix:**
- Consider streaming for very large files
- Or implement chunking for LLM processing

**Status:** 🟡 Open

---

## 🟠 Data Quality Issues

### DATA-001: Text Truncation Without Warning
**Location:** `ai/gemini_client.py:57-62`

**Problem:**
Text is truncated if it exceeds `MAX_TEXT_LENGTH` (12000 characters), but there's no clear warning about what was truncated. This might lose important information.

**Impact:** Medium - Data loss for long contracts

**Priority:** P1 - Should fix for data integrity

**Proposed Fix:**
- Implement chunking + aggregation (as noted in PROMPT.md Phase 2)
- Or at minimum, log warning with truncation details
- Or raise exception if text exceeds limit

**Status:** 🟢 Fixed (2025-01-07) - Added detailed warning with truncation length and impact

---

### DATA-002: Schema Validation After Normalization
**Location:** `ai/gemini_client.py:78-80`

**Problem:**
Schema validation happens after normalization. Since normalization fills missing fields with "Not Found", validation will always pass (all fields present).

**Impact:** Low - Validation is redundant but doesn't cause errors

**Priority:** P2 - Nice to have

**Proposed Fix:**
- Validate before normalization to catch actual missing fields
- Or remove redundant validation (normalization already ensures structure)

**Status:** 🟢 Fixed (2025-01-07)

---

## 🔵 Code Quality Issues

### CODE-001: Inconsistent Error Handling
**Location:** Multiple files

**Problem:**
Error handling is inconsistent across the codebase:
- Some methods return empty schema on error
- Some methods raise exceptions
- Some methods return empty string
- No standard error handling strategy

**Impact:** Medium - Makes error handling difficult for callers

**Priority:** P1 - Should standardize

**Proposed Fix:**
- Define error handling strategy:
  - Use exceptions for unrecoverable errors
  - Use return values (Result pattern) for recoverable errors
  - Document error handling strategy in coding guidelines

**Status:** 🟢 Fixed (2025-01-07) - Custom exception classes created, error handling strategy defined. Gradual migration in progress.

---

### CODE-002: OCR Handler - Unused Preprocess Parameter
**Location:** `extractors/ocr_handler.py:22`

**Problem:**
`preprocess` parameter exists in `OCRHandler.__init__()` but is not used. Images are already preprocessed in `PDFExtractor` before being passed to OCR handler.

**Impact:** Low - Confusing but doesn't cause errors

**Priority:** P3 - Cleanup

**Proposed Fix:**
- Remove `preprocess` parameter
- Or document that preprocessing happens earlier in pipeline

**Status:** 🔵 Open

---

## 📋 TODOs

### TODO-001: Implement Chunking for Long Documents
**Location:** `ai/gemini_client.py`

**Description:**
For documents exceeding `MAX_TEXT_LENGTH`, implement chunking strategy:
1. Split text into chunks
2. Process each chunk with LLM
3. Aggregate results intelligently

**Priority:** P1 - Required for long document support

**Status:** 🔵 Deferred to Next Iteration

**Reference:** PROMPT.md Phase 2

**Note:** Deferred to next iteration. Current 50K character limit handles most sample documents. Will implement hybrid approach (full document first, chunking fallback) when needed.

---

### TODO-002: Add Unit Tests
**Location:** `tests/`

**Description:**
Create comprehensive unit tests for:
- Text extraction (PDF, DOCX)
- OCR handlers (Tesseract, GCV, Gemini Vision)
- Schema validation
- LLM integration (mocked)
- Error handling

**Priority:** P1 - Required for production

**Status:** 📋 TODO

---

### TODO-003: Add Integration Tests
**Location:** `tests/`

**Description:**
Create integration tests for:
- Full extraction pipeline
- Different document types
- Different strategies
- Error scenarios

**Priority:** P1 - Required for production

**Status:** 📋 TODO

---

### TODO-004: Add Logging Configuration
**Location:** `config.py`

**Description:**
Add structured logging configuration:
- Log levels per module
- File logging option
- Log rotation
- Structured log format (JSON)

**Priority:** P2 - Nice to have

**Status:** 🟢 Fixed (2025-01-07) - Centralized logging with file rotation, JSON format, and module-level control implemented.

---

### TODO-005: Add Progress Tracking for Batch Processing
**Location:** `main.py`

**Description:**
Add progress tracking for batch processing:
- Progress bar
- Estimated time remaining
- Success/failure counts
- Resume capability

**Priority:** P2 - Nice to have

**Status:** 📋 TODO

---

### TODO-006: Add Retry Logic for API Calls
**Location:** `ai/gemini_client.py`

**Description:**
Add retry logic for Gemini API calls:
- Exponential backoff
- Max retry attempts
- Error handling for rate limits
- Timeout configuration

**Priority:** P1 - Required for production reliability

**Status:** 📋 TODO

---

### TODO-007: Add Configuration Validation
**Location:** `config.py`

**Description:**
Add comprehensive configuration validation:
- Validate API keys format
- Validate file paths exist
- Validate model names
- Validate strategy combinations

**Priority:** P2 - Nice to have

**Status:** 📋 TODO

---

### TODO-008: Add Performance Metrics
**Location:** Multiple files

**Description:**
Add performance metrics collection:
- Extraction time per document
- OCR time per page
- LLM processing time
- Memory usage tracking

**Priority:** P3 - Future enhancement

**Status:** 📋 TODO

---

### TODO-009: Implement Data Masking/Encryption
**Location:** `ai/gemini_client.py`, `extractors/`, `utils/data_masking.py` (new)

**Description:**
Implement data masking/encryption before sending documents to external APIs (Gemini). This is critical for security and privacy compliance.

**Requirements:**
1. **Masking Strategy:**
   - Identify sensitive data (PII, financial info, company names, etc.)
   - Replace with placeholders or encrypted values
   - Maintain structure for LLM extraction
   - Re-map extracted values back to original data

2. **What to Mask:**
   - Personal Identifiable Information (PII): Names, emails, phone numbers, addresses
   - Financial Information: Account numbers, amounts, payment details
   - Company Names: Client/vendor names (if required)
   - Dates: Execution dates, effective dates (if required)
   - Signatory Information: Names and titles (if required)

3. **Implementation Approach:**
   - Create `utils/data_masking.py` module
   - Mask text before sending to LLM
   - Store mapping dictionary (original → masked)
   - Re-map extracted metadata back to original values
   - Support configurable masking rules

4. **Configuration:**
   - `ENABLE_DATA_MASKING=true/false` - Enable/disable masking
   - `MASK_PII=true/false` - Mask PII
   - `MASK_FINANCIAL=true/false` - Mask financial data
   - `MASK_COMPANY_NAMES=true/false` - Mask company names
   - `MASK_DATES=true/false` - Mask dates
   - `MASK_SIGNATORIES=true/false` - Mask signatory information

5. **Masking Methods:**
   - **Placeholder replacement:** "John Doe" → "[SIGNATORY_1]"
   - **Pattern-based:** Email addresses → "[EMAIL_1]", Phone → "[PHONE_1]"
   - **Encryption:** Encrypt sensitive values (requires decryption key)
   - **Redaction:** Remove sensitive sections entirely

6. **Re-mapping:**
   - Store mapping: `{"[SIGNATORY_1]": "John Doe", "[EMAIL_1]": "john@example.com"}`
   - After extraction, replace masked values with originals
   - Handle cases where LLM returns masked values

**Priority:** P0 - Critical for security and compliance

**Status:** 📋 TODO

**Reference:** Security requirements, privacy compliance. See [DATA_MASKING_PLAN.md](planning/DATA_MASKING_PLAN.md) for detailed implementation plan.

**Note:** This is essential before processing sensitive documents. Consider implementing before production deployment.

---

### TODO-010: Document Pure Images (No Text)
**Location:** `extractors/pdf_extractor.py`

**Description:**
For pure image pages with no extractable text, document the image presence with metadata:
- Image dimensions (width x height)
- Image format
- Image size
- Page number

**Priority:** P3 - Future enhancement

**Status:** 📋 TODO

**Note:** Currently, pure images are documented as "[Page X - Image Page (No extractable text found)]". Future enhancement will add image dimensions and metadata.

---

### TODO-011: Implement Persistence & Storage System
**Location:** `storage/database.py`, `storage/cleanup.py`, `main.py`

**Status:** ✅ **Phase 1 & 2 Complete** (Database module and CLI integration done)

**Description:**
SQLite-based persistence system for tracking extraction jobs with UUIDs, file management, and cleanup policies. Required for FastAPI backend integration.

**Completed:**
1. ✅ **Database Schema:**
   - `extractions` table with UUID primary key
   - Track job status, file paths, timestamps, extraction config
   - Indexes on status, created_at, file_name
   - Monthly log tables (`extraction_logs_YYYY_MM`)

2. ✅ **File Storage:**
   - Store uploaded files in `uploads/{uuid}.{ext}` (preserves extension)
   - **Default:** Store JSON results in `extractions.result_json` column (database)
   - **Default:** Store logs in `extraction_logs` table (database, monthly tables)
   - **Legacy mode:** CLI `--legacy` flag allows file-based storage (`results/` directory)
   - **API:** Will always use database (no legacy mode)
   - PDF cleanup pending (Phase 3)

3. ✅ **CLI Integration:**
   - Database tracking in `extract_single_file()` and `extract_batch()`
   - Job management commands (`list-jobs`, `get-job`)
   - Legacy mode support (`--legacy` flag)
   - Re-run failed jobs (`--job-id` flag)

**Remaining:**
4. **Cleanup Strategy:** (Phase 3 - Pending)
   - Time-based: Delete PDFs older than N days (default: 7 days)
   - Count-based: Delete oldest PDFs when count exceeds threshold (default: 1000)
   - Always retain JSONs and logs
   - Never delete pending/processing jobs

5. **FastAPI Integration Points:** (Phase 4 - Pending)
   - POST `/api/v1/extract/upload` → Upload PDF, return job ID
   - GET `/api/v1/extract/{job_id}` → Get extraction result by job ID

6. **Implementation Phases:**
   - ✅ Phase 1: Database & Storage Module (`storage/database.py`) - **Complete**
   - ✅ Phase 2: Integration with CLI (`main.py`) - **Complete**
   - 📋 Phase 3: Cleanup Implementation (`storage/cleanup.py`) - **Pending**
   - 📋 Phase 4: FastAPI Backend - **Pending**

**Priority:** P1 - Required for FastAPI backend

**Status:** ✅ **Phase 1 & 2 Complete**, 📋 Phase 3 & 4 Pending

**Reference:** 
- See [PERSISTENCE_PLAN.md](planning/PERSISTENCE_PLAN.md) for detailed implementation plan
- See [IMPLEMENTATION_ROADMAP.md](planning/IMPLEMENTATION_ROADMAP.md) for phase breakdown
- See [Storage Database Module](modules/storage_database.md) for API reference

**Iteration 1 Scope:**
- ✅ SQLite database (local) - **Implemented**
- ✅ Local filesystem for PDFs (Cloud Run ephemeral storage) - **Implemented**
- ✅ **Default:** JSON results and logs stored in database - **Implemented**
- ✅ **Legacy mode:** CLI `--legacy` flag for file-based storage - **Implemented**
- 📋 **API:** Always uses database (no legacy mode) - **Phase 4 pending**

---

### TODO-012: GCS Integration for PDF Storage (Future Iteration)
**Location:** `storage/gcs_adapter.py`, `config.py`

**Description:**
Migrate PDF storage from local filesystem to Google Cloud Storage (GCS) for production deployment.

**Requirements:**
1. **GCS Storage Adapter:**
   - Create `storage/gcs_adapter.py` with GCS upload/download methods
   - Support for GCS bucket configuration
   - Handle GCS authentication (service account, default credentials)
   - Store GCS paths in `extractions.pdf_storage_path` (format: `gs://bucket/path/{uuid}.pdf`)
   - Update `pdf_storage_type` to `gcs` when using GCS

2. **Configuration:**
   - `GCP_PROJECT_ID`: GCP project ID
   - `GCP_STORAGE_BUCKET`: GCS bucket name for PDF storage
   - `USE_GCS`: Enable GCS storage (default: False)
   - `GCP_SERVICE_ACCOUNT_KEY`: Path to service account JSON (optional, uses default credentials if not set)

3. **Migration:**
   - Support both local and GCS storage (configurable)
   - Migration script to move existing PDFs to GCS
   - Update cleanup logic to handle GCS deletion

**Priority:** P2 - Future enhancement (after Iteration 1)

**Status:** 📋 TODO (Future Iteration)

**Reference:** See [IMPLEMENTATION_ROADMAP.md](planning/IMPLEMENTATION_ROADMAP.md) for architecture details.

---

### TODO-013: Cloud SQL Migration (Future Iteration)
**Location:** `storage/database.py`, `config.py`

**Description:**
Migrate from SQLite to Cloud SQL PostgreSQL for production deployment with better scalability and reliability.

**Requirements:**
1. **Cloud SQL Support:**
   - Add PostgreSQL connection support to `ExtractionDB` class
   - Support both SQLite (local) and PostgreSQL (Cloud SQL)
   - Connection pooling for Cloud SQL
   - Handle Cloud SQL authentication (Cloud SQL Proxy, private IP)

2. **Database Schema:**
   - Migrate SQLite schema to PostgreSQL
   - Use PostgreSQL-specific features (JSONB for `result_json`, table partitioning for logs)
   - Create migration scripts for schema changes

3. **Log Table Strategy:**
   - Use PostgreSQL table partitioning for `extraction_logs` (partition by month)
   - Or continue with monthly tables if preferred
   - Automatic partition management

4. **Configuration:**
   - `GCP_CLOUD_SQL_INSTANCE`: Cloud SQL instance connection name
   - `USE_CLOUD_SQL`: Enable Cloud SQL (default: False)
   - `CLOUD_SQL_DATABASE`: Database name
   - `CLOUD_SQL_USER`: Database user
   - `CLOUD_SQL_PASSWORD`: Database password (or use Secret Manager)
   - `CLOUD_SQL_CONNECTION_NAME`: Instance connection name

5. **Migration Path:**
   - Export data from SQLite
   - Import to Cloud SQL PostgreSQL
   - Test migration process
   - Document migration steps

**Priority:** P2 - Future enhancement (after Iteration 1)

**Status:** 📋 TODO (Future Iteration)

**Reference:** See [IMPLEMENTATION_ROADMAP.md](planning/IMPLEMENTATION_ROADMAP.md) for architecture details.

---

## 🚀 Optimizations

### OPT-001: Cache PDF Type Detection
**Location:** `extractors/pdf_extractor.py`

**Description:**
Cache PDF type detection results to avoid re-detection for same file.

**Priority:** P2 - Performance improvement

**Status:** 🚀 Proposed

---

### OPT-002: Lazy Load OCR Handlers
**Location:** `extractors/ocr_handler.py`

**Description:**
Only initialize OCR handlers when actually needed, not at import time.

**Priority:** P2 - Performance improvement

**Status:** 🚀 Proposed

---

### OPT-003: Parallel OCR Processing
**Location:** `extractors/ocr_handler.py`

**Description:**
Process multiple pages in parallel for OCR operations.

**Priority:** P2 - Performance improvement

**Status:** 🚀 Proposed

---

### OPT-004: Streaming for Large Files
**Location:** `extractors/pdf_extractor.py`

**Description:**
Implement streaming for very large PDFs to reduce memory usage.

**Priority:** P3 - Future enhancement

**Status:** 🚀 Proposed

---

## 📊 Issue Summary

| Category | Count | P0 | P1 | P2 | P3 |
|----------|-------|----|----|----|----|
| Critical Bugs | 3 | 1 | 2 | 0 | 0 |
| Performance | 4 | 0 | 1 | 2 | 1 |
| Data Quality | 2 | 0 | 1 | 1 | 0 |
| Code Quality | 2 | 0 | 1 | 0 | 1 |
| TODOs | 13 | 1 | 5 | 6 | 1 |
| Optimizations | 4 | 0 | 0 | 3 | 1 |
| **Total** | **28** | **2** | **11** | **12** | **3** |

---

## Priority Legend

- **P0 (Critical):** Must fix before production
- **P1 (High):** Should fix soon
- **P2 (Medium):** Nice to have
- **P3 (Low):** Future enhancement

---

## Status Legend

- 🔴 **Open:** Not yet addressed
- 🟡 **In Progress:** Currently being worked on
- 🟢 **Fixed:** Resolved and verified
- 📋 **TODO:** Planned for future work
- 🚀 **Proposed:** Optimization opportunity identified

---

## Notes

- This document should be updated as issues are fixed or new issues are discovered
- Priority levels may change based on user feedback and production requirements
- Some optimizations may be deferred to future phases based on actual usage patterns

