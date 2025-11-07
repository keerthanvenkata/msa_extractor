# Schema Validator

## Purpose

The `SchemaValidator` class provides JSON schema validation and normalization for extracted metadata.

## Features

- **Schema Validation**: Validates metadata against JSON Schema
- **Normalization**: Fills missing fields with "Not Found"
- **Empty Schema Generation**: Creates empty schema structure
- **Type Safety**: Ensures all fields are strings

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

## Schema Structure

The schema matches `METADATA_SCHEMA` from `config.py`:
- Contract Lifecycle (4 fields)
- Commercial Operations (3 fields)
- Risk & Compliance (4 fields)

All fields are required and must be strings.

## Dependencies

- `jsonschema` (for validation)
- `config` (for schema structure)

## Integration

- Used by `GeminiClient` for validation
- Used by `ExtractionCoordinator` for normalization
- Used by `main.py` for output validation

