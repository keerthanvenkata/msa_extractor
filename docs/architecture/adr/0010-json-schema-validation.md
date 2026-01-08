# ADR-0010: JSON Schema Validation Approach

**Status:** Accepted  
**Date:** November 2025 (estimated)  
**Deciders:** Development Team  
**Tags:** validation, schema, data-quality

## Context

Need to validate extracted metadata to ensure:
- All required fields are present
- Data types are correct
- Field lengths are within limits
- Structure matches expected schema

Options:
1. Manual validation (if/else checks)
2. Pydantic models
3. JSON Schema validation
4. Custom validation framework

## Decision

Chose **JSON Schema validation** using the `jsonschema` library, with dynamic schema generation from `METADATA_SCHEMA` config.

## Consequences

### Positive
- **Standard approach**: JSON Schema is industry standard
- **Dynamic**: Schema generated from config, stays in sync automatically
- **Comprehensive**: Validates structure, types, constraints
- **Clear errors**: JSON Schema provides detailed error messages
- **Flexible**: Easy to extend with new validation rules
- **Separation**: Validation logic separate from business logic

### Negative
- **Dependency**: Adds `jsonschema` library dependency
- **Performance**: Schema validation adds small overhead
- **Learning curve**: Team needs to understand JSON Schema

### Neutral
- **Config-driven**: Schema built from `METADATA_SCHEMA` in config
- **Normalization**: Validation includes normalization step

## Alternatives Considered

1. **Pydantic models**:
   - Pros: Type safety, automatic validation, Python-native
   - Cons: Schema defined in code, harder to modify
   - **Rejected** - Want config-driven schema

2. **Manual validation**:
   - Pros: Full control, no dependencies
   - Cons: Error-prone, hard to maintain, verbose
   - **Rejected** - Too much boilerplate

3. **Custom validation framework**:
   - Pros: Tailored to needs
   - Cons: More code to maintain, reinventing the wheel
   - **Rejected** - JSON Schema is standard

## Implementation Notes

- Schema built dynamically in `ai/schema.py` `_build_json_schema()`
- Uses `jsonschema.validate()` for validation
- Normalization step fills missing fields with `NOT_FOUND_VALUE`
- Validates field lengths, types, and structure
- Enhanced in v2.0.0 to handle validation objects and match flags

