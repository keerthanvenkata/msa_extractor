# MSA Metadata Extractor

A Python-based contract intelligence system for extracting structured metadata from Master Service Agreements (MSAs). The system reads PDF and DOCX contracts and extracts a well-defined set of metadata fields into structured, machine-readable JSON for downstream workflows.

## Overview

The MSA Metadata Extractor processes Master Service Agreements to extract key metadata including:

- Contract lifecycle dates (execution, effective, expiration)
- Commercial operations (billing frequency, payment terms)
- Risk & compliance information (indemnification, liability caps, insurance requirements)

All outputs follow a fixed JSON schema, ensuring consistency and machine-readability. Detailed module documentation lives in [`docs/`](docs/README.md).

## Requirements

- Python 3.10 or higher
- Virtual environment (recommended)
- Tesseract OCR (for scanned PDFs) — see setup guides:
  - [Windows setup](docs/windows_ocr_setup.md)
  - [Linux & Docker setup](docs/LINUX_AND_DOCKER_SETUP.md)
- Optional: Google Cloud Vision API credentials (for cloud OCR)

## Setup

### 1. Create Virtual Environment

On Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages:

- `pymupdf` — PDF parsing & rendering
- `python-docx` — DOCX text extraction
- `opencv-python`, `numpy`, `Pillow` — image preprocessing for OCR
- `pytesseract` — Tesseract OCR bridge
- `google-cloud-vision` (optional) — cloud OCR
- `google-generativeai` — Gemini API client

### 3. Configure Environment Variables

Copy the example environment file:

```powershell
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```text
GEMINI_API_KEY=your_api_key_here
```

Optional environment toggles (full list in [configuration docs](docs/configuration.md)):

```text
GEMINI_TEXT_MODEL=gemini-2.5-pro
GEMINI_VISION_MODEL=gemini-2.5-pro
EXTRACTION_METHOD=hybrid
LLM_PROCESSING_MODE=multimodal
PDF_PREPROCESSING_DPI=300
ENABLE_IMAGE_PREPROCESSING=true
OCR_ENGINE=tesseract
```

### 4. Install Native OCR Dependencies

**Windows:** Follow [Windows OCR setup](docs/windows_ocr_setup.md)
- Tesseract OCR (UB Mannheim build or Chocolatey)
- Visual C++ Redistributable

**Linux:** Follow [Linux & Docker setup](docs/LINUX_AND_DOCKER_SETUP.md)
- Tesseract OCR (via package manager)
- OpenCV dependencies

**Docker:** See [Linux & Docker setup](docs/LINUX_AND_DOCKER_SETUP.md) for Dockerfile and docker-compose examples

## Project Structure

```text
msa_extractor/
├── docs/                    # Module documentation & setup guides
├── main.py                  # CLI / Streamlit entry (placeholder)
├── config.py                # Environment variables, constants
├── extractors/              # Text extraction modules
│   ├── base_extractor.py
│   ├── pdf_extractor.py
│   └── image_preprocessor.py
├── ai/                      # LLM integration (placeholder)
├── processors/              # Post-processing modules (placeholder)
├── storage/                 # Data persistence (placeholder)
├── ui/                      # User interface (placeholder)
└── tests/                   # Unit tests
```

See the [documentation index](docs/README.md) for module-level design notes.

## Usage

### CLI Usage

Single file extraction:

```bash
python main.py --file ./contracts/example_msa.pdf --out ./results/example_msa.json
```

Batch processing:

```bash
python main.py --dir ./contracts --out-dir ./results --parallel 4
```

### Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

## Output Schema

All outputs follow this JSON structure. See [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) for complete field definitions, examples, and extraction rules.

```json
{
  "Contract Lifecycle": {
    "Party A": "",
    "Party B": "",
    "Execution Date": "",
    "Effective Date": "",
    "Expiration / Termination Date": "",
    "Authorized Signatory - Party A": "",
    "Authorized Signatory - Party B": ""
  },
  "Commercial Operations": {
    "Billing Frequency": "",
    "Payment Terms": "",
    "Expense Reimbursement Rules": ""
  },
  "Risk & Compliance": {
    "Indemnification Clause Reference": "",
    "Limitation of Liability Cap": "",
    "Insurance Requirements": "",
    "Warranties / Disclaimers": ""
  }
}
```

**Key Rules:**
- Fields that cannot be found will return `"Not Found"` (never null or empty)
- Dates: Preferred ISO format `yyyy-mm-dd`; if ambiguous, include `(AmbiguousDate)` flag
- Expiration Date: Return `"Evergreen"` if contract auto-renews
- Multiple values: Combine with semicolons (e.g., multiple signatories)
- Clause references: Include section heading/number and 1-2 sentence excerpt

See [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) for complete field definitions and examples.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

- Follow PEP 8 guidelines
- Include docstrings for all modules, classes, and functions
- Keep code modular and testable

## Additional Resources

- [Module documentation](docs/README.md)
- [PDF preprocessing reference](docs/pdf_preprocessing.md)
- [Windows OCR setup](docs/windows_ocr_setup.md)

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

