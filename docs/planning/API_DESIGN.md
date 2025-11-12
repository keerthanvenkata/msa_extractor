# API Design Specification

**Last Updated:** November 12, 2025  
**Status:** Design Phase  
**Version:** v1.0

---

## Overview

This document specifies the REST API endpoints for the MSA Metadata Extractor service. The API provides endpoints for uploading documents, checking job status, and retrieving extraction results.

---

## Base URL

```
http://localhost:8000/api/v1
```

For production:
```
https://your-domain.com/api/v1
```

---

## Authentication

### Iteration 1: API Key Authentication (Recommended)

**Simple API Key** - Best balance of simplicity and security for v1:

**Implementation:**
- API key passed in header: `X-API-Key: <key>`
- Or query parameter: `?api_key=<key>` (less secure, but simpler for testing)
- API key stored in environment variable: `API_KEY`
- Enable/disable via `API_ENABLE_AUTH` (default: `false` for development)

**Usage:**
```bash
# With header (recommended)
curl -H "X-API-Key: your-api-key-here" \
     -F "file=@contract.pdf" \
     http://localhost:8000/api/v1/extract/upload

# With query parameter (for testing)
curl -F "file=@contract.pdf" \
     "http://localhost:8000/api/v1/extract/upload?api_key=your-api-key-here"
```

**Response if unauthorized:**
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```
Status: `401 Unauthorized`

**Why API Key for v1:**
- ✅ Simple to implement (single key in env var)
- ✅ Easy to upgrade later (can add JWT/OAuth2 without breaking changes)
- ✅ Good enough for single-tenant or small deployments
- ✅ Can be enhanced with database-stored keys later
- ✅ No external dependencies

---

### Authentication Options Comparison

| Option | Complexity | Security | Multi-user | Upgrade Path | Recommendation |
|--------|-----------|----------|-----------|-------------|----------------|
| **No Auth** | Simplest | ❌ None | ❌ No | N/A | ❌ Not for production |
| **API Key** | Simple | ✅ Good | ⚠️ Single key | ✅ Easy | ✅ **Best for v1** |
| **JWT Tokens** | Medium | ✅ Good | ✅ Yes | ✅ Standard | ⚠️ Overkill for v1 |
| **OAuth2** | Complex | ✅ Excellent | ✅ Yes | ✅ Enterprise | ❌ Overkill for v1 |
| **Basic Auth** | Simple | ⚠️ Weak | ⚠️ Limited | ⚠️ Hard | ❌ Not recommended |

---

### Future Enhancements

**Phase 2 (Multi-user support):**
- JWT tokens with user authentication
- Database-stored API keys per user
- Rate limiting per API key
- Token expiration and refresh

**Phase 3 (Enterprise):**
- OAuth2 integration
- Role-based access control (RBAC)
- API key management dashboard
- Audit logging

**Migration Path:**
- API key authentication can coexist with JWT/OAuth2
- Add new endpoints with JWT, keep API key for backward compatibility
- Gradual migration without breaking existing clients

---

## Endpoints

### 1. POST `/api/v1/extract/upload`

Upload a PDF or DOCX file and start extraction job.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file` (required): PDF or DOCX file
  - `extraction_method` (optional): Override default (`text_direct`, `ocr_all`, `ocr_images_only`, `vision_all`, `hybrid`)
  - `llm_processing_mode` (optional): Override default (`text_llm`, `vision_llm`, `multimodal`, `dual_llm`)

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

**Error Responses:**
- `400 Bad Request`: Invalid file type, file too large, missing file
- `401 Unauthorized`: Invalid or missing API key (if auth enabled)
- `500 Internal Server Error`: Server error during upload

**Validation:**
- File type: PDF or DOCX only
- File size: Max `MAX_UPLOAD_SIZE_MB` (default: 25MB)
- File must be provided

**Behavior:**
1. Validates file type and size
2. Generates UUID for job
3. Saves file to `uploads/{uuid}.{ext}` (preserves extension)
4. Creates database job record (status: "pending")
5. Starts background extraction task
6. Returns immediately with job ID

---

### 2. GET `/api/v1/extract/status/{job_id}`

Check extraction job status (lightweight polling endpoint).

**Request:**
- Method: `GET`
- Path parameter: `job_id` (UUID)

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

**Error Responses:**
- `404 Not Found`: Job ID not found
- `401 Unauthorized`: Invalid or missing API key (if auth enabled)

**Polling Strategy:**
- Client should poll every 2-3 seconds
- When `status="completed"`, call `/result/{job_id}` to get metadata
- When `status="failed"`, check `error_message` field

---

### 3. GET `/api/v1/extract/result/{job_id}`

Get extracted metadata (only when job is completed).

**Request:**
- Method: `GET`
- Path parameter: `job_id` (UUID)

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
      "Expiration / Termination Date": "2028-03-31",
      "Authorized Signatory": "John Doe, VP of Operations",
      ...
    },
    "Commercial Operations": {
      "Billing Frequency": "Monthly",
      "Payment Terms": "Net 30 days from invoice date",
      ...
    },
    "Risk & Compliance": {
      "Indemnification Clause Reference": "Section 12 – Indemnification",
      ...
    }
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
  "error_message": "Extraction failed: File not found",
  "created_at": "2025-11-12T10:30:00Z",
  "failed_at": "2025-11-12T10:31:00Z"
}
```

**Error Responses:**
- `202 Accepted`: Job not completed yet (poll status endpoint)
- `404 Not Found`: Job ID not found
- `401 Unauthorized`: Invalid or missing API key (if auth enabled)

**Behavior:**
- Returns `result_json` from database (`extractions.result_json` column)
- No file I/O - always uses database
- If not completed, returns 202 with status URL for polling

---

### 4. GET `/api/v1/extract/jobs` (Optional)

List extraction jobs (for admin/monitoring).

**Request:**
- Method: `GET`
- Query parameters:
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
    },
    {
      "job_id": "def-456-ghi-789",
      "status": "processing",
      "file_name": "agreement.docx",
      "created_at": "2025-11-12T10:35:00Z",
      "completed_at": null
    }
  ],
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

---

### 5. GET `/api/v1/extract/{job_id}/logs` (Optional)

Get log entries for a job.

**Request:**
- Method: `GET`
- Path parameter: `job_id` (UUID)
- Query parameters:
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
    },
    {
      "timestamp": "2025-11-12T10:30:10Z",
      "level": "DEBUG",
      "message": "Detected PDF type: mixed",
      "module": "extractors.pdf_extractor",
      "details": "text_pages: 5, image_pages: 1"
    }
  ],
  "total": 15
}
```

---

### 6. GET `/health`

Health check endpoint (for load balancers and monitoring).

**Request:**
- Method: `GET`
- No authentication required

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

**Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "Database connection failed"
}
```

---

## Client Usage Flow

### Typical Client Flow

1. **Upload File:**
   ```bash
   POST /api/v1/extract/upload
   Content-Type: multipart/form-data
   
   Response: { "job_id": "abc-123", "status": "pending", ... }
   ```

2. **Poll Status:**
   ```bash
   GET /api/v1/extract/status/abc-123
   
   Response: { "status": "processing", ... }
   ```
   - Poll every 2-3 seconds
   - Continue until `status="completed"` or `status="failed"`

3. **Get Result:**
   ```bash
   GET /api/v1/extract/result/abc-123
   
   Response: { "status": "completed", "metadata": { ... } }
   ```

### Error Handling

- **Job Failed:** Check `error_message` in status or result endpoint
- **Job Not Found:** 404 response
- **File Too Large:** 400 response with error message
- **Invalid File Type:** 400 response with error message

---

## Background Tasks

### Extraction Task

- Uses FastAPI `BackgroundTasks` (Iteration 1)
- Max concurrent: `API_MAX_CONCURRENT_EXTRACTIONS` (default: 5)
- Future: Upgrade to Celery for distributed processing

**Task Flow:**
1. Update job status to "processing"
2. Run extraction using `ExtractionCoordinator`
3. Store JSON result in `extractions.result_json` column
4. Store logs in `extraction_logs` table
5. Update job status to "completed" or "failed"

---

## Configuration

See [Configuration Reference](../setup/configuration.md) for all API-related configuration options:

- `API_HOST`, `API_PORT`, `API_WORKERS`
- `MAX_UPLOAD_SIZE_MB` (default: 25MB)
- `API_MAX_CONCURRENT_EXTRACTIONS` (default: 5)
- `API_ENABLE_AUTH` (default: false)
- `API_KEY` (required if auth enabled)

---

## Future Enhancements

- **Webhooks:** Push notifications when job completes
- **Progress Tracking:** Percentage completion in status endpoint
- **Rate Limiting:** Per-API-key rate limits
- **JWT Authentication:** Multi-user support
- **OAuth2:** Enterprise authentication
- **Celery:** Distributed task queue
- **WebSocket:** Real-time status updates

---

## Related Documentation

- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) - Phase 4 details
- [Persistence Plan](PERSISTENCE_PLAN.md) - Database schema
- [Configuration Reference](../setup/configuration.md) - All config options

