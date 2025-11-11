# Persistence & Storage Plan

**Created:** 2025-01-07  
**Status:** Planning Phase  
**Priority:** P1 - Required for FastAPI Backend

---

## Overview

This document outlines the persistence and storage strategy for the MSA Metadata Extractor, including database schema, file storage, cleanup policies, and integration with the planned FastAPI backend.

---

## Goals

1. **Track Extractions:** Store metadata about each extraction job with UUID identifiers
2. **File Management:** Store uploaded PDFs temporarily, retain JSON results and logs
3. **Cleanup Strategy:** Automatically clean up old PDFs while preserving results
4. **API Ready:** Design for FastAPI backend integration (upload endpoint → job ID, get endpoint → JSON)
5. **Log Management:** Decide on log storage strategy (SQLite vs files)

---

## Database Schema (SQLite)

### Table: `extractions`

Primary table to track all extraction jobs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT (UUID) | PRIMARY KEY | Unique job identifier (UUID v4) |
| `file_name` | TEXT | NOT NULL | Original filename |
| `file_path` | TEXT | NOT NULL | Path to stored PDF file |
| `file_size` | INTEGER | | File size in bytes |
| `status` | TEXT | NOT NULL | `pending`, `processing`, `completed`, `failed` |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Job creation time |
| `started_at` | TIMESTAMP | | When processing started |
| `completed_at` | TIMESTAMP | | When processing finished |
| `error_message` | TEXT | | Error details if failed |
| `result_json_path` | TEXT | | Path to extracted JSON file |
| `log_path` | TEXT | | Path to log file |
| `extraction_method` | TEXT | | EXTRACTION_METHOD used |
| `llm_processing_mode` | TEXT | | LLM_PROCESSING_MODE used |
| `ocr_engine` | TEXT | | OCR_ENGINE used (if applicable) |
| `metadata` | TEXT (JSON) | | Additional metadata (JSON string) |

**Indexes:**
- `idx_extractions_status` on `status`
- `idx_extractions_created_at` on `created_at`
- `idx_extractions_file_name` on `file_name`

**Status Values:**
- `pending`: Job created, not yet started
- `processing`: Currently being processed
- `completed`: Successfully completed
- `failed`: Processing failed

### Optional Table: `extraction_logs` (Alternative to file-based logs)

If we decide to store logs in SQLite instead of files:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Log entry ID |
| `extraction_id` | TEXT (UUID) | FOREIGN KEY | References `extractions.id` |
| `timestamp` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Log entry time |
| `level` | TEXT | NOT NULL | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `message` | TEXT | NOT NULL | Log message |
| `module` | TEXT | | Module/logger name |
| `details` | TEXT (JSON) | | Additional structured data (JSON string) |

**Indexes:**
- `idx_extraction_logs_extraction_id` on `extraction_id`
- `idx_extraction_logs_timestamp` on `timestamp`
- `idx_extraction_logs_level` on `level`

**Note:** This table can grow large. Consider:
- Archiving old logs to files
- Periodic cleanup of logs older than N days
- Only storing ERROR/CRITICAL logs in DB, others in files

---

## File Storage Structure

```
storage/
├── uploads/          # Temporary PDF storage
│   ├── {uuid}.pdf    # Uploaded PDFs (temporary)
│   └── ...
├── results/          # Extracted JSON results (permanent)
│   ├── {uuid}.json   # Extracted metadata
│   └── ...
└── logs/             # Log files (permanent)
    ├── {uuid}.log    # Per-job log files
    └── ...
```

**Alternative Structure (if using existing directories):**
```
results/
├── {uuid}.json       # Extracted metadata
└── ...

logs/
├── {uuid}.log        # Per-job log files
└── ...

uploads/              # New directory for temporary PDFs
├── {uuid}.pdf
└── ...
```

---

## Log Storage Strategy

### Recommendation: **Hybrid Approach**

**Store logs as files, metadata in database:**

1. **Log Files:** Store full log content in `logs/{uuid}.log` files
   - Easy to view, grep, tail
   - No database bloat
   - Can be archived/compressed
   - Standard logging practice

2. **Log Metadata in DB:** Store summary in `extractions.log_path`
   - Quick lookup of log location
   - Can query by job ID
   - No need to parse files for basic info

3. **Error Summary in DB:** Store error details in `extractions.error_message`
   - Quick error lookup without reading files
   - Can query failed jobs easily

**Alternative: SQLite for Logs**
- **Pros:** Queryable, searchable, structured
- **Cons:** Database bloat, slower writes, harder to view/tail
- **Use Case:** Only if you need to query logs frequently

**Decision: Use file-based logs with metadata in DB** ✅

---

## Cleanup Strategy

### PDF Cleanup Rules

1. **Time-based Cleanup:**
   - Delete PDFs older than N days (configurable, default: 7 days)
   - Only delete if status is `completed` or `failed`
   - Never delete if status is `pending` or `processing`

2. **Count-based Cleanup:**
   - When total PDF count exceeds threshold (configurable, default: 1000)
   - Delete oldest PDFs first (by `created_at`)
   - Keep at least the most recent N files (configurable, default: 100)

3. **What to Keep:**
   - ✅ JSON result files (permanent)
   - ✅ Log files (permanent)
   - ✅ Database records (permanent)
   - ❌ PDF files (temporary, deleted after cleanup)

### Cleanup Implementation

**Option 1: Background Task (Recommended for FastAPI)**
- Run cleanup as a background task (e.g., Celery, APScheduler, or FastAPI background task)
- Schedule: Daily at 2 AM (configurable)
- Check both time-based and count-based rules

**Option 2: CLI Command**
- Add `python main.py cleanup` command
- Can be run manually or via cron/scheduled task
- Useful for CLI-only usage

**Option 3: On-Demand Cleanup**
- Trigger cleanup when count threshold is reached
- Run cleanup after each extraction completes
- Simple but may impact performance

**Recommendation: Option 1 (Background Task) for FastAPI, Option 2 (CLI) for standalone**

---

## Configuration Variables

Add to `config.py`:

```python
# Storage paths
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", BASE_DIR / "storage"))
UPLOADS_DIR = STORAGE_DIR / "uploads"
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", BASE_DIR / "results"))
LOGS_DIR = Path(os.getenv("LOG_FILE_PATH", BASE_DIR / "logs"))

# Cleanup configuration
CLEANUP_ENABLED = os.getenv("CLEANUP_ENABLED", "true").lower() == "true"
CLEANUP_PDF_DAYS = int(os.getenv("CLEANUP_PDF_DAYS", "7"))  # Delete PDFs after 7 days
CLEANUP_PDF_MAX_COUNT = int(os.getenv("CLEANUP_PDF_MAX_COUNT", "1000"))  # Max PDFs to keep
CLEANUP_PDF_MIN_COUNT = int(os.getenv("CLEANUP_PDF_MIN_COUNT", "100"))  # Always keep at least 100
CLEANUP_SCHEDULE_HOUR = int(os.getenv("CLEANUP_SCHEDULE_HOUR", "2"))  # Run at 2 AM
```

---

## Database Module Design

### Module: `storage/database.py`

**Class: `ExtractionDB`**

```python
class ExtractionDB:
    """SQLite database manager for extraction jobs."""
    
    def __init__(self, db_path: Path):
        """Initialize database connection."""
    
    def create_job(self, file_name: str, file_path: Path, file_size: int) -> str:
        """Create new extraction job, return UUID."""
    
    def get_job(self, job_id: str) -> dict:
        """Get job by UUID."""
    
    def update_job_status(self, job_id: str, status: str, 
                         error_message: str = None) -> None:
        """Update job status."""
    
    def complete_job(self, job_id: str, result_json_path: Path, 
                    log_path: Path) -> None:
        """Mark job as completed with result paths."""
    
    def get_jobs_by_status(self, status: str, limit: int = None) -> List[dict]:
        """Get jobs by status."""
    
    def get_old_jobs(self, days: int) -> List[dict]:
        """Get completed/failed jobs older than N days."""
    
    def get_jobs_for_cleanup(self, max_count: int, min_count: int) -> List[dict]:
        """Get jobs eligible for cleanup (count-based)."""
    
    def delete_job(self, job_id: str) -> None:
        """Delete job record (and associated files)."""
    
    def cleanup_old_pdfs(self, days: int) -> int:
        """Delete PDFs older than N days, return count deleted."""
    
    def cleanup_excess_pdfs(self, max_count: int, min_count: int) -> int:
        """Delete oldest PDFs when count exceeds threshold."""
```

---

## FastAPI Integration Points

### Endpoint 1: Upload PDF → Job ID

**POST `/api/v1/extract/upload`**

**Request:**
- `multipart/form-data` with PDF file
- Optional: `extraction_method`, `llm_processing_mode`, `ocr_engine`

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2025-01-07T10:30:00Z",
  "file_name": "contract.pdf"
}
```

**Flow:**
1. Receive uploaded file
2. Generate UUID
3. Save PDF to `uploads/{uuid}.pdf`
4. Create database record with status `pending`
5. Return job ID
6. (Async) Start extraction in background

### Endpoint 2: Get Result by Job ID

**GET `/api/v1/extract/{job_id}`**

**Response (Completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-01-07T10:30:00Z",
  "completed_at": "2025-01-07T10:32:15Z",
  "result": {
    // Full extracted metadata JSON
  }
}
```

**Response (Processing):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "created_at": "2025-01-07T10:30:00Z",
  "started_at": "2025-01-07T10:30:05Z"
}
```

**Response (Failed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "created_at": "2025-01-07T10:30:00Z",
  "failed_at": "2025-01-07T10:31:20Z",
  "error": "Extraction failed: ..."
}
```

**Flow:**
1. Query database for job_id
2. If completed, read JSON from `results/{uuid}.json`
3. Return status and result

### Optional Endpoint 3: List Jobs

**GET `/api/v1/extract/jobs?status=completed&limit=10`**

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "...",
      "file_name": "...",
      "status": "completed",
      "created_at": "...",
      "completed_at": "..."
    }
  ],
  "total": 42
}
```

---

## Migration from Current System

### Current State:
- Results saved to `results/{filename}.json`
- Logs saved to `logs/msa_extractor_{date}.log`
- No database tracking
- No UUID system

### Migration Steps:

1. **Create database schema** (new `storage/database.py`)
2. **Update `main.py`** to use database:
   - Generate UUID for each extraction
   - Save PDF to `uploads/{uuid}.pdf` (copy from original location)
   - Create database record
   - Save JSON to `results/{uuid}.json`
   - Save log to `logs/{uuid}.log` (or append to daily log)
3. **Add cleanup module** (`storage/cleanup.py`)
4. **Update CLI** to support cleanup command
5. **For FastAPI:** Create API endpoints using database module

---

## Implementation Phases

### Phase 1: Database & Storage Module (Immediate)
- [ ] Create `storage/database.py` with `ExtractionDB` class
- [ ] Create database schema (migrations or init script)
- [ ] Add configuration variables to `config.py`
- [ ] Create storage directories (`uploads/`, ensure `results/`, `logs/`)

### Phase 2: Integration with Current CLI (Before FastAPI)
- [ ] Update `main.py` to use database
- [ ] Generate UUIDs for each extraction
- [ ] Save PDFs to `uploads/{uuid}.pdf`
- [ ] Update result/log paths to use UUIDs
- [ ] Test with existing pipeline

### Phase 3: Cleanup Implementation
- [ ] Create `storage/cleanup.py` with cleanup functions
- [ ] Add `python main.py cleanup` CLI command
- [ ] Test cleanup logic (time-based and count-based)

### Phase 4: FastAPI Backend (Future)
- [ ] Create FastAPI app structure
- [ ] Implement upload endpoint (POST `/api/v1/extract/upload`)
- [ ] Implement get result endpoint (GET `/api/v1/extract/{job_id}`)
- [ ] Implement background task for extraction
- [ ] Implement background task for cleanup
- [ ] Add authentication/authorization (if needed)
- [ ] Add rate limiting (if needed)

---

## File Naming Convention

**UUID Format:** UUID v4 (e.g., `550e8400-e29b-41d4-a716-446655440000`)

**Files:**
- PDF: `uploads/{uuid}.pdf`
- JSON: `results/{uuid}.json`
- Log: `logs/{uuid}.log` (or `logs/msa_extractor_{date}.log` with UUID in log content)

**Database:**
- Primary key: `id` (UUID as TEXT)

---

## Security Considerations

1. **File Upload Validation:**
   - Validate file type (PDF only)
   - Validate file size (max limit)
   - Scan for malware (optional)

2. **UUID Security:**
   - UUIDs are unguessable (good for public API)
   - No sequential IDs that reveal job count
   - Can add authentication for additional security

3. **File Access:**
   - Store files outside web root (if serving via web server)
   - Use UUIDs to prevent directory traversal
   - Validate UUID format before file access

---

## Testing Strategy

1. **Database Tests:**
   - Test job creation, updates, queries
   - Test cleanup queries
   - Test concurrent access (if applicable)

2. **File Storage Tests:**
   - Test file saving with UUIDs
   - Test file deletion during cleanup
   - Test path handling (cross-platform)

3. **Cleanup Tests:**
   - Test time-based cleanup
   - Test count-based cleanup
   - Test edge cases (no files, all files too new, etc.)

4. **Integration Tests:**
   - Test full extraction flow with database
   - Test cleanup integration
   - Test error handling (failed extractions)

---

## Performance Considerations

1. **Database:**
   - SQLite is fine for single-server deployment
   - Consider connection pooling for FastAPI
   - Indexes on frequently queried columns

2. **File Storage:**
   - Consider using object storage (S3, GCS) for production
   - Local filesystem is fine for MVP

3. **Cleanup:**
   - Run cleanup as background task (don't block API)
   - Batch delete operations
   - Consider soft deletes (mark as deleted, delete later)

---

## Future Enhancements

1. **Object Storage:**
   - Migrate to S3/GCS for PDF storage
   - Keep SQLite for metadata
   - Use presigned URLs for file access

2. **Log Aggregation:**
   - Send logs to centralized logging service (e.g., Cloud Logging)
   - Keep file-based logs as backup

3. **Analytics:**
   - Track extraction success rates
   - Track processing times
   - Track field extraction accuracy

4. **Retention Policies:**
   - Configurable retention per job type
   - Archive old results instead of deleting
   - Compliance-aware retention

---

## Questions to Resolve

1. **Log Storage:** ✅ **Decided: File-based with metadata in DB**
2. **UUID Generation:** Use Python's `uuid.uuid4()` ✅
3. **Cleanup Frequency:** Daily at 2 AM (configurable) ✅
4. **PDF Storage:** Local filesystem for MVP, object storage later ✅
5. **Database:** SQLite for MVP, PostgreSQL later if needed ✅

---

## Next Steps

1. ✅ **Planning Complete** (this document)
2. ⏳ **Implementation:** Start with Phase 1 (Database & Storage Module)
3. ⏳ **Testing:** Test with existing pipeline before FastAPI work
4. ⏳ **FastAPI:** Build API endpoints after persistence is working

---

## References

- SQLite Documentation: https://www.sqlite.org/docs.html
- UUID Python Module: https://docs.python.org/3/library/uuid.html
- FastAPI File Uploads: https://fastapi.tiangolo.com/tutorial/request-files/
- FastAPI Background Tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/

