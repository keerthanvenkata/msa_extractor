# ADR-0003: Integrated Validation vs Separate Validation Service

**Status:** Accepted  
**Date:** January 8, 2026  
**Deciders:** Development Team  
**Tags:** validation, architecture, performance

## Context

We needed to add validation capabilities to assess extraction quality. Two approaches were considered:
1. **Separate validation service**: Second LLM call after extraction
2. **Integrated validation**: Validation as part of extraction response

## Decision

Chose **integrated validation** - validation is performed by the same LLM call that does extraction. The LLM returns validation scores, status, and notes as part of the extraction response.

## Consequences

### Positive
- **Single LLM call**: More efficient, lower latency, lower cost
- **Consistent context**: Validation uses same context as extraction
- **Simpler architecture**: No separate service to maintain
- **Atomic operation**: Extraction and validation happen together
- **Better performance**: One API call instead of two

### Negative
- **Larger prompt**: Prompt includes validation instructions
- **LLM complexity**: LLM must handle both extraction and validation
- **Less flexibility**: Can't disable validation independently

### Neutral
- **Template dependency**: Validation quality depends on template references
- **Scoring consistency**: LLM must be consistent in scoring

## Alternatives Considered

1. **Separate validation service**: 
   - Pros: Can disable independently, separate concerns
   - Cons: Two LLM calls, higher latency, higher cost, context loss
   - **Rejected** - Performance and cost concerns

2. **Post-processing validation**:
   - Pros: No LLM call needed
   - Cons: Limited to rule-based validation, can't assess quality vs template
   - **Rejected** - Need template comparison

3. **Hybrid approach**:
   - Pros: Best of both worlds
   - Cons: Most complex
   - **Rejected** - Over-engineering for current needs

## Implementation Notes

- Validation instructions added to extraction prompt
- LLM returns validation object for each field
- Schema validator normalizes validation structure
- Old `validator_service.py` moved to `legacy/` folder (deprecated)

