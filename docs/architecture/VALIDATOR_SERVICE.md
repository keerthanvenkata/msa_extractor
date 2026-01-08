# Validator Service Architecture

**Status:** Skeleton Implementation  
**Last Updated:** December 2025

## Overview

The Validator Service validates extracted MSA metadata against industry-standard templates and examples. It runs as a separate LLM call after initial extraction and enhances the metadata with:

- **Validation Scores** (0-100 per field/category)
- **Validation Flags** (missing_required, deviates_from_standard, etc.)
- **Negotiability Indicators** (negotiable vs compulsory)
- **Acceptable Deviation Analysis**
- **Recommendations and Insights**

## Architecture

### Current Pipeline (Before Validator)

```
1. API Upload → Background Task
2. ExtractionCoordinator.extract_metadata()
   ├─> Extract text from document
   └─> Process with Gemini LLM (extraction)
3. Schema Validation
4. Store in Database
5. Return to API
```

### Enhanced Pipeline (With Validator)

```
1. API Upload → Background Task
2. ExtractionCoordinator.extract_metadata()
   ├─> Extract text from document
   └─> Process with Gemini LLM (extraction)
3. Schema Validation
4. ValidatorService.validate_metadata()  ← NEW
   └─> Separate LLM call with templates/examples
5. Merge validation results with extracted metadata
6. Store enhanced metadata in Database
7. Return enhanced result to API
```

## Integration Points

### 1. Extraction Service (`api/services/extraction_service.py`)

**Current Flow:**
```python
metadata = coordinator.extract_metadata(...)
# Validate schema
validator = coordinator.gemini_client.schema_validator
is_valid, error = validator.validate(metadata)
metadata = validator.normalize(metadata)
# Store results
db.complete_job(..., result_json_dict=metadata, ...)
```

**Enhanced Flow:**
```python
metadata = coordinator.extract_metadata(...)
# Validate schema
validator = coordinator.gemini_client.schema_validator
is_valid, error = validator.validate(metadata)
metadata = validator.normalize(metadata)

# NEW: Run validation service
from ai.validator_service import ValidatorService
validator_service = ValidatorService(gemini_client=coordinator.gemini_client)
enhanced_metadata = validator_service.validate_metadata(
    extracted_metadata=metadata,
    original_text=extraction_result.raw_text  # If available
)

# Store enhanced results
db.complete_job(..., result_json_dict=enhanced_metadata, ...)
```

### 2. API Response Models (`api/models/responses.py`)

**Current Response:**
```python
class ResultResponse(BaseModel):
    metadata: Dict[str, Any]  # Just extracted metadata
```

**Enhanced Response:**
```python
class ResultResponse(BaseModel):
    metadata: Dict[str, Any]  # Enhanced with validation
    # OR separate:
    # extracted_metadata: Dict[str, Any]
    # validation: Dict[str, Any]
```

### 3. Database Schema

**Current:** Stores `result_json` as extracted metadata only.

**Enhanced:** Store enhanced metadata with validation results:
```json
{
  "metadata": { /* original extracted fields */ },
  "validation": {
    "validation_summary": { /* scores, counts */ },
    "field_validations": { /* per-field validation */ },
    "category_scores": { /* per-category scores */ },
    "recommendations": [ /* list of recommendations */ ]
  }
}
```

## Validation Template Structure

Each field template includes:

```python
{
  "example": "Standard example value",
  "description": "What this field represents",
  "negotiable": True/False,
  "compulsory": True/False,
  "acceptable_deviations": [
    "List of acceptable variations"
  ],
  "scoring_criteria": {
    "present_and_valid": 100,
    "present_with_issues": 75,
    "missing": 0
  },
  "what_to_look_for": [
    "Where to find this information",
    "Common section names"
  ]
}
```

## Validation Output Structure

```json
{
  "metadata": {
    /* Original extracted metadata preserved */
  },
  "validation": {
    "validation_summary": {
      "overall_score": 85,
      "total_fields": 22,
      "validated_fields": 20,
      "missing_required": 2,
      "deviations": 3,
      "validation_timestamp": "2025-12-XX..."
    },
    "field_validations": {
      "Contract Lifecycle": {
        "Execution Date": {
          "score": 100,
          "status": "valid",
          "flags": [],
          "deviation": null,
          "negotiable": false,
          "compulsory": true,
          "insights": "Date format is correct and present"
        },
        "Party A": {
          "score": 100,
          "status": "valid",
          "flags": [],
          ...
        }
      }
    },
    "category_scores": {
      "Contract Lifecycle": 95,
      "Commercial Operations": 80,
      "Finance Terms": 75,
      "Risk & Compliance": 90,
      "Legal Terms": 85
    },
    "recommendations": [
      "Missing Termination Notice Period - should be included",
      "Payment Terms deviate from standard - review recommended",
      "Indemnification clause present but may need legal review"
    ]
  }
}
```

## Required Changes

### 1. Configuration
- [ ] Create `config/validation_templates.py` with all field templates
- [ ] Load templates in `ValidatorService.__init__()`
- [ ] Add config option to enable/disable validation

### 2. Extraction Service
- [ ] Import `ValidatorService` in `extraction_service.py`
- [ ] Add validation step after schema validation
- [ ] Handle validation errors gracefully (fallback to original metadata)
- [ ] Log validation results

### 3. API Models
- [ ] Update `ResultResponse` to document enhanced structure
- [ ] Ensure backward compatibility (if needed)

### 4. Database
- [ ] No schema changes needed (stores JSON)
- [ ] Ensure enhanced metadata fits in `result_json` column

### 5. Documentation
- [ ] Update API docs with validation response structure
- [ ] Document validation scores and flags
- [ ] Add examples of validation output

## Configuration Options

Add to `config.py`:

```python
# Validation Configuration
VALIDATION_ENABLED = os.getenv("VALIDATION_ENABLED", "true").lower() == "true"
VALIDATION_TEMPLATES_PATH = os.getenv("VALIDATION_TEMPLATES_PATH", "config/validation_templates.py")
```

## Error Handling

- **LLM Validation Fails:** Return original metadata with error flag
- **Parse Error:** Return original metadata with validation error
- **Template Missing:** Log warning, skip validation for that field
- **Timeout:** Return original metadata, log timeout

## Performance Considerations

- **Separate LLM Call:** Adds ~2-5 seconds to extraction time
- **Token Usage:** Additional ~2000-3000 tokens per validation
- **Cost:** ~$0.01-0.02 per validation (Gemini pricing)
- **Caching:** Could cache validation templates (future optimization)

## Future Enhancements

1. **Template Management:** Load from database or external API
2. **Custom Templates:** Allow users to provide custom templates
3. **Validation History:** Track validation scores over time
4. **ML-Based Scoring:** Train model on validation patterns
5. **Batch Validation:** Validate multiple contracts together



