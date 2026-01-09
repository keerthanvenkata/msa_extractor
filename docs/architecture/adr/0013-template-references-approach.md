# ADR-0013: Template References Approach

**Status:** Accepted  
**Date:** 2026-01-09  
**Deciders:** Development Team  
**Tags:** template, prompt-engineering, config, v2.0.0

## Context

To improve extraction quality and enable template-based validation, we needed to integrate template clause references into the extraction process. We had to decide:
1. Where to store template references
2. How to structure the template data
3. How to integrate it into the prompt
4. What information to include (full clause vs. excerpt, sample answers, clause names)

## Decision

We will:
1. Store template references in `TEMPLATE_REFERENCES` dictionary in `config.py` (separate from `FIELD_INSTRUCTIONS`)
2. Structure each field's template reference as:
   - `clause_excerpt`: Relevant excerpt from template clause (full clause for small ones, excerpt for large ones)
   - `sample_answer`: Sample answer from template for that field
   - `clause_name`: Name/number of clause in template (e.g., "Section 12 - Indemnification")
3. Include template references in the prompt as a separate section (after field-specific instructions)
4. Use template references to:
   - Guide extraction (show LLM what to look for)
   - Enable match flag assignment (compare against template)
   - Provide context for validation scoring

## Consequences

### Positive
- Centralized template data in config
- Clear separation from field instructions
- Easy to update template references independently
- Supports match flag assignment
- Improves extraction quality with examples

### Negative
- Larger prompt (but manageable)
- Requires maintaining template references in sync with template document
- Initial population effort required

### Neutral
- Template references are optional (can be empty for fields without template)
- No breaking changes to API

## Alternatives Considered

1. **Hardcode in prompt builder**: Would make updates difficult and mix concerns
2. **Separate template file**: Would require additional file management
3. **Include in FIELD_INSTRUCTIONS**: Would mix instructions with references
4. **Full clause always**: Would make prompt too long for large clauses
5. **No template references**: Would reduce extraction quality and match flag accuracy

## Implementation Notes

- `TEMPLATE_REFERENCES` dictionary structure in `config.py`:
  ```python
  TEMPLATE_REFERENCES = {
      "Field Name": {
          "clause_excerpt": "...",
          "sample_answer": "...",
          "clause_name": "Section X - Title"
      }
  }
  ```
- Template references populated for all 22 fields (January 2026)
- Prompt builder includes template references section via `_build_template_references_text()` method
- Template references displayed in prompt after field-specific instructions
- Documentation updated in `docs/GEMINI_METADATA_FIELDS.md` and `docs/FIELDS_REFERENCE.md`

## References

- [ADR-0002: Config Refactoring](0002-config-refactoring-separation-of-concerns.md)
- [ADR-0012: Negotiable Fields Guidance](0012-negotiable-fields-guidance.md)
- `config.py` - `TEMPLATE_REFERENCES` dictionary
- `ai/gemini_client.py` - `_build_template_references_text()` method

