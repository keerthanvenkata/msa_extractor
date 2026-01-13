# Local Testing Guide

**Last Updated:** November 14, 2025  
**Status:** Active

This guide covers testing the MSA Metadata Extractor API locally before deploying to Cloud Run.

---

## Quick Start: Test with Uvicorn (Recommended for Development)

### Step 1: Activate Virtual Environment

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Or if you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### Step 2: Set Environment Variables

```powershell
# Required: Gemini API Key
$env:GEMINI_API_KEY = "your-gemini-api-key"

# Optional: API Authentication (set to false for local testing)
$env:API_ENABLE_AUTH = "false"

# Optional: Database path (defaults to ./storage/msa_extractor.db)
$env:DB_PATH = "./storage/msa_extractor.db"
```

### Step 3: Run the API

```powershell
# Option 1: Run directly with uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload

# Option 2: Run via Python module
python -m api.main

# Option 3: Run via main.py (if configured)
python main.py
```

### Step 4: Test the API

**Health Check:**
```powershell
# Option 1: Using curl.exe (if available)
curl.exe http://localhost:8080/api/v1/health

# Option 2: Using Invoke-RestMethod (PowerShell native)
Invoke-RestMethod -Uri http://localhost:8080/api/v1/health -Method Get
```

**Upload a File:**
```powershell
# Using Invoke-RestMethod (PowerShell native - recommended)
$filePath = "templates/template.pdf"
$uri = "http://localhost:8080/api/v1/extract/upload"

$form = @{
    file = Get-Item -Path $filePath
    extraction_method = "hybrid"
    llm_processing_mode = "multimodal"
}

$response = Invoke-RestMethod -Uri $uri -Method Post -Form $form
$response | ConvertTo-Json

# Save job_id for later use
$jobId = $response.job_id
Write-Host "Job ID: $jobId"
```

**Check Job Status:**
```powershell
# Replace {job_id} with the UUID returned from upload
$jobId = "your-job-id-here"
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/extract/status/$jobId" -Method Get | ConvertTo-Json
```

**Get Results:**
```powershell
# Replace {job_id} with the UUID returned from upload
$jobId = "your-job-id-here"
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/extract/result/$jobId" -Method Get | ConvertTo-Json
```

**Alternative: Using curl.exe (if installed):**
```powershell
# If you have curl.exe installed (not PowerShell's alias)
curl.exe -X POST http://localhost:8080/api/v1/extract/upload `
  -F "file=@templates/template.pdf" `
  -F "extraction_method=hybrid" `
  -F "llm_processing_mode=multimodal"
```

**View API Documentation:**
- Open browser: http://localhost:8080/docs
- Interactive Swagger UI for testing

---

## Testing with Docker (Matches Production Environment)

### Step 1: Build Docker Image

```powershell
docker build -t msa-extractor-api:local .
```

### Step 2: Run Container

```powershell
docker run -p 8080:8080 `
  -e GEMINI_API_KEY="your-gemini-api-key" `
  -e API_ENABLE_AUTH="false" `
  -v ${PWD}/storage:/app/storage `
  -v ${PWD}/uploads:/app/uploads `
  msa-extractor-api:local
```

**Note:** The `-v` flags mount local directories so database and uploads persist between container restarts.

### Step 3: Test (Same as above)

Use the same curl commands, but ensure the container is running.

---

## Understanding the "Job not found" Issue

### Root Cause

**In Cloud Run:** SQLite database is stored in **ephemeral container filesystem** (`/app/storage/msa_extractor.db`). When a container:
- Restarts
- Scales to zero and back up
- Is updated/redeployed

The database is **lost**, and all jobs disappear.

### Why It Happens

1. Job is created → stored in SQLite database
2. Job starts processing → status = "processing"
3. Container restarts (or scales) → database file is deleted
4. New container starts → new empty database
5. Status check → "Job not found" error

### Workarounds

**Option 1: Set Minimum Instances (Prevents Scale-to-Zero)**

```powershell
gcloud run deploy msa-extractor-api `
  --min-instances 1 `
  --image gcr.io/$PROJECT_ID/msa-extractor-api
```

**Note:** This prevents scale-to-zero but doesn't prevent restarts during updates.

**Option 2: Use Cloud SQL (Production Solution)**

Migrate from SQLite to Cloud SQL PostgreSQL for persistent storage. See [BUG-029](../../ISSUES_AND_TODOS.md#bug-029-ephemeral-database-storage-in-cloud-run).

**Option 3: Accept Limitation (Development/Testing Only)**

For development/testing, accept that jobs are lost on restart. This is documented in [GCP_DEPLOYMENT.md](../setup/GCP_DEPLOYMENT.md).

---

## Testing Scenarios

### Scenario 1: Basic Extraction

1. Upload a PDF file
2. Get job ID
3. Poll status until "completed"
4. Get results
5. Verify extracted metadata

### Scenario 2: Long-Running Job

1. Upload a large PDF (10+ MB)
2. Monitor status (should be "processing" for a while)
3. Wait for completion
4. Verify results

### Scenario 3: Error Handling

1. Upload invalid file (e.g., .txt file)
2. Verify error response
3. Check job status shows "failed"
4. Verify error message

### Scenario 4: Concurrent Jobs

1. Upload multiple files simultaneously
2. Get all job IDs
3. Poll all statuses
4. Verify all complete successfully

### Scenario 5: Database Persistence (Local Testing)

1. Upload a file
2. Get job ID
3. **Stop the API server**
4. **Restart the API server**
5. Check job status (should still exist locally)
6. **Note:** In Cloud Run, this would fail (ephemeral storage)

---

## Debugging Tips

### Check Database

```powershell
# View database file
ls -la storage/msa_extractor.db

# Query database (if sqlite3 is installed)
sqlite3 storage/msa_extractor.db "SELECT id, status, file_name, created_at FROM extractions ORDER BY created_at DESC LIMIT 10;"
```

### Check Logs

```powershell
# View application logs
# Logs are in the console output when running with uvicorn
# Or check storage/logs/ if file-based logging is enabled
```

### Check Uploads

```powershell
# View uploaded files
ls -la uploads/
```

### Enable Debug Logging

```powershell
$env:LOG_LEVEL = "DEBUG"
uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```

---

## Common Issues

### Issue: "Job not found" after deployment

**Cause:** Container restarted, database lost (ephemeral storage)

**Solution:** 
- For testing: Use local testing with persistent storage
- For production: Migrate to Cloud SQL

### Issue: "Module not found" errors

**Cause:** Missing dependencies

**Solution:**
```powershell
pip install -r requirements.txt
```

### Issue: "GEMINI_API_KEY not set"

**Cause:** Missing environment variable

**Solution:**
```powershell
$env:GEMINI_API_KEY = "your-key"
```

### Issue: Port already in use

**Cause:** Another process using port 8080

**Solution:**
```powershell
# Use different port
uvicorn api.main:app --host 0.0.0.0 --port 8081 --reload

# Or kill existing process
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

---

## Next Steps

1. ✅ Test locally with uvicorn
2. ✅ Test with Docker
3. ✅ Verify all endpoints work
4. ✅ Test error handling
5. ⏳ Deploy to Cloud Run (with known limitations)
6. ⏳ Plan Cloud SQL migration (for production)

---

## References

- [GCP Deployment Guide](../setup/GCP_DEPLOYMENT.md)
- [Environment Variables Guide](../setup/ENV_VARIABLES.md)
- [API Design Specification](../planning/API_DESIGN.md)
- [Known Issues](../../ISSUES_AND_TODOS.md#bug-029-ephemeral-database-storage-in-cloud-run)

