# Environment Variables Management for Cloud Run

**Best practices for managing configuration and secrets in Google Cloud Run**

---

## Overview

There are three ways to manage environment variables in Cloud Run:

1. **Google Secret Manager** (✅ **Recommended for secrets**)
   - Secure storage for sensitive values (API keys, passwords)
   - Version control and audit logging
   - Automatic rotation support

2. **Environment Variables** (✅ **For non-sensitive config**)
   - Simple key-value pairs
   - Set via Cloud Console or CLI
   - Good for non-sensitive configuration

3. **Cloud Console UI** (✅ **Easier for updates**)
   - Visual interface
   - No command line needed
   - Good for quick updates

---

## Method 1: Google Secret Manager (Recommended for Secrets)

### Step 1: Create Secrets

```powershell
# Set your project ID
$PROJECT_ID = "msa-extractor2234223"

# Create Gemini API key secret
echo -n "YOUR-GEMINI-API-KEY" | gcloud secrets create gemini-api-key `
  --data-file=- `
  --replication-policy="automatic" `
  --project=$PROJECT_ID

# Create API key secret (if using authentication)
echo -n "your-strong-random-api-key" | gcloud secrets create msa-api-key `
  --data-file=- `
  --replication-policy="automatic" `
  --project=$PROJECT_ID
```

**Alternative (PowerShell-friendly):**
```powershell
# Create secret from file
"YOUR-GEMINI-API-KEY" | Out-File -FilePath gemini-key.txt -NoNewline
gcloud secrets create gemini-api-key --data-file=gemini-key.txt --replication-policy="automatic"
Remove-Item gemini-key.txt

# Or use stdin
"YOUR-GEMINI-API-KEY" | gcloud secrets create gemini-api-key --data-file=- --replication-policy="automatic"
```

### Step 2: Grant Cloud Run Access to Secrets

```powershell
# Get your Cloud Run service account email
$SERVICE_ACCOUNT = "$PROJECT_ID-compute@developer.gserviceaccount.com"

# Grant access to secrets
gcloud secrets add-iam-policy-binding gemini-api-key `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/secretmanager.secretAccessor" `
  --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding msa-api-key `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/secretmanager.secretAccessor" `
  --project=$PROJECT_ID
```

### Step 3: Deploy with Secret References

```powershell
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

**With API authentication enabled:**
```powershell
gcloud run deploy msa-extractor-api `
  --image gcr.io/$PROJECT_ID/msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest,API_KEY=msa-api-key:latest `
  --set-env-vars API_ENABLE_AUTH=true
```

### Step 4: Update Secrets (When Needed)

```powershell
# Update secret value
echo -n "NEW-GEMINI-API-KEY" | gcloud secrets versions add gemini-api-key --data-file=-

# Cloud Run will automatically use the latest version
# Or specify version: --set-secrets GEMINI_API_KEY=gemini-api-key:2
```

---

## Method 2: Environment Variables (For Non-Sensitive Config)

### During Deployment

```powershell
gcloud run deploy msa-extractor-api `
  --image gcr.io/$PROJECT_ID/msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --set-env-vars API_ENABLE_AUTH=false,MAX_UPLOAD_SIZE_MB=50,EXTRACTION_METHOD=hybrid,LLM_PROCESSING_MODE=text_llm
```

### After Deployment (Update)

```powershell
# Update environment variables
gcloud run services update msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --update-env-vars MAX_UPLOAD_SIZE_MB=50,EXTRACTION_METHOD=hybrid
```

### Remove Environment Variables

```powershell
gcloud run services update msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --remove-env-vars EXTRACTION_METHOD
```

---

## Method 3: Cloud Console UI (Easiest)

### Steps

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on your service: `msa-extractor-api`
3. Click **"EDIT & DEPLOY NEW REVISION"**
4. Scroll to **"Variables & Secrets"**
5. Add environment variables or secret references
6. Click **"DEPLOY"**

### Adding Secrets via UI

1. In **"Variables & Secrets"** section
2. Click **"ADD VARIABLE"** → Select **"Reference a secret"**
3. Choose secret name (e.g., `gemini-api-key`)
4. Set environment variable name (e.g., `GEMINI_API_KEY`)
5. Select version (usually `latest`)

---

## Recommended Setup

### For Production

**Use Secret Manager for:**
- ✅ `GEMINI_API_KEY` (sensitive)
- ✅ `API_KEY` (sensitive, if using API authentication)

**Use Environment Variables for:**
- ✅ `API_ENABLE_AUTH` (non-sensitive boolean)
- ✅ `MAX_UPLOAD_SIZE_MB` (non-sensitive config)
- ✅ `EXTRACTION_METHOD` (non-sensitive config)
- ✅ `LLM_PROCESSING_MODE` (non-sensitive config)
- ✅ `OCR_ENGINE` (non-sensitive config)

### Example: Production Deployment

```powershell
# 1. Create secrets (one-time setup)
echo -n "YOUR-GEMINI-API-KEY" | gcloud secrets create gemini-api-key --data-file=- --replication-policy="automatic"
echo -n "your-strong-api-key" | gcloud secrets create msa-api-key --data-file=- --replication-policy="automatic"

# 2. Grant access
$PROJECT_ID = "msa-extractor2234223"
$SERVICE_ACCOUNT = "$PROJECT_ID-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding gemini-api-key --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding msa-api-key --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor"

# 3. Deploy with secrets and config
gcloud run deploy msa-extractor-api `
  --image gcr.io/$PROJECT_ID/msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest,API_KEY=msa-api-key:latest `
  --set-env-vars API_ENABLE_AUTH=true,MAX_UPLOAD_SIZE_MB=50,EXTRACTION_METHOD=hybrid,LLM_PROCESSING_MODE=text_llm
```

---

## Quick Reference

### List All Secrets

```powershell
gcloud secrets list
```

### View Secret (Metadata Only)

```powershell
gcloud secrets describe gemini-api-key
```

### View Secret Value (Requires Permissions)

```powershell
gcloud secrets versions access latest --secret="gemini-api-key"
```

### List Environment Variables

```powershell
gcloud run services describe msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --format="value(spec.template.spec.containers[0].env)"
```

### View Service Configuration

```powershell
gcloud run services describe msa-extractor-api `
  --platform managed `
  --region us-central1
```

---

## Security Best Practices

1. ✅ **Never commit secrets to Git**
   - Use Secret Manager for all sensitive values
   - Add `.env` to `.gitignore`

2. ✅ **Use Secret Manager for API Keys**
   - `GEMINI_API_KEY` → Secret Manager
   - `API_KEY` → Secret Manager

3. ✅ **Rotate secrets regularly**
   - Update secret versions in Secret Manager
   - Cloud Run automatically uses latest version

4. ✅ **Limit secret access**
   - Only grant access to necessary service accounts
   - Use IAM roles (`roles/secretmanager.secretAccessor`)

5. ✅ **Monitor secret access**
   - Enable Cloud Audit Logs
   - Review secret access in Cloud Console

6. ✅ **Use environment variables for non-sensitive config**
   - Safe to view in Cloud Console
   - Easy to update without redeploying

---

## Troubleshooting

### "Permission denied" when accessing secrets

```powershell
# Grant access to Cloud Run service account
$PROJECT_ID = "msa-extractor2234223"
$SERVICE_ACCOUNT = "$PROJECT_ID-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding SECRET_NAME `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/secretmanager.secretAccessor"
```

### Secret not found

```powershell
# List all secrets
gcloud secrets list

# Verify secret exists
gcloud secrets describe SECRET_NAME
```

### Environment variable not updating

```powershell
# Force new revision
gcloud run services update SERVICE_NAME `
  --update-env-vars KEY=value `
  --region REGION
```

---

## Migration: From Command Line to Secret Manager

If you've already deployed with `--set-env-vars GEMINI_API_KEY=...`, migrate to Secret Manager:

```powershell
# 1. Create secret from existing value
# (Get value from Cloud Console or previous deployment)
echo -n "YOUR-EXISTING-KEY" | gcloud secrets create gemini-api-key --data-file=- --replication-policy="automatic"

# 2. Grant access
$PROJECT_ID = "msa-extractor2234223"
$SERVICE_ACCOUNT = "$PROJECT_ID-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding gemini-api-key --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor"

# 3. Update service to use secret instead of env var
gcloud run services update msa-extractor-api `
  --platform managed `
  --region us-central1 `
  --remove-env-vars GEMINI_API_KEY `
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest
```

---

## See Also

- [GCP Deployment Guide](GCP_DEPLOYMENT.md) - Full deployment instructions
- [Configuration Reference](../setup/configuration.md) - All configuration options
- [Google Secret Manager Docs](https://cloud.google.com/secret-manager/docs)

