# ADR-0007: Multimodal LLM Processing as Default

**Status:** Accepted  
**Date:** November 2025 (estimated)  
**Deciders:** Development Team  
**Tags:** llm, extraction, default

## Context

Multiple LLM processing modes available:
- `text_llm`: Text-only processing (cost-effective)
- `vision_llm`: Vision-only processing
- `multimodal`: Text + images together in single call
- `dual_llm`: Text and vision processed separately, then merged

Need to choose a default that works best for most use cases.

## Decision

Chose **`multimodal`** as the default LLM processing mode (combined with `hybrid` extraction method).

## Consequences

### Positive
- **Best for signatures**: Multimodal excels at extracting signatory information
- **Context preservation**: Text and images together maintain context
- **Single API call**: More efficient than dual_llm
- **Handles mixed PDFs**: Works well with hybrid extraction method
- **Better accuracy**: Vision model sees both text and visual elements

### Negative
- **Higher cost**: Vision model calls are more expensive than text-only
- **Slower**: Vision processing can be slower than text-only
- **Token usage**: Images consume more tokens

### Neutral
- **Configurable**: Users can change to `text_llm` for cost savings
- **Use case dependent**: Best default, but not optimal for all scenarios

## Alternatives Considered

1. **`text_llm` as default**:
   - Pros: Lower cost, faster
   - Cons: Misses signature pages, lower accuracy for visual elements
   - **Rejected** - Accuracy and signature extraction are priorities

2. **`dual_llm` as default**:
   - Pros: Best of both worlds
   - Cons: Two API calls, higher cost, more complex
   - **Rejected** - Too expensive and complex for default

3. **`vision_llm` as default**:
   - Pros: Handles all visual elements
   - Cons: Ignores native text, less efficient
   - **Rejected** - Wastes native text extraction capability

## Implementation Notes

- Default: `LLM_PROCESSING_MODE=multimodal`
- Combined with `EXTRACTION_METHOD=hybrid` for optimal results
- Users can override via environment variable for cost optimization
- Best results for mixed PDFs with signature pages

