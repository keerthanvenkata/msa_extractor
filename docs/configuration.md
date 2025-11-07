# Configuration Reference

`config.py` centralises environment-driven settings so modules stay declarative and easy to test. The table below summarises the main categories.

**Important**: For metadata schema definitions and field requirements, see [`REQUIREMENTS.md`](REQUIREMENTS.md).

## API & Model Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Required for all Gemini calls | `` (must be set) |
| `GEMINI_TEXT_MODEL` | Text LLM for metadata extraction (`gemini-1.5-flash` recommended) | `gemini-1.5-flash` |
| `GEMINI_VISION_MODEL` | Vision LLM for direct OCR/understanding | `gemini-1.5-flash` |
| `GEMINI_MODEL` | Legacy default (kept for backwards compatibility) | `gemini-pro` |

## Extraction Strategies

| Variable | Description | Options |
|----------|-------------|---------|
| `EXTRACTION_STRATEGY` | Global strategy selector | `auto`, `text_extraction`, `gemini_vision`, `tesseract`, `gcv` |
| `OCR_ENGINE` | OCR backend when strategy relies on OCR | `tesseract`, `gcv` |

### Auto Strategy Behaviour

1. Detect PDF type (text vs image vs mixed)
2. Text-based → Text extraction + Gemini Flash
3. Image-based → chosen OCR engine (Tesseract/GCV) or direct Gemini Vision
4. Mixed → falls back to text extraction with logging (per-page logic planned)

## PDF Preprocessing

| Variable | Description | Default |
|----------|-------------|---------|
| `PDF_PREPROCESSING_DPI` | Render resolution for converting PDFs to images | `300` |
| `ENABLE_IMAGE_PREPROCESSING` | Master switch for OpenCV preprocessing | `true` |
| `ENABLE_DESKEW` | Correct page rotation | `true` |
| `ENABLE_DENOISE` | Remove speckle noise | `true` |
| `ENABLE_ENHANCE` | Apply CLAHE contrast enhancement | `true` |
| `ENABLE_BINARIZE` | Adaptive thresholding to black/white | `true` |

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
