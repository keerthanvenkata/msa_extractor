# Storage Database Module

**Last Updated:** November 12, 2025  
**Module:** `storage.database`  
**Class:** `ExtractionDB`

---

## Overview

The `storage.database` module provides SQLite-based persistence for the MSA Metadata Extractor. It handles job tracking, result storage, and logging with support for both database-first (default) and legacy file-based storage modes.

---

## Architecture

### Database-First Design (Default)
- **JSON Results:** Stored in `extractions.result_json` column (TEXT)
- **Logs:** Stored in monthly tables (`extraction_logs_YYYY_MM`)
- **PDFs:** Stored as files in `uploads/{uuid}.{ext}` directory
- **No separate result/log files** - everything queryable from database

### Legacy Mode Support
- **JSON Results:** Saved to `results/{uuid}.json` files
- **Logs:** Still stored in database (file-based logging not implemented)
- **Database:** Still tracks job metadata with file paths
- **Purpose:** Backward compatibility with existing workflows

---

## Database Schema

### Table: `extractions`

Primary table for tracking all extraction jobs.

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Primary key, UUID v4 job identifier |
| `file_name` | TEXT | Original filename |
| `file_size` | INTEGER | File size in bytes |
| `status` | TEXT | `pending`, `processing`, `completed`, `failed` |
| `created_at` | TIMESTAMP | Job creation time (DEFAULT CURRENT_TIMESTAMP) |
| `started_at` | TIMESTAMP | When processing started |
| `completed_at` | TIMESTAMP | When processing finished |
| `error_message` | TEXT | Error details if failed |
| `result_json` | TEXT (JSON) | Extracted metadata JSON (default mode) |
| `pdf_storage_path` | TEXT | Path to stored file (`uploads/{uuid}.{ext}`) |
| `pdf_storage_type` | TEXT | `local` (Iteration 1) or `gcs` (future) |
| `result_json_path` | TEXT | Legacy mode: path to JSON file |
| `log_path` | TEXT | Legacy mode: path to log file |
| `extraction_method` | TEXT | EXTRACTION_METHOD used |
| `llm_processing_mode` | TEXT | LLM_PROCESSING_MODE used |
| `ocr_engine` | TEXT | OCR_ENGINE used (if applicable) |
| `metadata` | TEXT (JSON) | Additional metadata |

**Indexes:**
- `idx_extractions_status` on `status`
- `idx_extractions_created_at` on `created_at`
- `idx_extractions_file_name` on `file_name`

### Table: `extraction_logs_YYYY_MM` (Monthly Tables)

Log entries stored in monthly tables for efficient management.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key (AUTOINCREMENT) |
| `extraction_id` | TEXT (UUID) | Foreign key to `extractions.id` |
| `timestamp` | TIMESTAMP | Log entry time (DEFAULT CURRENT_TIMESTAMP) |
| `level` | TEXT | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `message` | TEXT | Log message |
| `module` | TEXT | Module name (optional) |
| `details` | TEXT | Additional details (optional) |

**Indexes:**
- `idx_extraction_logs_YYYY_MM_extraction_id` on `extraction_id`

---

## Class: `ExtractionDB`

### Initialization

```python
from storage.database import ExtractionDB

# Use default database path (from config.DB_PATH)
# Recommended: Use context manager for automatic cleanup
with ExtractionDB() as db:
    # Use database
    job_id = db.create_job(...)
    # Connection automatically closed when exiting context

# Or specify custom path
with ExtractionDB(db_path=Path("custom/path.db")) as db:
    # Use database
    pass

# Manual management (not recommended)
db = ExtractionDB()
try:
    # Use database
    pass
finally:
    db.close()
```

**Behavior:**
- Creates database file if it doesn't exist
- Creates parent directory if needed
- Initializes schema (tables and indexes)
- Creates current month's log table
- Sets `row_factory` to `sqlite3.Row` for dict-like access

### Methods

#### `create_job(file_name, pdf_storage_path, file_size=None, extraction_method=None, llm_processing_mode=None, ocr_engine=None) -> str`

Create a new extraction job.

**Parameters:**
- `file_name` (str): Original filename
- `pdf_storage_path` (str): Path to stored file (can be empty initially)
- `file_size` (int, optional): File size in bytes
- `extraction_method` (str, optional): EXTRACTION_METHOD used
- `llm_processing_mode` (str, optional): LLM_PROCESSING_MODE used
- `ocr_engine` (str, optional): OCR_ENGINE used

**Returns:**
- `str`: Job UUID (v4)

**Example:**
```python
job_id = db.create_job(
    file_name="contract.pdf",
    pdf_storage_path="uploads/abc-123.pdf",
    file_size=1024000,
    extraction_method="hybrid",
    llm_processing_mode="text_llm"
)
```

#### `get_job(job_id: str) -> Optional[Dict[str, Any]]`

Get a job by ID with parsed JSON fields.

**Parameters:**
- `job_id` (str): Job UUID

**Returns:**
- `Optional[Dict]`: Job dict with `result_json` and `metadata` parsed, or `None` if not found

**Example:**
```python
job = db.get_job("abc-123-def-456")
if job:
    print(f"Status: {job['status']}")
    print(f"Result: {job['result_json']}")
```

#### `update_job_status(job_id, status, started_at=None, completed_at=None, error_message=None)`

Update job status and timestamps.

**Parameters:**
- `job_id` (str): Job UUID
- `status` (str): New status (`pending`, `processing`, `completed`, `failed`)
- `started_at` (datetime, optional): When processing started
- `completed_at` (datetime, optional): When processing finished
- `error_message` (str, optional): Error message if failed

**Example:**
```python
db.update_job_status(
    job_id,
    "processing",
    started_at=datetime.now()
)
```

#### `complete_job(job_id, result_json_dict, pdf_storage_path, pdf_storage_type='local', result_json_path=None, log_path=None)`

Mark job as completed and store result JSON.

**Parameters:**
- `job_id` (str): Job UUID
- `result_json_dict` (dict): Extracted metadata as dict
- `pdf_storage_path` (str): Path to stored file
- `pdf_storage_type` (str): Storage type (`local` or `gcs`)
- `result_json_path` (str, optional): Legacy mode - path to JSON file
- `log_path` (str, optional): Legacy mode - path to log file

**Example:**
```python
db.complete_job(
    job_id=job_id,
    result_json_dict=metadata,
    pdf_storage_path="uploads/abc-123.pdf",
    pdf_storage_type="local"
)
```

#### `add_log_entry(job_id, level, message, module=None, details=None, timestamp=None)`

Add a log entry to the current month's log table.

**Parameters:**
- `job_id` (str): Job UUID
- `level` (str): Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- `message` (str): Log message
- `module` (str, optional): Module name
- `details` (str, optional): Additional details
- `timestamp` (datetime, optional): Log timestamp (defaults to now)

**Example:**
```python
db.add_log_entry(
    job_id,
    "ERROR",
    "Extraction failed",
    module="extractors.pdf_extractor",
    details="File not found"
)
```

#### `get_logs(job_id, limit=1000, level=None) -> List[Dict[str, Any]]`

Get log entries for a job, searching across all monthly tables.

**Parameters:**
- `job_id` (str): Job UUID
- `limit` (int): Maximum number of entries to return
- `level` (str, optional): Filter by log level

**Returns:**
- `List[Dict]`: List of log entry dicts, sorted by timestamp descending

**Example:**
```python
error_logs = db.get_logs(job_id, level="ERROR", limit=100)
```

#### `list_jobs(status=None, limit=50, offset=0, sort='created_at DESC') -> List[Dict[str, Any]]`

List jobs with optional filtering, sorting, and pagination.

**Parameters:**
- `status` (str, optional): Filter by status
- `limit` (int): Maximum number of jobs to return
- `offset` (int): Number of jobs to skip
- `sort` (str): SQL ORDER BY clause

**Returns:**
- `List[Dict]`: List of job dicts with parsed JSON fields

**Example:**
```python
completed_jobs = db.list_jobs(status="completed", limit=10)
```

#### `delete_job(job_id, hard_delete=False)`

Delete a job (hard delete only currently).

**Parameters:**
- `job_id` (str): Job UUID
- `hard_delete` (bool): If True, permanently delete (default: False, but currently always hard deletes)

**Note:** Currently always performs hard delete. Soft delete not implemented.

#### `get_jobs_for_cleanup(days_old, max_count=None) -> List[str]`

Get job IDs eligible for cleanup.

**Parameters:**
- `days_old` (int): Delete PDFs older than N days
- `max_count` (int, optional): Maximum number of PDFs to keep

**Returns:**
- `List[str]`: List of job IDs

**Example:**
```python
# Time-based cleanup: jobs older than 7 days
old_jobs = db.get_jobs_for_cleanup(days_old=7)

# Count-based cleanup: keep only 100 most recent
old_jobs = db.get_jobs_for_cleanup(days_old=365, max_count=100)
```

#### `close()`

Close database connection.

**Example:**
```python
db = ExtractionDB()
# Use database
db.close()
```

---

## Usage Examples

### Basic Job Lifecycle

```python
from storage.database import ExtractionDB
from datetime import datetime

# Recommended: Use context manager for automatic cleanup
with ExtractionDB() as db:
    # Create job
    job_id = db.create_job(
        file_name="contract.pdf",
        pdf_storage_path="uploads/abc-123.pdf",
        file_size=1024000
    )
    
    # Update status
    db.update_job_status(job_id, "processing", started_at=datetime.now())
    
    # Add log entry
    db.add_log_entry(job_id, "INFO", "Starting extraction")
    
    # Complete job
    db.complete_job(
        job_id=job_id,
        result_json_dict={"Contract Lifecycle": {"Effective Date": "2025-01-01"}},
        pdf_storage_path="uploads/abc-123.pdf"
    )
    
    # Get job
    job = db.get_job(job_id)
    print(f"Status: {job['status']}")
    print(f"Result: {job['result_json']}")
    
    # Get logs
    logs = db.get_logs(job_id)
    for log in logs:
        print(f"{log['timestamp']} [{log['level']}] {log['message']}")
    # Database automatically closed when exiting context
```

### Legacy Mode Support

```python
# Complete job in legacy mode (file-based storage)
db.complete_job(
    job_id=job_id,
    result_json_dict=None,  # Not stored in DB
    pdf_storage_path="uploads/abc-123.pdf",
    result_json_path="results/abc-123.json",  # File path
    log_path="logs/abc-123.log"  # File path
)
```

---

## Configuration

Database path and storage directories are configured in `config.py`:

- `DB_PATH`: Database file path (default: `storage/msa_extractor.db`)
- `UPLOADS_DIR`: Directory for uploaded files (default: `uploads/`)
- `RESULTS_DIR`: Directory for legacy mode JSON files (default: `results/`)
- `LOGS_DIR`: Directory for legacy mode log files (default: `logs/`)

---

## Error Handling

The module uses standard Python exceptions:
- `sqlite3.Error`: Database operation errors
- `ValueError`: Invalid parameters
- `FileNotFoundError`: Database file path issues

All errors are logged using the centralized logging system.

---

## Thread Safety

- SQLite connections are **not thread-safe** by default
- `check_same_thread=False` is set to allow connection reuse
- For multi-threaded applications, use connection pooling or one connection per thread

---

## Performance Considerations

- **Indexes:** Created on `status`, `created_at`, and `file_name` for fast queries
- **Monthly Log Tables:** Prevents single large table, easier to archive/delete
- **JSON Storage:** Small files (~1-5KB) stored as TEXT, no performance impact
- **Connection Reuse:** Use context manager or reuse `ExtractionDB` instance when possible

---

## Future Enhancements

- **Cloud SQL Support:** Migration to PostgreSQL for production
- **Connection Pooling:** For multi-threaded FastAPI backend
- **Soft Delete:** Mark jobs as deleted instead of hard delete
- **Archive Old Logs:** Move old monthly log tables to archive
- **GCS Integration:** Store PDFs in Google Cloud Storage

---

## Related Documentation

- [Persistence Plan](../planning/PERSISTENCE_PLAN.md)
- [Implementation Roadmap](../planning/IMPLEMENTATION_ROADMAP.md)
- [Main CLI Module](main_cli.md)

