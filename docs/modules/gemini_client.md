# Gemini Client

**Module:** `ai.gemini_client`  
**Last Updated:** January 9, 2026  
**Version:** v2.0.0

## Purpose

The `GeminiClient` class provides integration with Google Gemini API for metadata extraction with integrated validation. It supports three processing modes:

- **Text-based extraction** (using Gemini text model)
- **Image-based extraction** (using Gemini Vision model)
- **Multimodal extraction** (text + images together)

## Features

- Text and vision model support
- Multimodal input (text + images in single call)
- **Config-based prompt generation**: Uses `FIELD_INSTRUCTIONS` and `TEMPLATE_REFERENCES` from config
- **Field metadata integration**: Displays `mandatory_field`, `negotiable`, and `expected_position` in prompt
- **Template references**: Includes clause excerpts, sample answers, and clause names in prompt
- **Negotiable fields guidance**: Explicit instructions for match flag assignment on negotiable fields
- **Integrated validation**: Returns validation scores and match flags as part of extraction
- **Template comparison**: Match flags indicate how extracted values compare to templates
- **Enhanced schema**: Returns `extracted_value`, `match_flag`, and `validation` for each field
- JSON parsing with markdown handling
- Schema validation and normalization
- Retry logic with exponential backoff
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

### Multimodal Extraction

```python
from ai.gemini_client import GeminiClient

client = GeminiClient()
# text: string, image_bytes_list: list of bytes
metadata = client.extract_metadata_multimodal(text, image_bytes_list)
```

## Prompt Template (v2.0.0)

The client uses a detailed prompt template that includes:
1. **Role Definition**: "You are a contract analyst."
2. **Task**: Extract metadata and return VALID JSON ONLY matching the schema
3. **Schema Structure**: Enhanced structure with `extracted_value`, `match_flag`, and `validation` for each field
4. **Field Definitions**: All field definitions from `FIELD_DEFINITIONS` organized by category
5. **Field-Specific Instructions**: LLM extraction instructions from `FIELD_INSTRUCTIONS` (config-based) including:
   - Field-specific extraction instructions
   - `mandatory_field`: Whether field is mandatory (yes/no)
   - `negotiable`: Whether field is negotiable (yes/no)
   - `expected_position`: Expected/standard position for non-negotiable fields
6. **Template References**: Clause excerpts, sample answers, and clause names from `TEMPLATE_REFERENCES` (populated for all 22 fields)
7. **Extraction Rules**: 18 rules including:
   - Enhanced field structure requirements
   - Match flag values and assignment guidance
   - Validation requirements (score, status, notes)
   - Negotiable fields guidance (match_flag reflects structure, not values)
   - Date formatting, Evergreen contracts, multiple values, etc.
8. **Search Guidance**: Instructions on where to find information in documents
9. **Contract Content**: Either contract text or images

See `docs/REQUIREMENTS.md` for complete field definitions and `docs/GEMINI_METADATA_FIELDS.md` for complete prompt structure.

## Configuration

- `GEMINI_API_KEY`: Required
- `GEMINI_TEXT_MODEL`: Text model (default: `gemini-2.5-pro`)
- `GEMINI_VISION_MODEL`: Vision model (default: `gemini-2.5-pro`)
- `MAX_TEXT_LENGTH`: Maximum text length (default: 50000)
- `API_MAX_RETRIES`: Maximum retry attempts (default: 3)
- `API_RETRY_INITIAL_DELAY`: Initial retry delay in seconds (default: 1)
- `API_RETRY_MAX_DELAY`: Maximum retry delay in seconds (default: 60)

## Error Handling

- Returns empty schema on error (all fields = "Not Found")
- Logs errors for debugging
- Handles JSON parsing errors gracefully
- Validates and normalizes output

## Dependencies

- `google-generativeai`
- `ai.schema` (SchemaValidator)

