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

### Option 1: Using Google Cloud Console (No CLI Required)

#### Step 1: Enable Required APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services > Library**
4. Enable these APIs:
   - Cloud Build API
   - Cloud Run API
   - Artifact Registry API (or Container Registry API)

#### Step 2: Build Container Using Cloud Build

1. Go to **Cloud Build > Triggers** in Cloud Console
2. Click **Create Trigger**
3. Connect your repository (GitHub, Cloud Source Repositories, etc.)
4. Or use **Cloud Build > History > Run** to build from local files:
   - Click **Run** button
   - Select **Build from Dockerfile**
   - Upload your project files (or connect to source)
   - Set build configuration:
     - **Cloud Build configuration file:** Leave empty (uses Dockerfile)
     - **Dockerfile location:** `Dockerfile`
     - **Image name:** `gcr.io/YOUR-PROJECT-ID/msa-extractor-api` (replace YOUR-PROJECT-ID)
   - Click **Run**

#### Step 3: Deploy to Cloud Run

1. Go to **Cloud Run** in Cloud Console
2. Click **Create Service**
3. Configure:
   - **Service name:** `msa-extractor-api`
   - **Region:** Choose your region (e.g., `us-central1`)
   - **Deploy one revision from an existing container image**
   - **Container image URL:** Click **Select** and choose the image you built
   - **Container port:** `8080` (Cloud Run sets PORT automatically)
   - **Authentication:** Allow unauthenticated invocations (for now)
4. **Container** tab:
   - **Memory:** 2 GiB
   - **CPU:** 2
   - **Timeout:** 3600 seconds
   - **Max instances:** 10
5. **Variables & Secrets** tab:
   - Add environment variables:
     - `GEMINI_API_KEY` = `your-gemini-api-key`
     - `API_ENABLE_AUTH` = `false`
6. Click **Create**

#### Step 4: Get Service URL

After deployment, the service URL will be displayed in the Cloud Run service details page.

---

### Option 2: Build Locally and Push (If Docker is Installed)

If you have Docker installed locally, you can build and push the image:

#### Step 1: Authenticate Docker with GCP

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Go to **IAM & Admin > Service Accounts**
3. Create a service account with **Storage Admin** role (for pushing to Container Registry)
4. Create a JSON key and download it
5. In PowerShell (or terminal):
```powershell
# Set environment variable (replace with your key file path)
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\key.json"

# Authenticate Docker (if using Container Registry)
docker login -u oauth2accesstoken -p (gcloud auth print-access-token) gcr.io
```

**Note:** If you don't have `gcloud` CLI, you can use the service account JSON key directly with Docker.

#### Step 2: Build and Tag Image

```powershell
# Set your project ID
$PROJECT_ID = "your-project-id"

# Build the image
docker build -t gcr.io/$PROJECT_ID/msa-extractor-api .

# Tag for Container Registry
docker tag gcr.io/$PROJECT_ID/msa-extractor-api gcr.io/$PROJECT_ID/msa-extractor-api:latest
```

#### Step 3: Push to Container Registry

```powershell
# Push the image
docker push gcr.io/$PROJECT_ID/msa-extractor-api:latest
```

#### Step 4: Deploy via Cloud Console

Follow **Option 1, Step 3** above to deploy the pushed image to Cloud Run.

---

### Option 3: Using gcloud CLI (If Available)

```bash
# Set your project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Build container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/msa-extractor-api

# Deploy to Cloud Run
# ⚠️ For production, use Secret Manager instead (see ENV_VARIABLES.md)
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
  --set-env-vars API_ENABLE_AUTH=false

# Get the service URL
gcloud run services describe msa-extractor-api \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

**Note:** Cloud Run automatically sets `PORT=8080`. The app reads `PORT` environment variable.

---

## Configuration

### Environment Variables Management

⚠️ **Important:** For production, use **Google Secret Manager** for sensitive values (API keys). See [Environment Variables Guide](ENV_VARIABLES.md) for best practices.

**Quick Start (Development):**
```bash
# ⚠️ For development only - use Secret Manager for production
gcloud run deploy msa-extractor-api \
  --image gcr.io/$PROJECT_ID/msa-extractor-api \
  --set-env-vars GEMINI_API_KEY=your-key \
  --set-env-vars API_ENABLE_AUTH=false
```

**Production (Recommended):**
```bash
# 1. Create secrets first (see ENV_VARIABLES.md)
# 2. Deploy with secret references
gcloud run deploy msa-extractor-api \
  --image gcr.io/$PROJECT_ID/msa-extractor-api \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-env-vars API_ENABLE_AUTH=false
```

### Required Configuration

| Variable | Description | Method | Example |
|----------|-------------|--------|---------|
| `GEMINI_API_KEY` | Gemini API key (required) | **Secret Manager** ✅ | `AIza...` |
| `PORT` | Server port | Auto-set by Cloud Run | `8080` |

### Optional Configuration

| Variable | Description | Default | Method |
|----------|-------------|---------|--------|
| `API_ENABLE_AUTH` | Enable API key authentication | `false` | Env Var |
| `API_KEY` | API key(s) for authentication | `` | **Secret Manager** ✅ |
| `MAX_UPLOAD_SIZE_MB` | Maximum file upload size | `25` | Env Var |
| `EXTRACTION_METHOD` | Default extraction method | `hybrid` | Env Var |
| `LLM_PROCESSING_MODE` | Default LLM processing mode | `text_llm` | Env Var |
| `OCR_ENGINE` | Default OCR engine | `tesseract` | Env Var |

**📖 See [Environment Variables Guide](ENV_VARIABLES.md) for:**
- Setting up Secret Manager
- Managing secrets securely
- Updating configuration
- Best practices

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

