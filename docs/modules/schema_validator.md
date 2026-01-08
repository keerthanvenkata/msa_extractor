# Schema Validator

**Module:** `ai.schema`  
**Last Updated:** January 8, 2026  
**Version:** v2.0.0

## Purpose

The `SchemaValidator` class provides JSON schema validation and normalization for extracted metadata with enhanced structure including validation scores and match flags.

## Features

- **Schema Validation**: Validates metadata against JSON Schema with enhanced structure
- **Normalization**: Fills missing fields with default values and ensures proper structure
- **Empty Schema Generation**: Creates empty schema structure with all fields
- **Enhanced Structure Support**: Handles `extracted_value`, `match_flag`, and `validation` objects
- **Validation Enforcement**: Validates match flags and validation status enums

## Usage

### Validation

```python
from ai.schema import SchemaValidator

validator = SchemaValidator()
is_valid, error = validator.validate(metadata)

if not is_valid:
    print(f"Validation error: {error}")
```

### Normalization

```python
from ai.schema import normalize_metadata

# Normalize metadata (fills missing fields)
normalized = normalize_metadata(metadata)
```

### Empty Schema

```python
from ai.schema import SchemaValidator

validator = SchemaValidator()
empty_schema = validator.get_empty_schema()
```

## Schema Structure (v2.0.0 Enhanced)

The schema matches `METADATA_SCHEMA` from `config.py`. Each field is an object with:

```json
{
  "extracted_value": "string",
  "match_flag": "same_as_template" | "similar_not_exact" | "different_from_template" | "flag_for_review" | "not_found",
  "validation": {
    "score": 0-100,
    "status": "valid" | "warning" | "invalid" | "not_found",
    "notes": "string (optional, max 500 chars)"
  }
}
```

**Categories:**
- Org Details (1 field: Organization Name)
- Contract Lifecycle (7 fields: Party A, Party B, Execution Date, Effective Date, Expiration/Termination Date, Authorized Signatory - Party A, Authorized Signatory - Party B)
- Business Terms (2 fields: Document Type, Termination Notice Period)
- Commercial Operations (3 fields: Billing Frequency, Payment Terms, Expense Reimbursement Rules)
- Finance Terms (3 fields: Pricing Model Type, Currency, Contract Value)
- Risk & Compliance (4 fields: Indemnification Clause Reference, Limitation of Liability Cap, Insurance Requirements, Warranties / Disclaimers)
- Legal Terms (3 fields: Governing Law, Confidentiality Clause Reference, Force Majeure Clause Reference)

**Validation Rules:**
- All fields are required
- `extracted_value` must be a string (max length: `MAX_FIELD_LENGTH`)
- `match_flag` must be one of the allowed enum values
- `validation.score` must be integer 0-100
- `validation.status` must be one of the allowed enum values
- `validation.notes` is optional, max 500 characters

## Dependencies

- `jsonschema` (for validation)
- `config` (for schema structure)

## Integration

- Used by `GeminiClient` for validation
- Used by `ExtractionCoordinator` for normalization
- Used by `main.py` for output validation

