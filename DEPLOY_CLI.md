# Quick Deployment Guide - Using gcloud CLI

**Step-by-step instructions for deploying via gcloud CLI**

---

## Prerequisites

1. **Google Cloud SDK (gcloud)** installed
   - Download from: https://cloud.google.com/sdk/docs/install
   - Or install via PowerShell: `(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe"); & $env:Temp\GoogleCloudSDKInstaller.exe`

2. **GCP Account** with billing enabled
3. **GEMINI_API_KEY** - Required for extraction

---

## Step 1: Authenticate and Set Project

Open a **new PowerShell window** (separate from Cursor):

```powershell
# Authenticate with Google Cloud
gcloud auth login

# List your projects to find your project ID
gcloud projects list

# Set your project (replace YOUR-PROJECT-ID with your actual project ID)
gcloud config set project YOUR-PROJECT-ID

# Verify project is set
gcloud config get-value project
```

**Example:**
```powershell
gcloud config set project my-msa-extractor-project
```

---

## Step 2: Enable Required APIs

```powershell
# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Artifact Registry API (or Container Registry)
gcloud services enable artifactregistry.googleapis.com
```

**Wait for APIs to enable** (takes 1-2 minutes)

---

## Step 3: Navigate to Project Directory

```powershell
# Change to your project directory
cd D:\dev\projects\msa_extractor
```

---

## Step 4: Build Container Image

```powershell
# Set your project ID as a variable (replace with your actual project ID)
$PROJECT_ID = "YOUR-PROJECT-ID"

# Build and push container image to Google Container Registry
gcloud builds submit --tag gcr.io/$PROJECT_ID/msa-extractor-api
```

**This will:**
- Upload your project files to Cloud Build
- Build the Docker image using your `Dockerfile`
- Push the image to Google Container Registry
- Take 5-10 minutes

**Note:** The `.gcloudignore` file will automatically exclude unnecessary files (venv, __pycache__, etc.)

---

## Step 5: Deploy to Cloud Run

### Option A: Quick Start (Development Only)

⚠️ **For production, use Secret Manager instead (see Option B or [ENV_VARIABLES.md](docs/setup/ENV_VARIABLES.md))**

```powershell
# Deploy to Cloud Run (replace YOUR-PROJECT-ID and your-gemini-api-key)
gcloud run deploy msa-extractor-api `
  --image gcr.io/YOUR-PROJECT-ID/msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --set-env-vars GEMINI_API_KEY=your-actual-gemini-api-key `
  --set-env-vars API_ENABLE_AUTH=false
```

### Option B: Production (Using Secret Manager) ✅ Recommended

```powershell
# 1. Create secrets (one-time setup)
$PROJECT_ID = "YOUR-PROJECT-ID"
echo -n "YOUR-GEMINI-API-KEY" | gcloud secrets create gemini-api-key --data-file=- --replication-policy="automatic" --project=$PROJECT_ID

# 2. Grant Cloud Run access to secrets
$SERVICE_ACCOUNT = "$PROJECT_ID-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding gemini-api-key `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/secretmanager.secretAccessor" `
  --project=$PROJECT_ID

# 3. Deploy with secret references
gcloud run deploy msa-extractor-api `
  --image gcr.io/$PROJECT_ID/msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest `
  --set-env-vars API_ENABLE_AUTH=false
```

**Important Notes:**
- Replace `YOUR-PROJECT-ID` with your actual project ID
- Replace `YOUR-GEMINI-API-KEY` with your real Gemini API key
- The backticks (`) in PowerShell allow line continuation
- Cloud Run automatically sets `PORT=8080` - the app reads this automatically
- **📖 See [Environment Variables Guide](docs/setup/ENV_VARIABLES.md) for detailed instructions**

---

## Step 6: Get Your Service URL

After deployment completes, you'll see the service URL in the output. Or get it with:

```powershell
# Get the service URL
gcloud run services describe msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --format 'value(status.url)'
```

**Example output:**
```
https://msa-extractor-api-xxxxx-uc.a.run.app
```

---

## Step 7: Test Your Deployment

### Health Check

```powershell
# Replace with your actual service URL
$SERVICE_URL = "https://msa-extractor-api-xxxxx-uc.a.run.app"

# Test health endpoint
curl "$SERVICE_URL/api/v1/health"
```

### API Documentation

Open in browser:
```
https://your-service-url/docs
```

### Test Upload

```powershell
# Upload a test file
curl -X POST "$SERVICE_URL/api/v1/extract/upload" `
  -F "file=@test.pdf" `
  -F "extraction_method=hybrid" `
  -F "llm_processing_mode=text_llm"
```

---

## Complete Example (All Steps)

```powershell
# Step 1: Authenticate and set project
gcloud auth login
gcloud config set project my-msa-extractor-project

# Step 2: Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Step 3: Navigate to project
cd D:\dev\projects\msa_extractor

# Step 4: Build container
$PROJECT_ID = "my-msa-extractor-project"
gcloud builds submit --tag gcr.io/$PROJECT_ID/msa-extractor-api

# Step 5: Deploy to Cloud Run
gcloud run deploy msa-extractor-api `
  --image gcr.io/$PROJECT_ID/msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --set-env-vars GEMINI_API_KEY=AIzaSy...your-key-here,API_ENABLE_AUTH=false

# Step 6: Get service URL
gcloud run services describe msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --format 'value(status.url)'
```

---

## Updating Deployment

To update your deployment after code changes:

```powershell
# Rebuild and redeploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/msa-extractor-api
gcloud run deploy msa-extractor-api `
  --image gcr.io/$PROJECT_ID/msa-extractor-api `
  --platform managed `
  --region us-central1
```

---

## Viewing Logs

```powershell
# Stream logs
gcloud run services logs tail msa-extractor-api `
  --platform managed `
  --region us-central1

# View recent logs
gcloud run services logs read msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --limit 50
```

---

## Troubleshooting

### "Project not found" error
- Verify project ID: `gcloud projects list`
- Set project: `gcloud config set project YOUR-PROJECT-ID`

### "API not enabled" error
- Enable APIs: `gcloud services enable cloudbuild.googleapis.com run.googleapis.com`

### Build fails
- Check build logs: `gcloud builds list` then `gcloud builds log BUILD-ID`
- Verify `Dockerfile` exists in project root
- Check `.gcloudignore` isn't excluding necessary files

### Container won't start
- Check logs: `gcloud run services logs read msa-extractor-api --region us-central1`
- Verify `GEMINI_API_KEY` environment variable is set
- Check memory/CPU settings (minimum 2Gi memory recommended)

### Port issues
- Cloud Run sets `PORT=8080` automatically
- The app reads `PORT` environment variable (configured in `config.py`)
- No need to set `API_PORT` manually

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | ✅ Yes | Gemini API key | `AIzaSy...` |
| `API_ENABLE_AUTH` | No | Enable API key auth | `false` |
| `API_KEY` | No | API key(s) for auth | `key1,key2` |
| `EXTRACTION_METHOD` | No | Default extraction method | `hybrid` |
| `LLM_PROCESSING_MODE` | No | Default LLM mode | `text_llm` |
| `OCR_ENGINE` | No | Default OCR engine | `tesseract` |
| `MAX_UPLOAD_SIZE_MB` | No | Max upload size | `25` |

---

## Next Steps

1. ✅ Test all endpoints
2. ✅ Monitor logs
3. ✅ Set up authentication (set `API_ENABLE_AUTH=true` and `API_KEY`)
4. ✅ Configure alerts in Cloud Console

---

For detailed documentation, see [GCP_DEPLOYMENT.md](docs/setup/GCP_DEPLOYMENT.md)

