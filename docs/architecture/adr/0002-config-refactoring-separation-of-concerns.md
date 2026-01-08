# ADR-0002: Config Refactoring - Separation of Concerns

**Status:** Accepted  
**Date:** January 8, 2026  
**Deciders:** Development Team  
**Tags:** configuration, refactoring, maintainability

## Context

Field-specific LLM instructions were hardcoded in the prompt builder (`ai/gemini_client.py`), making it difficult to:
1. Update instructions without modifying code
2. Maintain consistency between documentation and code
3. Add template references for extraction guidance
4. Separate field definitions from extraction instructions

## Decision

Refactored configuration into four distinct dictionaries in `config.py`:
1. **`METADATA_SCHEMA`**: Structure only (defines categories and fields)
2. **`FIELD_DEFINITIONS`**: Field descriptions for LLM prompts
3. **`FIELD_INSTRUCTIONS`**: Field-specific extraction instructions (moved from prompt builder)
4. **`TEMPLATE_REFERENCES`**: Template clause excerpts, sample answers, and clause names

## Consequences

### Positive
- **Separation of concerns**: Each config serves a distinct purpose
- **Maintainability**: Instructions can be updated without touching code
- **Template integration**: Easy to add template examples
- **Consistency**: Single source of truth for each concern
- **Testability**: Configs can be tested independently

### Negative
- **More config files**: Four dictionaries instead of one
- **Initial setup complexity**: Need to understand all four configs

### Neutral
- **Prompt builder changes**: Now reads from config instead of hardcoding
- **Documentation updates**: All docs reference the new structure

## Alternatives Considered

1. **Single config dict**: Rejected - too monolithic, hard to maintain
2. **External config files**: Considered but rejected - Python dicts are easier for now
3. **Database storage**: Rejected - overkill for static configuration

## Implementation Notes

- All field instructions moved from `ai/gemini_client.py` to `config.py`
- Prompt builder uses `_build_field_instructions_text()` to format instructions
- Template references are optional (empty until populated)
- Backward compatibility: None (clean break)

