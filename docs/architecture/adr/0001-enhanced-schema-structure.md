# ADR-0001: Enhanced Schema Structure with Validation and Match Flags

**Status:** Accepted  
**Date:** January 8, 2026  
**Deciders:** Development Team  
**Tags:** schema, validation, architecture

## Context

The original schema structure returned simple string values for each field. As the system evolved, we needed:
1. A way to track how extracted values compare to template examples
2. Per-field validation scores and status
3. Better quality assessment of extracted data
4. Integration of validation into the extraction response

## Decision

We adopted an enhanced schema structure where each field is an object containing:
- `extracted_value`: The actual extracted value (string)
- `match_flag`: Indicates how the value compares to template (`same_as_template`, `similar_not_exact`, `different_from_template`, `flag_for_review`, `not_found`)
- `validation`: Object with `score` (0-100), `status` (valid/warning/invalid/not_found), and optional `notes`

## Consequences

### Positive
- **Integrated validation**: Validation is part of extraction, not a separate step
- **Template comparison**: Match flags enable comparison against standard templates
- **Quality metrics**: Per-field scores provide granular quality assessment
- **Single LLM call**: More efficient than separate validation service
- **Consistent structure**: All fields follow the same pattern

### Negative
- **Larger response size**: Each field now has 3 properties instead of 1
- **Breaking change**: Existing integrations need to be updated
- **More complex schema**: Validation logic is more complex

### Neutral
- **Backward compatibility**: Removed to simplify codebase (no legacy support)
- **Template dependency**: Match flags require template references to be meaningful

## Alternatives Considered

1. **Separate validation service**: Rejected - adds latency and complexity
2. **Parallel structure**: Rejected - harder to maintain field-level consistency
3. **Legacy compatibility**: Rejected - adds complexity, decided to make clean break

## Implementation Notes

- Schema defined in `config.py` as `METADATA_SCHEMA`
- Validation handled in `ai/schema.py`
- Prompt instructions in `ai/gemini_client.py`
- All 22 fields use the enhanced structure

