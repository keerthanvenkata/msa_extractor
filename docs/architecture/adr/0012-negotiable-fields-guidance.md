# ADR-0012: Negotiable Fields Guidance

**Status:** Accepted  
**Date:** 2026-01-09  
**Deciders:** Development Team  
**Tags:** validation, template, prompt-engineering, v2.0.0

## Context

In v2.0.0, we introduced match flags to compare extracted values against template examples. However, some fields are inherently negotiable (e.g., Party A, Party B, Execution Date, Payment Terms) and will naturally vary between contracts. We needed to clarify how match flags should be assigned for these negotiable fields.

## Decision

We will explicitly guide the LLM that for negotiable fields:
1. The extracted values do NOT need to match the template values
2. The `match_flag` should reflect **structural similarity**, not **value similarity**
3. For negotiable fields:
   - Use `"same_as_template"` only if the STRUCTURE/FORMAT matches (e.g., both use "Net 30 days" format)
   - Use `"different_from_template"` if the actual VALUES differ (e.g., different party names, different dates, different payment terms)
4. For non-negotiable fields (e.g., Limitation of Liability Cap, Warranties), the match_flag should reflect how closely the extracted clause matches the template clause structure and content

## Consequences

### Positive
- More accurate match flag assignment for negotiable fields
- Better understanding of template compliance vs. value differences
- More meaningful quality assessment
- Clear distinction between negotiable and non-negotiable fields

### Negative
- Slightly more complex prompt instructions
- Requires LLM to understand the distinction between structure and value

### Neutral
- Field metadata (`negotiable` flag) is already in `FIELD_INSTRUCTIONS`
- No changes to response schema required

## Alternatives Considered

1. **No special handling**: Match flags would always compare values, leading to incorrect flags for negotiable fields
2. **Separate match flags for negotiable fields**: Would complicate the schema and API
3. **Remove match flags for negotiable fields**: Would reduce information available to users

## Implementation Notes

- Added explicit guidance in prompt (both text and vision versions)
- Guidance is included in `_build_extraction_prompt` method in `ai/gemini_client.py`
- Field metadata (`negotiable` flag) is displayed in field-specific instructions section
- Documentation updated in `docs/GEMINI_METADATA_FIELDS.md`

## References

- [ADR-0001: Enhanced Schema Structure](0001-enhanced-schema-structure.md)
- [ADR-0002: Config Refactoring](0002-config-refactoring-separation-of-concerns.md)
- `config.py` - `FIELD_INSTRUCTIONS` with `negotiable` metadata
- `ai/gemini_client.py` - Prompt builder with negotiable fields guidance

