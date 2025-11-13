# Quick Deployment Guide - Cloud Console Method

**For users without gcloud CLI access**

---

## Step-by-Step: Deploy via Google Cloud Console

### Prerequisites
- Google Cloud account with billing enabled
- Project created in Google Cloud Console
- Docker installed locally (optional, for local build)

---

## Method 1: Cloud Build from Console (Recommended)

### Step 1: Enable APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services > Library**
4. Search and enable:
   - **Cloud Build API**
   - **Cloud Run API**
   - **Artifact Registry API** (or **Container Registry API**)

### Step 2: Build Container Image

1. Go to **Cloud Build > History**
2. Click **Run** button (top right)
3. Select **Build from Dockerfile**
4. **Source:**
   - Option A: Connect to GitHub/GitLab repository
   - Option B: Upload files (zip your project, excluding `venv/`, `__pycache__/`, etc.)
5. **Configuration:**
   - **Cloud Build configuration file:** Leave empty
   - **Dockerfile location:** `Dockerfile`
   - **Image name:** `gcr.io/YOUR-PROJECT-ID/msa-extractor-api`
     - Replace `YOUR-PROJECT-ID` with your actual project ID
6. Click **Run**

**Wait for build to complete** (5-10 minutes)

### Step 3: Deploy to Cloud Run

1. Go to **Cloud Run** in Cloud Console
2. Click **Create Service**
3. **Basics:**
   - **Service name:** `msa-extractor-api`
   - **Region:** Choose (e.g., `us-central1`)
   - **Deploy one revision from an existing container image**
   - **Container image URL:** Click **Select** → Choose your built image
   - **Container port:** `8080`
   - **Authentication:** ✅ Allow unauthenticated invocations
4. **Container:**
   - **Memory:** 2 GiB
   - **CPU:** 2
   - **Timeout:** 3600 seconds
   - **Max instances:** 10
   - **Min instances:** 0
5. **Variables & Secrets:**
   - Click **Add Variable**
   - Add:
     - Name: `GEMINI_API_KEY`, Value: `your-actual-gemini-api-key`
     - Name: `API_ENABLE_AUTH`, Value: `false`
6. Click **Create**

### Step 4: Get Your Service URL

After deployment completes, the service URL will be shown at the top of the service details page.

**Example:** `https://msa-extractor-api-xxxxx-uc.a.run.app`

---

## Method 2: Build Locally and Push (If Docker Installed)

### Step 1: Prepare Dockerfile

Make sure your `Dockerfile` is in the project root.

### Step 2: Build Image Locally

```powershell
# Build the Docker image
docker build -t msa-extractor-api .
```

### Step 3: Tag for Google Container Registry

```powershell
# Replace YOUR-PROJECT-ID with your actual project ID
$PROJECT_ID = "YOUR-PROJECT-ID"
docker tag msa-extractor-api gcr.io/$PROJECT_ID/msa-extractor-api:latest
```

### Step 4: Authenticate and Push

**Option A: Using Service Account (Recommended)**

1. Go to **IAM & Admin > Service Accounts** in Cloud Console
2. Create service account with **Storage Admin** role
3. Create JSON key and download
4. In PowerShell:
```powershell
# Set credentials
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\key.json"

# Install gcloud CLI or use Docker with service account
# If you have gcloud:
gcloud auth activate-service-account --key-file=$env:GOOGLE_APPLICATION_CREDENTIALS
gcloud auth configure-docker

# Push image
docker push gcr.io/$PROJECT_ID/msa-extractor-api:latest
```

**Option B: Using Cloud Console Upload**

1. Build image locally: `docker build -t msa-extractor-api .`
2. Save as tar: `docker save msa-extractor-api > msa-extractor-api.tar`
3. Go to **Artifact Registry** or **Container Registry** in Cloud Console
4. Upload the tar file (if supported) or use Cloud Build instead

### Step 5: Deploy to Cloud Run

Follow **Method 1, Step 3** above to deploy the pushed image.

---

## Testing Your Deployment

### 1. Health Check

Open in browser or use curl:
```
https://your-service-url/api/v1/health
```

Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "storage_type": "local"
}
```

### 2. API Documentation

Open in browser:
```
https://your-service-url/docs
```

### 3. Test Upload

Use the interactive docs at `/docs` or:

```powershell
# Replace with your actual service URL
$URL = "https://your-service-url/api/v1/extract/upload"

# Upload a test file
curl -X POST $URL `
  -F "file=@test.pdf" `
  -F "extraction_method=hybrid" `
  -F "llm_processing_mode=text_llm"
```

---

## Troubleshooting

### Build Fails

- Check that `Dockerfile` is in project root
- Verify all dependencies in `requirements.txt`
- Check build logs in Cloud Build > History

### Container Won't Start

- Check Cloud Run logs: **Cloud Run > msa-extractor-api > Logs**
- Verify environment variables are set correctly
- Ensure `GEMINI_API_KEY` is set

### Port Issues

- Cloud Run automatically sets `PORT=8080`
- The app reads `PORT` environment variable
- No need to set `API_PORT` manually

### Database Issues

- SQLite uses ephemeral storage (data lost on restart)
- This is expected for Iteration 1
- For persistent storage, use Cloud SQL (future iteration)

---

## Next Steps

1. ✅ Test all endpoints
2. ✅ Monitor logs in Cloud Console
3. ✅ Set up authentication (set `API_ENABLE_AUTH=true` and `API_KEY`)
4. ✅ Configure alerts for errors

---

## Files to Exclude When Uploading

If uploading files to Cloud Build, exclude:
- `venv/` or `env/`
- `__pycache__/`
- `*.pyc`
- `.env` (use environment variables in Cloud Run instead)
- `storage/*.db` (database files)
- `uploads/`, `results/`, `logs/` (local directories)
- `.git/`

See `.gcloudignore` file for complete list.

---

For detailed documentation, see [GCP_DEPLOYMENT.md](docs/setup/GCP_DEPLOYMENT.md)

