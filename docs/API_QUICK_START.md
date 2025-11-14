# API Quick Start Guide

**For non-technical users** - Extract metadata from MSA contracts in 3 simple steps.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Upload Your Contract

Upload a PDF or DOCX file to start extraction:

```bash
POST /api/v1/extract/upload
```

**What you need:**
- Your contract file (PDF or DOCX)
- API key (if authentication is enabled)

**Example using curl:**
```bash
curl -X POST "https://your-api-url.com/api/v1/extract/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@contract.pdf"
```

**What you get back:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "pending",
  "file_name": "contract.pdf",
  "status_url": "/api/v1/extract/status/abc123-def456-ghi789",
  "result_url": "/api/v1/extract/result/abc123-def456-ghi789"
}
```

**Save the `job_id`** - you'll need it for the next steps!

---

### Step 2: Check Status

Check if extraction is complete:

```bash
GET /api/v1/extract/status/{job_id}
```

**Example:**
```bash
curl -X GET "https://your-api-url.com/api/v1/extract/status/abc123-def456-ghi789" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "processing",  // or "completed", "failed"
  "file_name": "contract.pdf",
  "created_at": "2025-11-14 10:00:00"
}
```

**Status values:**
- `pending` - Waiting to start
- `processing` - Extraction in progress (usually 30-60 seconds)
- `completed` - Ready! Get your results
- `failed` - Something went wrong (check error_message)

**💡 Tip:** Poll every 5-10 seconds until status is `completed` or `failed`.

---

### Step 3: Get Your Results

Once status is `completed`, get the extracted metadata:

```bash
GET /api/v1/extract/result/{job_id}
```

**Example:**
```bash
curl -X GET "https://your-api-url.com/api/v1/extract/result/abc123-def456-ghi789" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "completed",
  "file_name": "contract.pdf",
  "metadata": {
    "Contract Lifecycle": {
      "Party A": "Adaequare Inc.",
      "Party B": "Orbit Inc.",
      "Execution Date": "2024-09-23",
      "Effective Date": "2024-09-23",
      "Expiration / Termination Date": "2027-09-22",
      "Authorized Signatory - Party A": "John Doe, President",
      "Authorized Signatory - Party B": "Jane Smith, CEO"
    },
    "Commercial Operations": {
      "Billing Frequency": "Monthly",
      "Payment Terms": "Net 30 days",
      "Expense Reimbursement Rules": "Pre-approved expenses only"
    },
    "Risk & Compliance": {
      "Indemnification Clause Reference": "Section 12 - Indemnification",
      "Limitation of Liability Cap": "$1,000,000",
      "Insurance Requirements": "CGL $2M per occurrence",
      "Warranties / Disclaimers": "Services performed in professional manner"
    }
  }
}
```

**That's it!** You now have structured metadata from your contract.

---

## 🎯 Default Mode: Hybrid + Multimodal

**This is what the API uses by default** - no configuration needed!

### What it does:
1. **Extracts text** directly from text pages (fast and accurate)
2. **Converts image pages** (like signature pages) to images
3. **Sends everything together** to the AI in one call

### Why it's the default:
- ✅ Works great for mixed PDFs (text + scanned pages)
- ✅ Captures signatures and visual elements
- ✅ Preserves context between text and images
- ✅ Best accuracy for most contracts

### When to use it:
- Most MSA contracts (text pages + signature pages)
- Mixed PDFs with both text and scanned content
- When you need signature information extracted

---

## 🔧 Other Options (Advanced)

If the default doesn't work for your specific case, you can override settings:

### Upload with Custom Settings

Add parameters to your upload request:

```bash
curl -X POST "https://your-api-url.com/api/v1/extract/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@contract.pdf" \
  -F "extraction_method=text_direct" \
  -F "llm_processing_mode=text_llm"
```

### Extraction Methods

| Method | Best For | What It Does |
|--------|----------|--------------|
| `hybrid` (default) | Mixed PDFs | Extract text + convert images |
| `text_direct` | Text-only PDFs | Extract text only, skip images |
| `ocr_all` | Fully scanned PDFs | OCR all pages |
| `ocr_images_only` | Mixed PDFs | Extract text + OCR image pages |
| `vision_all` | Complex layouts | Convert all to images |

### LLM Processing Modes

| Mode | Best For | What It Does |
|------|----------|--------------|
| `multimodal` (default) | Most contracts | Send text + images together |
| `text_llm` | Cost-effective | Text-only processing |
| `vision_llm` | Complex layouts | Vision-only processing |
| `dual_llm` | Maximum accuracy | Text + vision separately, then merge |

**💡 Recommendation:** Start with defaults (`hybrid` + `multimodal`). Only change if you have a specific need.

---

## 📋 Complete Workflow Example

Here's a complete example using Python:

```python
import requests
import time

# Your API details
API_URL = "https://your-api-url.com"
API_KEY = "your-api-key"
FILE_PATH = "contract.pdf"

# Step 1: Upload
with open(FILE_PATH, 'rb') as f:
    response = requests.post(
        f"{API_URL}/api/v1/extract/upload",
        headers={"X-API-Key": API_KEY},
        files={"file": f}
    )
    upload_data = response.json()
    job_id = upload_data["job_id"]
    print(f"Uploaded! Job ID: {job_id}")

# Step 2: Wait for completion
while True:
    status_response = requests.get(
        f"{API_URL}/api/v1/extract/status/{job_id}",
        headers={"X-API-Key": API_KEY}
    )
    status_data = status_response.json()
    
    if status_data["status"] == "completed":
        print("Extraction complete!")
        break
    elif status_data["status"] == "failed":
        print(f"Failed: {status_data.get('error_message')}")
        break
    else:
        print(f"Status: {status_data['status']}... waiting")
        time.sleep(5)

# Step 3: Get results
if status_data["status"] == "completed":
    result_response = requests.get(
        f"{API_URL}/api/v1/extract/result/{job_id}",
        headers={"X-API-Key": API_KEY}
    )
    result_data = result_response.json()
    print("Metadata:", result_data["metadata"])
```

---

## ❓ Common Questions

**Q: How long does extraction take?**  
A: Usually 30-60 seconds for a typical MSA contract.

**Q: What file formats are supported?**  
A: PDF and DOCX files.

**Q: What's the maximum file size?**  
A: Default is 50MB. Contact your administrator for larger files.

**Q: Can I process multiple files at once?**  
A: Yes! Upload multiple files to get multiple job IDs, then check each one separately.

**Q: What if extraction fails?**  
A: Check the `error_message` in the status response. Common issues: corrupted files, unsupported format, or API key problems.

**Q: Do I need to keep polling?**  
A: Yes, the API is asynchronous. Upload returns immediately, then poll status until complete.

---

## 🔗 Additional Resources

- **Interactive API Docs:** Visit `/docs` on your API server for a Swagger UI
- **Health Check:** `GET /api/v1/health` to verify the API is running
- **List Jobs:** `GET /api/v1/extract/jobs` to see all your extraction jobs

---

**Need help?** Contact your API administrator or check the full documentation.

