# ADR-0004: Two-Tier Extraction Architecture

**Status:** Accepted  
**Date:** November 2025 (estimated)  
**Deciders:** Development Team  
**Tags:** architecture, extraction, design

## Context

The original extraction system had a single "extraction mode" that combined content extraction and LLM processing into one concept. This led to:
- Confusion between extraction strategies and processing modes
- Limited flexibility in combining extraction methods with processing approaches
- Difficulty understanding what each mode actually did
- Hard to extend with new methods

## Decision

Adopted a **two-tier architecture** that separates:
1. **Content Extraction Methods** (`EXTRACTION_METHOD`): How to extract content from PDF pages
   - `text_direct`, `ocr_all`, `ocr_images_only`, `vision_all`, `hybrid`
2. **LLM Processing Modes** (`LLM_PROCESSING_MODE`): How to process extracted content with LLMs
   - `text_llm`, `vision_llm`, `multimodal`, `dual_llm`

This allows any extraction method to be combined with any processing mode (5 × 4 = 20+ combinations).

## Consequences

### Positive
- **Clear separation of concerns**: Extraction vs Processing are distinct
- **Greater flexibility**: Can mix and match methods and modes
- **Better naming**: Method names clearly indicate what they do
- **Easier to understand**: No confusion between "mode" and "strategy"
- **Future-proof**: Easy to add new extraction methods or processing modes

### Negative
- **More configuration**: Two variables instead of one
- **Migration needed**: Old configs need updating

### Neutral
- **Default combination**: `hybrid` + `multimodal` chosen as default (best for mixed PDFs)

## Alternatives Considered

1. **Single extraction mode**: Rejected - too limiting, confusing
2. **Three-tier architecture**: Considered but rejected - over-engineering
3. **Strategy pattern with inheritance**: Rejected - too complex for current needs

## Implementation Notes

- Migration guide provided in `docs/architecture/EXTRACTION_ARCHITECTURE.md`
- Old configs mapped to new two-variable approach
- Default: `EXTRACTION_METHOD=hybrid` + `LLM_PROCESSING_MODE=multimodal`

