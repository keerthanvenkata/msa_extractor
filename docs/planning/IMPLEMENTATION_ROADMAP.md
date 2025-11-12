# Implementation Roadmap - Job Handling, Persistence & API

**Date:** November 12, 2025  
**Last Updated:** November 12, 2025  
**Status:** Active Development  
**Priority:** P1 - Core Features

**Note:** Cleanup service (Phase 3) has been deferred to next iteration. FastAPI backend (now Phase 3) is the current priority.

---

## Architecture Decision: Database-First (Iteration 1: SQLite + Local Storage)

### Iteration 1 (Current): SQLite + Local Storage
- **Database (SQLite)**: 
  - Job metadata, status, timestamps, extraction config
  - **JSON results stored in `result_json` column** (TEXT) - files are small (~1-5KB)
  - **Logs stored in `extraction_logs` table** (monthly tables: `extraction_logs_YYYY_MM`)
- **PDF Files**: Temporary storage in `uploads/{uuid}.pdf` (local filesystem)
  - Cleared after N days (configurable, default: 7 days)
  - Cloud Run provides ephemeral storage (enough for first run)
- **Default behavior**: Everything stored in database (JSON and logs)
- **Legacy mode**: CLI `--legacy` flag allows file-based storage (`results/`, `logs/` directories)
  - For backward compatibility
  - API always uses database (no legacy mode)

### Future Iterations (TODO)
- **GCS Integration**: Migrate PDF storage to Cloud Storage bucket
- **Cloud SQL**: Migrate from SQLite to Cloud SQL PostgreSQL
- **Partitioned Logs**: Use PostgreSQL table partitioning for logs

**Why Database-First?**
- JSON files are small (~1-5KB) - no performance impact storing in DB
- Logs in DB: Queryable, searchable, easier to manage
- Simpler deployment: No file system management for results/logs
- Better for API: Direct DB queries, no file I/O overhead for results
- Cloud Run compatible: Ephemeral storage for PDFs, SQLite for database

**Legacy Mode Support:**
- CLI `--legacy` flag: Allows file-based storage (`results/`, `logs/` directories)
- Backward compatibility: Existing workflows can continue using file-based storage
- Database still tracks job metadata even in legacy mode
- API always uses database (no legacy mode option)

---

## Task Breakdown

### Phase 1: Database & Storage Module ⏳ (Current)

#### 1.1 Create Database Module
- [ ] Create `storage/database.py` with `ExtractionDB` class
- [ ] Implement database initialization (`__init__`, `_init_db()`)
- [ ] Create `extractions` table schema (see schema below)
- [ ] Add indexes: `idx_extractions_status`, `idx_extractions_created_at`, `idx_extractions_file_name`
- [ ] Add database migration/versioning (optional, for future schema changes)

#### 1.2 Database Methods
- [ ] `create_job(file_name, file_path, file_size, extraction_method, llm_processing_mode, ocr_engine)` → returns UUID
- [ ] `get_job(job_id)` → returns job dict with `result_json` parsed
- [ ] `update_job_status(job_id, status, started_at=None, completed_at=None, error_message=None)`
- [ ] `complete_job(job_id, result_json_dict, pdf_storage_path, pdf_storage_type='local')` → stores JSON in DB
- [ ] `add_log_entry(job_id, level, message, module=None, details=None)` → adds to logs table
- [ ] `get_logs(job_id, limit=1000)` → returns log entries for job
- [ ] `list_jobs(status=None, limit=50, offset=0, sort='created_at DESC')`
- [ ] `delete_job(job_id)` (soft delete or hard delete)
- [ ] `get_jobs_for_cleanup(days_old, max_count)` → returns list of job IDs

#### 1.3 Configuration
- [ ] Add to `config.py`:
  - `DB_PATH` (already exists, verify default)
  - `UPLOADS_DIR` (new: `BASE_DIR / "uploads"`)
  - `CLEANUP_PDF_DAYS` (new: default 7)
  - `CLEANUP_PDF_MAX_COUNT` (new: default 1000)
  - `CLEANUP_PDF_MIN_COUNT` (new: default 500)
  - **GCP Configuration (for future iterations - TODO):**
    - `GCP_PROJECT_ID` (optional)
    - `GCP_STORAGE_BUCKET` (optional, for PDF storage)
    - `GCP_CLOUD_SQL_INSTANCE` (optional, for Cloud SQL)
    - `USE_GCS` (default: False, use GCS for PDF storage if True)
    - `USE_CLOUD_SQL` (default: False, use Cloud SQL if True)
    - **Note:** Iteration 1 uses SQLite + local storage only
- [ ] Create storage directories on startup:
  - `uploads/` (for temporary PDFs - local only)
  - `storage/` (for database)
  - `results/` (for legacy mode - file-based JSON storage)
  - `logs/` (for legacy mode - file-based log storage)
- [ ] **Note:** `results/` and `logs/` directories kept for legacy CLI mode, but default and API use database

#### 1.4 Testing
- [ ] Unit tests for `ExtractionDB` class
- [ ] Test database creation and schema
- [ ] Test all CRUD operations
- [ ] Test query methods (list, filter, sort)

---

### Phase 2: CLI Integration 🔄 (After Phase 1)

#### 2.1 Update Main CLI
- [ ] Modify `extract_single_file()` in `main.py`:
  - Add `--legacy` flag option (default: False, uses database)
  - Generate UUID for each extraction
  - Create database job record (status: "pending")
  - Copy PDF to `uploads/{uuid}.pdf` (local) or upload to GCS (if configured)
  - Update job status to "processing"
  - Run extraction
  - **If `--legacy` flag:**
    - Save JSON to `results/{uuid}.json` (file-based)
    - Save logs to `logs/{uuid}.log` (file-based)
    - Update database with file paths
  - **If default (no `--legacy` flag):**
    - **Store JSON result in `extractions.result_json` column** (database)
    - **Store logs in `extraction_logs` table** (database)
  - Update job status to "completed" with PDF storage path
  - Handle errors: update status to "failed" with error message, log to DB
- [ ] Modify `extract_batch()` in `main.py`:
  - Generate UUID for each file
  - Create job records for all files
  - Process files (same as single file)
  - Return list of job IDs

#### 2.2 CLI Commands
- [ ] Add `--legacy` flag to CLI (default: False)
  - When enabled: Use file-based storage (`results/`, `logs/` directories)
  - When disabled (default): Use database storage
  - API always uses database (no legacy mode)
- [ ] Add `--job-id` flag to `extract_single_file` (optional, for re-running failed jobs)
- [ ] Add `python main.py list-jobs [--status STATUS] [--limit N]` command
- [ ] Add `python main.py get-job <job_id>` command
- [ ] Update help text and documentation

#### 2.3 Logging Integration
- [ ] Create custom log handler that writes to `extraction_logs` table
- [ ] Update logger to accept `job_id` context
- [ ] **Default mode:** Store all log entries in database (with job_id, level, message, timestamp)
- [ ] **Legacy mode:** Write logs to `logs/{uuid}.log` files (when `--legacy` flag is used)
- [ ] Use monthly log tables (`extraction_logs_YYYY_MM`) for SQLite
- [ ] For GCP: Use partitioned table or monthly tables based on Cloud SQL type
- [ ] Ensure UUID is in all log messages for traceability
- [ ] **Note:** API always uses database logging (no legacy mode)

#### 2.4 Testing
- [ ] Test single file extraction with UUID
- [ ] Test batch extraction with UUIDs
- [ ] Test job status updates
- [ ] Test error handling and failed job tracking
- [ ] Verify files are saved with UUID names

---

### Phase 3: Cleanup Implementation 🧹 (Deferred to Next Iteration)

**Status:** Deferred to next iteration after FastAPI backend is complete.

**Rationale:** Cleanup service is not critical for initial API deployment. Manual cleanup can be performed via database queries if needed. Automated cleanup can be added after API is stable.

**Future Implementation:**
- [ ] Create `storage/cleanup.py` with `CleanupService` class
- [ ] Implement `cleanup_old_pdfs(days_old, max_count)`:
  - Query database for jobs older than N days
  - Delete PDF files from `uploads/` directory
  - Update database records (mark as cleaned)
  - Return cleanup statistics
- [ ] Implement `cleanup_failed_jobs(days_old)` (optional):
  - Clean up failed jobs older than N days
  - Delete associated files
- [ ] Add `python main.py cleanup [--days N] [--max-count N]` command
- [ ] Add `--dry-run` flag to preview what would be deleted
- [ ] Add scheduled cleanup task (cron-like or background thread)
- [ ] Test cleanup logic (time-based and count-based)

**Note:** Database method `get_jobs_for_cleanup()` is already implemented and ready for use when cleanup service is built.

---

### Phase 3: FastAPI Backend 🚀 (After Phase 2)

#### 3.1 FastAPI Structure
- [ ] Create `api/` directory structure:
  ```
  api/
  ├── __init__.py
  ├── main.py          # FastAPI app
  ├── routes/
  │   ├── __init__.py
  │   ├── extract.py    # Extraction endpoints
  │   └── health.py     # Health check
  ├── models/
  │   ├── __init__.py
  │   ├── requests.py   # Pydantic request models
  │   └── responses.py  # Pydantic response models
  ├── services/
  │   ├── __init__.py
  │   ├── extraction_service.py
  │   └── cleanup_service.py
  └── middleware/
      ├── __init__.py
      └── logging.py
  ```

#### 3.2 Dependencies
- [ ] Add to `requirements.txt`:
  - `fastapi>=0.104.0`
  - `uvicorn[standard]>=0.24.0`
  - `python-multipart>=0.0.6` (for file uploads)
  - `pydantic>=2.0.0` (for request/response models)

#### 3.3 API Endpoints

##### POST `/api/v1/extract/upload`
**Purpose:** Upload PDF/DOCX file and start extraction job

**Request:**
- `multipart/form-data`:
  - `file` (required): PDF or DOCX file
  - `extraction_method` (optional): Override default extraction method
  - `llm_processing_mode` (optional): Override default LLM processing mode

**Response (201 Created):**
```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "file_name": "contract.pdf",
  "file_size": 1024000,
  "created_at": "2025-11-12T10:30:00Z",
  "status_url": "/api/v1/extract/status/abc-123-def-456",
  "result_url": "/api/v1/extract/result/abc-123-def-456"
}
```

**Behavior:**
- Validates file type (PDF or DOCX)
- Validates file size (max: `MAX_UPLOAD_SIZE_MB`, default: 25MB)
- Generates UUID for job
- Saves file to `uploads/{uuid}.{ext}` (preserves extension)
- Creates database job record (status: "pending")
- Starts background extraction task (FastAPI BackgroundTasks)
- Returns immediately with job ID and status URLs

**Error Responses:**
- `400 Bad Request`: Invalid file type, file too large, missing file
- `500 Internal Server Error`: Server error during upload

---

##### GET `/api/v1/extract/status/{job_id}`
**Purpose:** Check extraction job status (lightweight polling endpoint)

**Response (200 OK):**
```json
{
  "job_id": "abc-123-def-456",
  "status": "processing",  // pending | processing | completed | failed
  "file_name": "contract.pdf",
  "created_at": "2025-11-12T10:30:00Z",
  "started_at": "2025-11-12T10:30:05Z",
  "completed_at": null,
  "error_message": null,
  "result_url": "/api/v1/extract/result/abc-123-def-456"  // Only if status="completed"
}
```

**Behavior:**
- Validates UUID format
- Queries database for job
- Returns lightweight status information
- Includes `result_url` when status is "completed"
- Client can poll this endpoint every 2-3 seconds

**Error Responses:**
- `404 Not Found`: Job ID not found

---

##### GET `/api/v1/extract/result/{job_id}`
**Purpose:** Get extracted metadata (only when job is completed)

**Response (200 OK - Completed):**
```json
{
  "job_id": "abc-123-def-456",
  "status": "completed",
  "file_name": "contract.pdf",
  "created_at": "2025-11-12T10:30:00Z",
  "completed_at": "2025-11-12T10:32:15Z",
  "metadata": {
    "Contract Lifecycle": {
      "Effective Date": "2025-01-01",
      ...
    },
    "Commercial Operations": { ... },
    "Risk & Compliance": { ... }
  }
}
```

**Response (202 Accepted - Not Ready):**
```json
{
  "error": "Job not completed yet",
  "status": "processing",
  "status_url": "/api/v1/extract/status/abc-123-def-456"
}
```

**Response (200 OK - Failed):**
```json
{
  "job_id": "abc-123-def-456",
  "status": "failed",
  "error_message": "Extraction failed: ...",
  "created_at": "2025-11-12T10:30:00Z",
  "failed_at": "2025-11-12T10:31:00Z"
}
```

**Behavior:**
- Validates UUID format
- Queries database for job
- **Returns `result_json` from `extractions.result_json` column** (database, no file I/O)
- If not completed: Returns 202 Accepted with status URL
- If failed: Returns error message
- **Note:** API always uses database (no legacy mode, no file I/O for results)

**Error Responses:**
- `202 Accepted`: Job not completed yet
- `404 Not Found`: Job ID not found

---

##### GET `/api/v1/extract/jobs` (Optional)
**Purpose:** List extraction jobs (for admin/monitoring)

**Query Parameters:**
- `status` (optional): Filter by status (`pending`, `processing`, `completed`, `failed`)
- `limit` (optional): Max results (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `sort` (optional): Sort order (default: `created_at DESC`)

**Response (200 OK):**
```json
{
  "jobs": [
    {
      "job_id": "abc-123-def-456",
      "status": "completed",
      "file_name": "contract.pdf",
      "created_at": "2025-11-12T10:30:00Z",
      "completed_at": "2025-11-12T10:32:15Z"
    }
  ],
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

---

##### GET `/api/v1/extract/{job_id}/logs` (Optional)
**Purpose:** Get log entries for a job

**Query Parameters:**
- `limit` (optional): Max log entries (default: 1000)
- `level` (optional): Filter by log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

**Response (200 OK):**
```json
{
  "job_id": "abc-123-def-456",
  "logs": [
    {
      "timestamp": "2025-11-12T10:30:05Z",
      "level": "INFO",
      "message": "Starting extraction",
      "module": "extractors.pdf_extractor",
      "details": null
    }
  ],
  "total": 15
}
```

**Behavior:**
- Queries `extraction_logs` table (monthly tables for SQLite)
- Returns log entries sorted by timestamp (descending)
- **Note:** API always uses database (no legacy mode, no file I/O for logs)

---

##### GET `/health`
**Purpose:** Health check endpoint

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "storage_type": "local",
  "timestamp": "2025-11-12T10:30:00Z"
}
```

**Behavior:**
- Checks database connection
- Returns API version and status
- Used by load balancers and monitoring

#### 3.4 Background Tasks
- [ ] Implement `process_extraction(job_id, file_path)` background task:
  - Update job status to "processing"
  - Run extraction using `ExtractionCoordinator`
  - **Store JSON result in `extractions.result_json` column** (database, always)
  - **Store logs in `extraction_logs` table** (database, always)
  - Update job status to "completed"
  - Handle errors: update status to "failed", log to DB
  - **Note:** API background tasks always use database (no legacy mode)
- [ ] **Note:** Background cleanup task deferred to next iteration

#### 3.5 Request/Response Models
- [ ] Create Pydantic models:
  - `UploadRequest` (file, extraction_method, llm_processing_mode, ocr_engine)
  - `UploadResponse` (job_id, status, created_at, file_name, file_size)
  - `JobResponse` (job_id, status, timestamps, file_name, result_json, error)
  - `JobListResponse` (jobs, total, limit, offset)
  - `LogEntryResponse` (timestamp, level, message, module, details)
  - `JobLogsResponse` (job_id, logs, total)
  - `HealthResponse` (status, version, database, storage_type, timestamp)

#### 3.6 Error Handling
- [ ] Handle file upload errors (size, type, etc.)
- [ ] Handle invalid UUID format
- [ ] Handle job not found (404)
- [ ] Handle extraction errors (500 with error details)
- [ ] Add proper HTTP status codes

#### 3.7 Configuration
- [ ] Add to `config.py`:
  - `API_HOST` (default: "0.0.0.0")
  - `API_PORT` (default: 8000)
  - `API_WORKERS` (default: 1)
  - `API_RELOAD` (default: False, for development)
  - `MAX_UPLOAD_SIZE_MB` (default: 25) - Maximum file upload size in MB
  - `API_MAX_CONCURRENT_EXTRACTIONS` (default: 5) - Max concurrent background extraction tasks
  - `API_ENABLE_AUTH` (default: False) - Enable API key authentication
  - `API_KEY` (default: "") - API key(s) for authentication (comma-separated for multiple keys)

#### 4.8 Startup/Shutdown
- [ ] Initialize database on startup
- [ ] Create storage directories on startup
- [ ] Register background tasks
- [ ] Graceful shutdown handling

#### 3.10 Testing
- [ ] Unit tests for API endpoints
- [ ] Integration tests with test database
- [ ] Test file upload (local and GCS)
- [ ] Test job status retrieval
- [ ] Test JSON result retrieval from database
- [ ] Test log retrieval from database
- [ ] Test error cases
- [ ] Test background task execution
- [ ] Test Cloud Run deployment (Iteration 1: SQLite + local storage)

#### 3.11 GCP Cloud Run Deployment (Iteration 1)
- [ ] Update `Dockerfile` for GCP Cloud Run deployment
- [ ] Configure SQLite database path for Cloud Run ephemeral storage
- [ ] Configure `uploads/` directory for Cloud Run ephemeral storage
- [ ] Add environment variable configuration
- [ ] Document Cloud Run deployment steps
- [ ] Test deployment on Cloud Run
- [ ] **Note:** Iteration 1 uses SQLite + local storage (Cloud Run ephemeral storage is sufficient)

#### 3.12 GCP Advanced Features (Future Iterations - TODO)
- [ ] Add GCP configuration options (Cloud SQL, GCS)
- [ ] Create GCS storage adapter for PDF uploads
- [ ] Add Cloud SQL connection support (PostgreSQL)
- [ ] Migrate from SQLite to Cloud SQL
- [ ] Migrate PDF storage from local to GCS
- [ ] Update log tables to use PostgreSQL partitioning
- [ ] Test local SQLite → Cloud SQL migration path
- [ ] Document GCS and Cloud SQL setup

#### 3.13 Docker Integration
- [ ] Update `Dockerfile` for API mode
- [ ] Update `docker-compose.yml` for API service
- [ ] Add health check endpoint to docker-compose
- [ ] Test Docker deployment

---

## Database Schema

### Table: `extractions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID v4 job identifier |
| `file_name` | TEXT | NOT NULL | Original filename |
| `file_size` | INTEGER | | File size in bytes |
| `status` | TEXT | NOT NULL | `pending`, `processing`, `completed`, `failed` |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Job creation time |
| `started_at` | TIMESTAMP | | When processing started |
| `completed_at` | TIMESTAMP | | When processing finished |
| `error_message` | TEXT | | Error details if failed |
| `result_json` | TEXT (JSON) | | **Extracted metadata JSON (stored in DB by default, NULL in legacy mode)** |
| `pdf_storage_path` | TEXT | | Path to PDF (local: `uploads/{uuid}.pdf`, GCP: GCS path) |
| `pdf_storage_type` | TEXT | | `local` (Iteration 1) or `gcs` (future) |
| `result_json_path` | TEXT | | **Legacy mode only:** Path to `results/{uuid}.json` file (if `--legacy` flag used) |
| `log_path` | TEXT | | **Legacy mode only:** Path to `logs/{uuid}.log` file (if `--legacy` flag used) |
| `extraction_method` | TEXT | | EXTRACTION_METHOD used |
| `llm_processing_mode` | TEXT | | LLM_PROCESSING_MODE used |
| `ocr_engine` | TEXT | | OCR_ENGINE used (if applicable) |
| `metadata` | TEXT | | Additional metadata (JSON string) |

**Indexes:**
- `idx_extractions_status` on `status`
- `idx_extractions_created_at` on `created_at`
- `idx_extractions_file_name` on `file_name`

### Table: `extraction_logs` (Monthly Tables or Single Partitioned Table)

**Option 1: Monthly Tables** (Recommended for SQLite)
- `extraction_logs_2025_11`, `extraction_logs_2025_12`, etc.
- Easier to archive/delete old months
- Simpler queries per month
- Auto-create new month table when needed

**Option 2: Single Table with Partitioning** (For Cloud SQL PostgreSQL)
- Single `extraction_logs` table
- Partition by month using `timestamp` column
- Better for Cloud SQL PostgreSQL
- Automatic partition management

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Log entry ID |
| `extraction_id` | TEXT (UUID) | NOT NULL, FOREIGN KEY | References `extractions.id` |
| `timestamp` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Log entry time |
| `level` | TEXT | NOT NULL | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `message` | TEXT | NOT NULL | Log message |
| `module` | TEXT | | Module/logger name |
| `details` | TEXT (JSON) | | Additional structured data (JSON string) |

**Indexes:**
- `idx_extraction_logs_extraction_id` on `extraction_id`
- `idx_extraction_logs_timestamp` on `timestamp`
- `idx_extraction_logs_level` on `level`

**Note:** For monthly tables, indexes are per table. For partitioned table, indexes are global.

---

## Storage Structure

### Iteration 1: Local Development & Cloud Run (SQLite + Local Storage)
```
project_root/ (or Cloud Run ephemeral storage):
├── uploads/              # Temporary PDFs (cleaned up after N days)
│   ├── {uuid1}.pdf
│   ├── {uuid2}.pdf
│   └── ...
├── results/              # Legacy mode only (file-based JSON storage)
│   ├── {uuid1}.json      # Only used with --legacy flag
│   └── ...
├── logs/                 # Legacy mode only (file-based log storage)
│   ├── {uuid1}.log       # Only used with --legacy flag
│   └── ...
└── storage/              # Database
    └── msa_extractor.db  # SQLite database
        ├── extractions table (with result_json column)
        └── extraction_logs_YYYY_MM tables (monthly)
```

**Default Behavior (Database Storage):**
- JSON results stored in `extractions.result_json` column
- Logs stored in `extraction_logs` table
- No files in `results/` or `logs/` directories

**Legacy Mode (`--legacy` flag):**
- JSON results saved to `results/{uuid}.json` files
- Logs saved to `logs/{uuid}.log` files
- Database still tracks job metadata
- For backward compatibility with existing workflows

**Cloud Run Deployment:**
- Uses ephemeral storage for `uploads/` and `storage/` directories
- SQLite database stored in ephemeral storage
- PDFs cleared after N days (configurable)
- API always uses database (no legacy mode)
- Sufficient for Iteration 1

### Future Iterations: GCP Production (Cloud SQL + Cloud Storage)
```
Cloud SQL (PostgreSQL):
├── extractions table (with result_json JSONB column)
└── extraction_logs table (partitioned by month)

Cloud Storage (GCS):
└── gs://{bucket-name}/pdfs/
    ├── {uuid1}.pdf
    ├── {uuid2}.pdf
    └── ...
```

**Note:** 
- **Iteration 1 (Default):** JSON results stored in `extractions.result_json` column (database)
- **Iteration 1 (Default):** Logs stored in `extraction_logs` table (database)
- **Iteration 1 (Legacy Mode):** JSON and logs saved to files (`results/`, `logs/` directories) when `--legacy` flag is used
- **Iteration 1:** Only PDFs stored as files (local filesystem, Cloud Run ephemeral storage)
- **API:** Always uses database (no legacy mode)
- **Future:** PDFs migrated to GCS, database migrated to Cloud SQL

---

## Implementation Order

1. **Phase 1** (Database & Storage) → Foundation ✅
2. **Phase 2** (CLI Integration) → Test with existing pipeline ✅
   - Default mode: Database storage
   - Legacy mode: File-based storage (`--legacy` flag)
3. **Phase 3** (FastAPI Backend) → API service (Current Priority)
   - Always uses database (no legacy mode)
4. **Phase 4** (Cleanup Service) → Deferred to Next Iteration
   - Automated PDF cleanup after N days
   - CLI cleanup command
   - Background scheduled cleanup

---

## Notes

- **Data Masking/Encryption**: Deferred to v2 (after API is live)
- **Chunking**: Deferred to next iteration (current docs fit within limits)
- **Testing**: Each phase should be tested before moving to next
- **Documentation**: Update docs as we implement each phase

---

## Questions to Resolve

1. **Log Storage**: Per-job log files (`logs/{uuid}.log`) or daily logs with UUID in content?
   - **Decision**: Per-job log files for easier debugging and API access
2. **Cleanup Frequency**: Deferred to next iteration (manual cleanup via database queries available if needed)
   - **Decision**: Both - CLI command for manual, optional background task
3. **Job Deletion**: Soft delete (mark as deleted) or hard delete (remove from DB)?
   - **Decision**: Hard delete for simplicity (can add soft delete later if needed)

---

**Last Updated:** November 12, 2025

