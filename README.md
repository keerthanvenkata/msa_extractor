# MSA Metadata Extractor

A Python-based contract intelligence system for extracting structured metadata from Master Service Agreements (MSAs). The system reads PDF and DOCX contracts and extracts a well-defined set of metadata fields into structured, machine-readable JSON for downstream workflows.

## Overview

The MSA Metadata Extractor processes Master Service Agreements to extract key metadata including:
- Contract lifecycle dates (execution, effective, expiration)
- Commercial operations (billing frequency, payment terms)
- Risk & compliance information (indemnification, liability caps, insurance requirements)

All outputs follow a fixed JSON schema, ensuring consistency and machine-readability.

## Requirements

- Python 3.10 or higher
- Virtual environment (recommended)

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

### 3. Configure Environment Variables

Copy the example environment file:
```bash
copy .env.example .env
```

On macOS/Linux:
```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

## Project Structure

```
msa_extractor/
├── main.py                   # CLI / Streamlit entry
├── config.py                 # Environment variables, constants
├── extractors/               # Text extraction modules
│   ├── pdf_extractor.py
│   └── docx_extractor.py
├── ai/                       # LLM integration
│   ├── gemini_client.py
│   └── schema.py
├── processors/               # Post-processing modules
│   ├── postprocess.py
│   └── clause_finder.py
├── storage/                  # Data persistence
│   ├── sqlite_store.py
│   └── file_store.py
├── ui/                       # User interface
│   └── streamlit_app.py
└── tests/                    # Unit tests
```

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

All outputs follow this JSON structure:

```json
{
  "Contract Lifecycle": {
    "Execution Date": "",
    "Effective Date": "",
    "Expiration / Termination Date": "",
    "Authorized Signatory": ""
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

Fields that cannot be found will return `"Not Found"` (never null or empty).

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

- Follow PEP 8 guidelines
- Include docstrings for all modules, classes, and functions
- Keep code modular and testable

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

