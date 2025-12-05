# Schema Validator

**Module:** `ai.schema`  
**Last Updated:** November 12, 2025

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
- Org Details (1 field: Organization Name)
- Contract Lifecycle (7 fields: Party A, Party B, Execution Date, Effective Date, Expiration/Termination Date, Authorized Signatory - Party A, Authorized Signatory - Party B)
- Business Terms (2 fields: Document Type, Termination Notice Period)
- Commercial Operations (3 fields: Billing Frequency, Payment Terms, Expense Reimbursement Rules)
- Finance Terms (3 fields: Pricing Model Type, Currency, Contract Value)
- Risk & Compliance (4 fields: Indemnification Clause Reference, Limitation of Liability Cap, Insurance Requirements, Warranties / Disclaimers)
- Legal Terms (3 fields: Governing Law, Confidentiality Clause Reference, Force Majeure Clause Reference)

All fields are required and must be strings.

## Dependencies

- `jsonschema` (for validation)
- `config` (for schema structure)

## Integration

- Used by `GeminiClient` for validation
- Used by `ExtractionCoordinator` for normalization
- Used by `main.py` for output validation

