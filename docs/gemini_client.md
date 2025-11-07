# Gemini Client

## Purpose

The `GeminiClient` class provides integration with Google Gemini API for:
- **Text-based metadata extraction** (using Gemini Flash text model)
- **Image-based metadata extraction** (using Gemini Vision model)

## Features

- Text and vision model support
- Schema-aware prompt generation
- JSON parsing with markdown handling
- Schema validation and normalization
- Error handling with fallback

## Usage

### Text-Based Extraction

```python
from ai.gemini_client import GeminiClient

client = GeminiClient()
metadata = client.extract_metadata_from_text(contract_text)
```

### Image-Based Extraction

```python
from ai.gemini_client import GeminiClient

client = GeminiClient()
with open("contract_page.png", "rb") as f:
    image_bytes = f.read()
metadata = client.extract_metadata_from_image(image_bytes, "image/png")
```

## Prompt Template

The client uses a detailed prompt template that includes:
- Field definitions from `FIELD_DEFINITIONS`
- Extraction rules (dates, Evergreen, multiple values, etc.)
- Schema structure
- Examples and format specifications

See `docs/REQUIREMENTS.md` for complete field definitions.

## Configuration

- `GEMINI_API_KEY`: Required
- `GEMINI_TEXT_MODEL`: Text model (default: `gemini-1.5-flash`)
- `GEMINI_VISION_MODEL`: Vision model (default: `gemini-1.5-flash`)
- `MAX_TEXT_LENGTH`: Maximum text length (default: 12000)

## Error Handling

- Returns empty schema on error (all fields = "Not Found")
- Logs errors for debugging
- Handles JSON parsing errors gracefully
- Validates and normalizes output

## Dependencies

- `google-generativeai`
- `ai.schema` (SchemaValidator)

