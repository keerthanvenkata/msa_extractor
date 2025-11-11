# Windows OCR & Dependency Setup

This guide covers installation of native dependencies required for OCR pipelines (Tesseract, OpenCV prerequisites, Google Cloud Vision tooling) on Windows 10/11.

## 1. Python Environment

1. Install Python 3.10.x from [python.org](https://www.python.org/downloads/)
2. During installation, select:
   - “Add Python to PATH”
   - “Install launcher for all users”
3. Verify:
   ```powershell
   python --version
   pip --version
   ```
4. Create/activate your project virtual environment:
   ```powershell
   cd D:\dev\projects\msa_extractor
   python -m venv venv
   venv\Scripts\activate
   ```

## 2. Tesseract OCR

### Option A: Windows Installer (Recommended)

1. Download latest installer from [UB Mannheim builds](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run installer — leave default path (e.g., `C:\Program Files\Tesseract-OCR`)
3. During installation, select English and any additional languages required
4. Add installation path to `PATH` (if installer didn’t do it):
   ```powershell
   setx PATH "%PATH%;C:\Program Files\Tesseract-OCR"
   ```
5. Verify:
   ```powershell
   tesseract --version
   ```

### Option B: Chocolatey

```powershell
choco install -y tesseract
```

## 3. Visual C++ Redistributable

Many imaging libraries depend on Microsoft VC++ runtimes. Install the latest x64 redistributable from [Microsoft](https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist).

## 4. Install Python Packages

Activate your virtual environment and install Python dependencies (after updating `requirements.txt`):

```powershell
pip install -r requirements.txt
```

Packages include `pymupdf`, `opencv-python`, `pillow`, `numpy`, `pytesseract`, `google-cloud-vision`, etc.

## 5. Configure Tesseract Path (Optional)

If Tesseract lives in a non-standard location, configure it via environment variables:

### Option A: Environment Variables (Recommended)

Add to your `.env` file:

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata
TESSERACT_LANG=eng
```

### Option B: System Environment Variables

```powershell
setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"
setx TESSDATA_PREFIX "C:\Program Files\Tesseract-OCR\tessdata"
setx TESSERACT_LANG "eng"
```

### Option C: Python Code (Not Recommended)

Only use if environment variables don't work:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

**Note:** The system automatically configures Tesseract from environment variables. Use `.env` file for project-specific settings.

## 6. Google Cloud Vision (Optional)

1. Install the Cloud SDK (optional but handy):
   ```powershell
   winget install Google.CloudSDK
   ```
2. Create a service account with Vision API access
3. Download JSON credentials and set environment variable:
   ```powershell
   setx GOOGLE_APPLICATION_CREDENTIALS "C:\path\to\service-account.json"
   ```
4. Enable Vision API in your Google Cloud project

## 7. Test the OCR Stack

```powershell
python - <<'PY'
from PIL import Image
import pytesseract

img = Image.new("RGB", (200, 60), color="white")
print("Tesseract version:", pytesseract.get_tesseract_version())
PY
```

No errors = foundation ready for integration.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `TesseractNotFoundError` | Confirm PATH includes installation directory or configure `pytesseract` manually |
| `ImportError: DLL load failed` (OpenCV) | Install VC++ redistributable, ensure 64-bit Python | 
| Permission issues | Run PowerShell as Administrator when installing system packages |
| OCR accuracy low | Increase DPI (`PDF_PREPROCESSING_DPI=600`), ensure preprocessing enabled |
