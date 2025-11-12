# Configuration Reference

`config.py` centralises environment-driven settings so modules stay declarative and easy to test. The table below summarises the main categories.

**Important**: For metadata schema definitions and field requirements, see [`REQUIREMENTS.md`](REQUIREMENTS.md).

## API & Model Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Required for all Gemini calls | `` (must be set) |
| `GEMINI_TEXT_MODEL` | Text LLM for metadata extraction | `gemini-2.5-pro` |
| `GEMINI_VISION_MODEL` | Vision LLM for direct OCR/understanding | `gemini-2.5-pro` |
| `GEMINI_MODEL` | Legacy default (kept for backwards compatibility, not used) | `gemini-pro` |

## FastAPI Server Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | FastAPI server host | `0.0.0.0` |
| `API_PORT` | FastAPI server port | `8000` |
| `API_WORKERS` | Number of worker processes | `1` |
| `API_RELOAD` | Enable auto-reload (development) | `false` |
| `MAX_UPLOAD_SIZE_MB` | Maximum file upload size (MB) | `25` |
| `API_MAX_CONCURRENT_EXTRACTIONS` | Max concurrent background extraction tasks | `5` |
| `API_ENABLE_AUTH` | Enable API key authentication | `false` |
| `API_KEY` | API key for authentication (if enabled) | `` (must be set if auth enabled) |

## Extraction Configuration

| Variable | Description | Options | Default |
|----------|-------------|---------|---------|
| `EXTRACTION_METHOD` | How to extract content from PDF pages | `text_direct`, `ocr_all`, `ocr_images_only`, `vision_all`, `hybrid` | `hybrid` |
| `LLM_PROCESSING_MODE` | How to process extracted content with LLMs | `text_llm`, `vision_llm`, `multimodal`, `dual_llm` | `text_llm` |
| `OCR_ENGINE` | OCR backend when OCR is needed | `tesseract`, `gcv` | `tesseract` |

### Extraction Methods

- **`text_direct`**: Extract text directly from text pages, ignore image pages
- **`ocr_all`**: Convert all pages to images and run OCR on all pages
- **`ocr_images_only`**: Extract text from text pages + OCR only image pages
- **`vision_all`**: Convert all pages to images (no OCR, for vision LLM)
- **`hybrid`**: Extract text from text pages + convert image pages to images (default)

### LLM Processing Modes

- **`text_llm`**: Send all text (direct + OCR) to text LLM (default)
- **`vision_llm`**: Send all images to vision LLM
- **`multimodal`**: Send text + images together to vision LLM in single call
- **`dual_llm`**: Send text to text LLM + images to vision LLM separately, then merge

See [EXTRACTION_ARCHITECTURE.md](../architecture/EXTRACTION_ARCHITECTURE.md) for detailed information.

## PDF Preprocessing

| Variable | Description | Default |
|----------|-------------|---------|
| `PDF_PREPROCESSING_DPI` | Render resolution for converting PDFs to images | `300` |
| `ENABLE_IMAGE_PREPROCESSING` | Master switch for OpenCV preprocessing | `true` |
| `ENABLE_DESKEW` | Correct page rotation | `true` |
| `ENABLE_DENOISE` | Remove speckle noise | `true` |
| `ENABLE_ENHANCE` | Apply CLAHE contrast enhancement | `true` |
| `ENABLE_BINARIZE` | Adaptive thresholding to black/white | `true` |

## Tesseract OCR Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TESSERACT_CMD` | Path to Tesseract executable (optional, for non-standard installations) | `` (uses PATH) |
| `TESSERACT_LANG` | Language code(s) for OCR (ISO 639-2, e.g., "eng", "eng+fra") | `eng` |
| `TESSDATA_PREFIX` | Path to tessdata directory (optional, for custom location) | `` (uses default) |

**Note:** 
- **Windows:** If Tesseract is not in PATH, set `TESSERACT_CMD` to the full path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`)
- **Linux:** Usually in PATH (`/usr/bin/tesseract`), no configuration needed
- **Docker:** Usually in PATH, no configuration needed

## Paths & Storage

| Variable | Description | Default |
|----------|-------------|---------|
| `OUTPUT_DIR` | Folder for extracted JSON/exports | `./results` |
| `DB_PATH` | SQLite database location | `./msa_extractor.db` |
| `CONTRACTS_DIR` | Input contract directory (created if missing) | `./contracts` |

## Logging & Validation

- `LOG_LEVEL` — standard Python logging level (`INFO` default)
- `MAX_TEXT_LENGTH` — soft limit for text passed to LLMs (enforce chunking if exceeded)
- `validate_config()` — call at startup to ensure mandatory keys (currently `GEMINI_API_KEY`) are populated

## Practices

- Keep secrets in `.env` (never commit `.env`, use `.env.example`)
- When adding new toggles, document them here and provide sensible defaults
- Group related settings with section comments to keep `config.py` readable
