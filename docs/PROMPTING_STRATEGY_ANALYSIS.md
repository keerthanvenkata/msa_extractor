# Prompting Strategy Analysis

**Date:** 2025-01-07  
**Status:** Current Implementation Review

---

## Current Implementation

### What We're Doing Now

**We are sending the ENTIRE document text to the LLM** (with a 12,000 character limit).

#### For Text-Based PDFs:
1. Extract ALL text from ALL pages using PyMuPDF
2. Combine all text into a single `raw_text` string
3. Send entire `raw_text` to Gemini Flash (text LLM) with extraction prompt
4. If text exceeds 12,000 chars, truncate from the end (with warning)

#### For Image-Based PDFs (OCR):
1. OCR ALL pages using Tesseract/Google Cloud Vision
2. Combine all OCR text into a single `raw_text` string
3. Send entire `raw_text` to Gemini Flash (text LLM) with extraction prompt
4. If text exceeds 12,000 chars, truncate from the end (with warning)

#### For Gemini Vision Strategy:
1. Send first 3 pages as images to Gemini Vision API
2. Extract metadata directly from images (no text extraction step)
3. Extract text from all pages for reference

### What We're NOT Doing

- ❌ **No keyword extraction** - We don't pre-filter for relevant sections
- ❌ **No section filtering** - We don't extract only specific sections (e.g., "Terms", "Payment")
- ❌ **No keyword-based search** - We don't search for specific terms before sending to LLM
- ❌ **No context windowing** - We don't split into chunks and process separately (except truncation)

---

## Pros and Cons Analysis

### ✅ Pros of Sending Entire Document

#### 1. **Context Preservation**
- **Full context available**: LLM can see relationships between sections
- **Cross-references**: Can resolve references like "as stated in Section 12" or "per clause 3.2"
- **Consistency checking**: Can verify consistency across document (e.g., dates, amounts)
- **Contextual understanding**: Can understand implications and dependencies

**Example:**
- Payment terms might reference "Effective Date" defined earlier
- Indemnification clause might reference "Limitation of Liability" from another section
- Expiration date might be calculated based on "Effective Date" + "Term Duration"

#### 2. **Accuracy Benefits**
- **No information loss**: All relevant information is available
- **Better field extraction**: LLM can find information wherever it appears
- **Handles edge cases**: Can find metadata in unexpected locations (signature pages, appendices)
- **Reduces false negatives**: Less likely to miss information

**Example:**
- Execution date might be on signature page (last page)
- Authorized signatory might be in appendix
- Insurance requirements might be in a separate exhibit

#### 3. **Precision Benefits**
- **Better disambiguation**: Can distinguish between similar terms in different contexts
- **Handles multiple values**: Can identify all instances and combine appropriately
- **Understands relationships**: Can extract related information together

**Example:**
- Can distinguish "Effective Date" from "Execution Date" when both present
- Can identify all signatories when multiple parties sign
- Can extract full indemnification clause reference with context

#### 4. **Simplicity**
- **No preprocessing complexity**: Don't need to identify relevant sections
- **No keyword matching**: Don't need to maintain keyword lists
- **No filtering logic**: Simpler code, fewer edge cases
- **Easier to maintain**: Less code to maintain and debug

#### 5. **Cost Efficiency (for text LLMs)**
- **Single API call**: One request per document
- **Lower cost**: Text LLMs (Gemini Flash) are very cost-effective
- **No multiple passes**: Don't need to search, then extract, then validate

---

### ❌ Cons of Sending Entire Document

#### 1. **Potential Accuracy Issues**

**Noise and Distraction:**
- **Irrelevant content**: Large amounts of boilerplate, legal jargon, definitions
- **Information overload**: LLM might get distracted by irrelevant sections
- **Signal-to-noise ratio**: Important information might be diluted by noise

**Example:**
- 50-page contract with 5 pages of actual terms
- 45 pages of definitions, exhibits, appendices
- LLM might focus on wrong sections

**However, this is mitigated by:**
- Modern LLMs (Gemini Flash) are very good at focusing on relevant information
- Well-structured prompts guide the LLM to specific fields
- Field definitions in prompt help LLM identify what to extract

#### 2. **Token Limit Constraints**

**Current Limit:**
- `MAX_TEXT_LENGTH = 12,000` characters
- For very long documents, we truncate from the end
- This can lose important information (signature pages, appendices)

**Impact:**
- Large contracts (100+ pages) might exceed limit
- Truncation loses context from end of document
- May miss metadata on later pages

**Mitigation:**
- We log warnings when truncation occurs
- TODO-001: Implement chunking for long documents (planned)

#### 3. **Processing Time**

**Latency:**
- Larger documents take longer to process
- More tokens = longer API response time
- But this is usually acceptable (2-5 seconds for typical contracts)

**Not a major concern:**
- Text LLMs are fast
- Single API call is faster than multiple passes
- Acceptable for batch processing

#### 4. **Cost (for very large documents)**

**Token costs:**
- More tokens = higher cost
- But Gemini Flash is very cost-effective
- Still cheaper than multiple API calls with filtering

**Not a concern at current stage:**
- User stated cost is not a problem
- Text LLMs are inexpensive
- Single call is more efficient than multiple calls

---

## Alternative Approaches

### Approach 1: Keyword-Based Section Extraction

**How it works:**
1. Search for keywords (e.g., "Payment Terms", "Effective Date", "Indemnification")
2. Extract sections containing keywords
3. Send only relevant sections to LLM

**Pros:**
- Reduces token count
- Focuses on relevant sections
- Faster processing

**Cons:**
- ❌ **Lower accuracy**: Might miss information in unexpected locations
- ❌ **False negatives**: Keywords might not match exactly
- ❌ **Context loss**: Can't resolve cross-references
- ❌ **Maintenance burden**: Need to maintain keyword lists
- ❌ **Edge cases**: What if "Effective Date" is in a table or footnote?

**Verdict:** ❌ **Not recommended** - Too risky for accuracy-critical use case

---

### Approach 2: Structured Section Extraction

**How it works:**
1. Parse document structure (headers, sections)
2. Identify relevant sections (e.g., "Terms", "Payment", "Liability")
3. Extract only those sections
4. Send to LLM

**Pros:**
- Reduces token count
- Maintains some context within sections
- More targeted extraction

**Cons:**
- ❌ **Complexity**: Need robust section detection
- ❌ **Inconsistent structure**: Documents vary in structure
- ❌ **Context loss**: Can't resolve cross-references between sections
- ❌ **False negatives**: Might miss sections with non-standard headers
- ❌ **Maintenance**: Need to handle various document structures

**Verdict:** ❌ **Not recommended** - Too complex, too risky for accuracy

---

### Approach 3: Chunking with Aggregation

**How it works:**
1. Split document into chunks (e.g., 10,000 chars each)
2. Process each chunk with LLM
3. Aggregate results intelligently
4. Resolve conflicts and merge

**Pros:**
- ✅ Handles very long documents
- ✅ No truncation loss
- ✅ Can process documents of any size

**Cons:**
- ❌ **Complexity**: Need intelligent aggregation logic
- ❌ **Multiple API calls**: More expensive and slower
- ❌ **Context loss**: Chunks lose cross-chunk context
- ❌ **Aggregation challenges**: How to merge results? Handle conflicts?
- ❌ **Accuracy risk**: Might miss information that spans chunks

**Verdict:** ⚠️ **Use only when necessary** - For documents exceeding token limits

**Current Status:** TODO-001 (planned for Phase 2)

---

### Approach 4: Hybrid - Full Document with Smart Prompting

**How it works (Current + Enhancements):**
1. Send entire document (current approach)
2. Enhance prompt with:
   - Section hints (e.g., "Payment terms are usually in Section X")
   - Priority guidance (e.g., "Check signature page for execution date")
   - Context markers (e.g., "Look for cross-references to Section Y")

**Pros:**
- ✅ Maintains full context
- ✅ Guides LLM to relevant sections
- ✅ No information loss
- ✅ Simple to implement

**Cons:**
- Still sends full document (token cost)
- But this is acceptable per user requirements

**Verdict:** ✅ **Recommended enhancement** - Best of both worlds

---

## Recommendations

### For Current Stage (Accuracy & Precision Priority)

**✅ Keep sending entire document** with these enhancements:

1. **Enhance prompts with section guidance:**
   - Add hints about where to find information
   - Guide LLM to check signature pages, appendices
   - Provide examples of common locations

2. **Increase MAX_TEXT_LENGTH:**
   - Current: 12,000 chars (~3-5 pages)
   - Recommended: 50,000-100,000 chars (~15-30 pages)
   - This covers most contracts without chunking

3. **Implement chunking for very long documents:**
   - Only when document exceeds new limit
   - Use intelligent aggregation
   - TODO-001 (already planned)

4. **Add prompt engineering improvements:**
   - Emphasize accuracy and precision in prompt
   - Add examples of correct extractions
   - Guide LLM to verify information

### Why This Approach is Best

1. **Accuracy**: Full context = better accuracy
2. **Precision**: Can extract exact values with context
3. **Handles edge cases**: Information in unexpected locations
4. **Simple**: No complex filtering logic
5. **Cost-effective**: Single API call, text LLMs are cheap
6. **Maintainable**: Less code, fewer edge cases

---

## Accuracy vs Precision Analysis

### Current Approach Impact

**Accuracy (Correctness):**
- ✅ **High**: Full document provides all information
- ✅ **No false negatives**: Information won't be missed due to filtering
- ✅ **Context-aware**: Can understand relationships and dependencies

**Precision (Exactness):**
- ✅ **High**: Can extract exact values with full context
- ✅ **Disambiguation**: Can distinguish between similar terms
- ✅ **Complete extraction**: Can get full clause references, not just keywords

**Potential Issues:**
- ⚠️ **Noise**: Irrelevant content might distract (but modern LLMs handle this well)
- ⚠️ **Token limits**: Very long documents might be truncated (mitigated by chunking)

### Alternative Approach Impact

**Keyword/Section Filtering:**
- ❌ **Lower accuracy**: Might miss information
- ❌ **False negatives**: Information in unexpected locations
- ❌ **Lower precision**: Can't resolve cross-references
- ❌ **Context loss**: Can't understand relationships

**Verdict:** Current approach is better for accuracy and precision

---

## Conclusion

**Recommendation: Keep sending entire document** with enhancements:

1. ✅ **Maintain current approach** (full document)
2. ✅ **Enhance prompts** with section guidance
3. ✅ **Increase MAX_TEXT_LENGTH** to 50,000-100,000 chars
4. ✅ **Implement chunking** only for very long documents (TODO-001)

**Rationale:**
- Accuracy and precision are priorities
- Full context is essential for accurate extraction
- Cost is not a concern for text LLMs
- Modern LLMs handle full documents well
- Simpler code, fewer edge cases

**Next Steps:**
1. Enhance prompts with section guidance
2. Increase MAX_TEXT_LENGTH
3. Add prompt examples and best practices
4. Plan chunking implementation for edge cases

---

## References

- Current implementation: `ai/gemini_client.py`
- Text extraction: `extractors/pdf_extractor.py`
- Prompt building: `ai/gemini_client.py:_build_extraction_prompt()`
- TODO-001: Chunking for long documents (planned)

