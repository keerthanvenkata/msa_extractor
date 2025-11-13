# GCP Cloud Run Deployment Guide

**Last Updated:** November 13, 2025  
**Status:** Ready for Deployment

This guide covers deploying the MSA Metadata Extractor API to Google Cloud Platform (GCP) Cloud Run.

---

## Prerequisites

1. **GCP Account** with billing enabled
2. **Google Cloud SDK** (`gcloud`) installed and configured
3. **Docker** installed (for local testing)
4. **GEMINI_API_KEY** - Required for extraction functionality

---

## Quick Start

### 1. Set Up GCP Project

```bash
# Set your project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 2. Build and Deploy

```bash
# Build container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/msa-extractor-api

# Deploy to Cloud Run
gcloud run deploy msa-extractor-api \
  --image gcr.io/$PROJECT_ID/msa-extractor-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10 \
  --set-env-vars GEMINI_API_KEY=your-gemini-api-key \
  --set-env-vars API_ENABLE_AUTH=false \
  --set-env-vars API_PORT=8080
```

**Note:** Cloud Run automatically sets `PORT=8080`. The app reads `PORT` environment variable.

### 3. Get Service URL

```bash
# Get the service URL
gcloud run services describe msa-extractor-api \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

---

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Gemini API key (required) | `AIza...` |
| `PORT` | Server port (Cloud Run sets automatically) | `8080` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_ENABLE_AUTH` | Enable API key authentication | `false` |
| `API_KEY` | API key(s) for authentication | `` |
| `MAX_UPLOAD_SIZE_MB` | Maximum file upload size | `25` |
| `EXTRACTION_METHOD` | Default extraction method | `hybrid` |
| `LLM_PROCESSING_MODE` | Default LLM processing mode | `text_llm` |
| `OCR_ENGINE` | Default OCR engine | `tesseract` |

### Setting Environment Variables

**During Deployment:**
```bash
gcloud run deploy msa-extractor-api \
  --image gcr.io/$PROJECT_ID/msa-extractor-api \
  --set-env-vars GEMINI_API_KEY=your-key \
  --set-env-vars API_ENABLE_AUTH=true \
  --set-env-vars API_KEY=your-api-key
```

**After Deployment:**
```bash
gcloud run services update msa-extractor-api \
  --update-env-vars API_ENABLE_AUTH=true \
  --update-env-vars API_KEY=your-api-key
```

---

## Resource Configuration

### Recommended Settings

- **Memory:** 2Gi (minimum for OCR processing)
- **CPU:** 2 (for faster extraction)
- **Timeout:** 3600 seconds (60 minutes) for large documents
- **Max Instances:** 10 (adjust based on traffic)
- **Min Instances:** 0 (scale to zero when idle)

### Example Deployment with Resources

```bash
gcloud run deploy msa-extractor-api \
  --image gcr.io/$PROJECT_ID/msa-extractor-api \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 5
```

---

## Storage Considerations

### Current Implementation (Iteration 1)

- **SQLite Database:** Stored in Cloud Run ephemeral storage (`/app/storage/`)
  - Data persists during container lifetime
  - Lost when container stops (ephemeral)
  - Suitable for development/testing

- **PDF Files:** Stored in Cloud Run ephemeral storage (`/app/uploads/`)
  - Temporary storage during extraction
  - Cleared after processing (or on container restart)
  - 10GB ephemeral storage limit per instance

### Limitations

⚠️ **Important:** Ephemeral storage is not persistent. Data is lost when:
- Container stops (scales to zero)
- Container restarts
- Service is updated/redeployed

### Future Iterations

- **Cloud SQL:** Persistent database (PostgreSQL)
- **Cloud Storage:** Persistent PDF storage (GCS bucket)
- See [IMPLEMENTATION_ROADMAP.md](../planning/IMPLEMENTATION_ROADMAP.md) for details

---

## Authentication

### Option 1: Public Access (Development)

```bash
gcloud run deploy msa-extractor-api \
  --allow-unauthenticated
```

### Option 2: API Key Authentication

1. Enable authentication in environment variables:
```bash
gcloud run services update msa-extractor-api \
  --update-env-vars API_ENABLE_AUTH=true \
  --update-env-vars API_KEY=your-strong-random-key
```

2. Use API key in requests:
```bash
curl -H "X-API-Key: your-strong-random-key" \
  https://your-service-url/api/v1/extract/upload \
  -F "file=@contract.pdf"
```

### Option 3: Cloud Run IAM (Recommended for Production)

```bash
# Require authentication (Cloud Run IAM)
gcloud run deploy msa-extractor-api \
  --no-allow-unauthenticated

# Get identity token for requests
gcloud auth print-identity-token

# Use in requests
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://your-service-url/api/v1/extract/upload \
  -F "file=@contract.pdf"
```

---

## Testing Deployment

### 1. Health Check

```bash
curl https://your-service-url/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "storage_type": "local",
  "timestamp": "2025-11-13T10:30:00Z"
}
```

### 2. Upload File

```bash
curl -X POST https://your-service-url/api/v1/extract/upload \
  -F "file=@contract.pdf" \
  -F "extraction_method=hybrid" \
  -F "llm_processing_mode=text_llm"
```

### 3. Check Job Status

```bash
curl https://your-service-url/api/v1/extract/status/{job_id}
```

### 4. Get Results

```bash
curl https://your-service-url/api/v1/extract/result/{job_id}
```

---

## Monitoring

### View Logs

```bash
# Stream logs
gcloud run services logs tail msa-extractor-api \
  --platform managed \
  --region us-central1

# View recent logs
gcloud run services logs read msa-extractor-api \
  --platform managed \
  --region us-central1 \
  --limit 50
```

### Metrics

- View metrics in Cloud Console: **Cloud Run > msa-extractor-api > Metrics**
- Key metrics:
  - Request count
  - Request latency
  - Error rate
  - Memory usage
  - CPU usage

---

## Troubleshooting

### Container Fails to Start

1. **Check logs:**
```bash
gcloud run services logs read msa-extractor-api --limit 100
```

2. **Common issues:**
   - Missing `GEMINI_API_KEY` environment variable
   - Port configuration (should use `PORT` env var, not `API_PORT`)
   - Memory too low (increase to 2Gi minimum)

### Extraction Fails

1. **Check job logs via API:**
```bash
curl https://your-service-url/api/v1/extract/{job_id}/logs
```

2. **Common issues:**
   - Invalid file format (only PDF/DOCX supported)
   - File too large (max 25MB default)
   - Timeout (increase timeout for large files)

### Database Issues

- **SQLite locked:** Multiple instances accessing same database
  - **Solution:** Use Cloud SQL in future iteration
  - **Workaround:** Limit concurrency to 1 instance

---

## Cost Optimization

### Development/Testing

- **Min Instances:** 0 (scale to zero)
- **Max Instances:** 1-2
- **Memory:** 1Gi (minimum)
- **CPU:** 1

### Production

- **Min Instances:** 1 (faster cold starts)
- **Max Instances:** 10+ (based on traffic)
- **Memory:** 2Gi (for OCR processing)
- **CPU:** 2 (for faster extraction)

### Cost Estimates

- **Free Tier:** 2 million requests/month, 360,000 GB-seconds
- **Pricing:** ~$0.40 per million requests + compute costs
- **Typical Usage:** $10-50/month for moderate traffic

---

## Next Steps

### Immediate (After Deployment)

1. ✅ Test all endpoints
2. ✅ Monitor logs and metrics
3. ✅ Set up alerts for errors
4. ✅ Configure authentication (if needed)

### Future Iterations

1. **Cloud SQL Integration:**
   - Migrate from SQLite to Cloud SQL PostgreSQL
   - Persistent database storage

2. **Cloud Storage Integration:**
   - Migrate PDF storage to GCS bucket
   - Persistent file storage

3. **Cleanup Service:**
   - Automated PDF cleanup after N days
   - Scheduled Cloud Run jobs

4. **Enhanced Authentication:**
   - JWT/OAuth2 support
   - User management

See [IMPLEMENTATION_ROADMAP.md](../planning/IMPLEMENTATION_ROADMAP.md) for details.

---

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [API Design Specification](../planning/API_DESIGN.md)
- [Implementation Roadmap](../planning/IMPLEMENTATION_ROADMAP.md)

---

**Note:** This deployment uses SQLite + ephemeral storage (Iteration 1). For production with persistent storage, see future iterations for Cloud SQL + GCS integration.

