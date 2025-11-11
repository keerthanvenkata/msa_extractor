# Data Masking & Encryption Plan

**Status:** 📋 Planning Phase  
**Priority:** P0 - Critical for Security & Compliance

## Overview

Before sending documents to external APIs (like Gemini), sensitive data must be masked or encrypted to protect privacy and comply with security requirements. This document outlines the data masking strategy and implementation plan.

## Requirements

### Security Goals
1. **Protect PII:** Personal Identifiable Information must not be sent to external APIs
2. **Protect Financial Data:** Account numbers, amounts, payment details must be masked
3. **Compliance:** Meet privacy regulations (GDPR, CCPA, etc.)
4. **Reversibility:** Must be able to map extracted metadata back to original values
5. **Configurability:** Allow users to configure what gets masked

### Functional Requirements
1. **Mask before API calls:** All text/images sent to Gemini must be masked
2. **Preserve structure:** Masking should maintain document structure for LLM extraction
3. **Re-map after extraction:** Map extracted metadata back to original values
4. **Support all extraction modes:** Text-only, multimodal, OCR-based
5. **Logging:** Log what was masked (without exposing original data)

## What to Mask

### 1. Personal Identifiable Information (PII)
- **Names:** Individual names, signatory names
- **Email addresses:** All email addresses
- **Phone numbers:** Phone, fax, mobile numbers
- **Addresses:** Physical addresses, mailing addresses
- **Social Security Numbers:** SSN, tax IDs
- **Employee IDs:** Employee identification numbers

### 2. Financial Information
- **Account numbers:** Bank accounts, credit card numbers
- **Amounts:** Dollar amounts, payment terms (if sensitive)
- **Payment details:** Wire transfer info, ACH details
- **Tax information:** Tax IDs, EIN numbers

### 3. Company Information (Optional)
- **Company names:** Client/vendor names (if required)
- **Internal references:** Project codes, contract numbers
- **Proprietary information:** Trade secrets, confidential terms

### 4. Dates (Optional)
- **Execution dates:** If dates are sensitive
- **Effective dates:** If dates reveal sensitive timing
- **Expiration dates:** If dates are confidential

### 5. Signatory Information (Optional)
- **Signatory names:** Names of authorized signatories
- **Titles:** Job titles and designations
- **Signatures:** Signature images (if sent to API)

## Masking Strategies

### Strategy 1: Placeholder Replacement (Recommended)
**Approach:** Replace sensitive values with structured placeholders

**Example:**
```
Original: "John Doe, VP of Operations"
Masked: "[SIGNATORY_1], [TITLE_1]"

Original: "john.doe@company.com"
Masked: "[EMAIL_1]"

Original: "Account: 1234-5678-9012"
Masked: "Account: [ACCOUNT_1]"
```

**Pros:**
- ✅ Maintains structure for LLM
- ✅ Easy to re-map
- ✅ Clear what type of data was masked
- ✅ LLM can still extract relationships

**Cons:**
- ⚠️ May confuse LLM if too many placeholders
- ⚠️ Need to handle LLM returning placeholders

### Strategy 2: Pattern-Based Masking
**Approach:** Replace with pattern-based placeholders

**Example:**
```
Email: "john@example.com" → "[EMAIL_ADDRESS]"
Phone: "+1-555-123-4567" → "[PHONE_NUMBER]"
Date: "2025-03-14" → "[DATE_YYYY-MM-DD]"
Amount: "$50,000" → "[CURRENCY_AMOUNT]"
```

**Pros:**
- ✅ Preserves data type information
- ✅ LLM understands what type of data to extract
- ✅ Easy pattern matching

**Cons:**
- ⚠️ Less specific than placeholder replacement

### Strategy 3: Encryption
**Approach:** Encrypt sensitive values with a key

**Example:**
```
Original: "John Doe"
Encrypted: "a7f3b2c9d1e4f5a6b7c8d9e0f1a2b3c"
```

**Pros:**
- ✅ Strong security
- ✅ Can decrypt if needed

**Cons:**
- ⚠️ LLM cannot understand encrypted data
- ⚠️ Requires key management
- ⚠️ May break extraction accuracy

**Recommendation:** Use for highly sensitive data that doesn't need to be extracted (e.g., account numbers)

### Strategy 4: Redaction
**Approach:** Remove sensitive sections entirely

**Example:**
```
Original: "Contact: John Doe, john@example.com, +1-555-1234"
Redacted: "Contact: [REDACTED]"
```

**Pros:**
- ✅ Strong privacy protection
- ✅ Simple implementation

**Cons:**
- ⚠️ May lose context for LLM
- ⚠️ May break extraction if critical info is redacted

**Recommendation:** Use sparingly, only for non-essential sensitive data

## Implementation Plan

### Phase 1: Core Masking Module
**File:** `utils/data_masking.py`

**Components:**
1. **DataMasker class:**
   - `mask_text(text: str) -> tuple[str, dict]` - Mask text, return masked text + mapping
   - `unmask_metadata(metadata: dict, mapping: dict) -> dict` - Re-map metadata
   - `mask_image(image_bytes: bytes) -> tuple[bytes, dict]` - Mask images (redact signatures)

2. **Masking functions:**
   - `mask_emails(text: str) -> tuple[str, dict]`
   - `mask_phones(text: str) -> tuple[str, dict]`
   - `mask_names(text: str) -> tuple[str, dict]`
   - `mask_addresses(text: str) -> tuple[str, dict]`
   - `mask_account_numbers(text: str) -> tuple[str, dict]`
   - `mask_dates(text: str) -> tuple[str, dict]`

3. **Pattern detection:**
   - Regex patterns for each data type
   - Configurable patterns via config

### Phase 2: Integration Points

1. **GeminiClient:**
   - Mask text before `extract_metadata_from_text()`
   - Mask images before `extract_metadata_from_image()`
   - Mask multimodal input before `extract_metadata_multimodal()`
   - Unmask metadata after extraction

2. **PDF Extractor:**
   - Mask text during extraction (if enabled)
   - Mask signature images (if enabled)

3. **OCR Handler:**
   - Mask OCR text before processing (if needed)

### Phase 3: Configuration

**Environment Variables:**
```env
# Enable/disable masking
ENABLE_DATA_MASKING=true

# What to mask
MASK_PII=true
MASK_FINANCIAL=true
MASK_COMPANY_NAMES=false
MASK_DATES=false
MASK_SIGNATORIES=true

# Masking method
MASKING_METHOD=placeholder  # placeholder, pattern, encryption, redaction

# Encryption key (if using encryption)
MASKING_ENCRYPTION_KEY=  # Optional, for encryption method
```

### Phase 4: Re-mapping

**After LLM Extraction:**
1. Check if extracted metadata contains masked values
2. Look up original values in mapping dictionary
3. Replace masked values with originals
4. Log what was re-mapped (for audit)

**Example:**
```python
# Original text
text = "John Doe, VP of Operations, john@example.com"

# Masked text sent to LLM
masked_text = "[SIGNATORY_1], [TITLE_1], [EMAIL_1]"
mapping = {
    "[SIGNATORY_1]": "John Doe",
    "[TITLE_1]": "VP of Operations",
    "[EMAIL_1]": "john@example.com"
}

# LLM returns
extracted = {
    "Authorized Signatory": "[SIGNATORY_1], [TITLE_1]"
}

# Re-map
unmasked = {
    "Authorized Signatory": "John Doe, VP of Operations"
}
```

## Configuration Options

### Masking Levels

1. **None:** No masking (not recommended for sensitive data)
2. **Minimal:** Mask only PII (names, emails, phones)
3. **Standard:** Mask PII + Financial data
4. **Maximum:** Mask everything except structure

### Per-Field Masking

Allow configuration per metadata field:
```env
MASK_EXECUTION_DATE=false
MASK_EFFECTIVE_DATE=false
MASK_SIGNATORY=true
MASK_PAYMENT_TERMS=false
```

## Security Considerations

1. **Key Management:**
   - Encryption keys must be stored securely
   - Use environment variables or key management service
   - Never commit keys to repository

2. **Mapping Storage:**
   - Mapping dictionaries should be stored securely
   - Consider encrypting mapping files
   - Clear mappings after processing

3. **Logging:**
   - Log that masking occurred (without exposing original data)
   - Log what types of data were masked
   - Do not log original values

4. **API Calls:**
   - Ensure masked data is sent to API
   - Verify no original data leaks in logs
   - Audit API calls for compliance

## Testing Requirements

1. **Unit Tests:**
   - Test masking functions for each data type
   - Test re-mapping accuracy
   - Test edge cases (no matches, multiple matches)

2. **Integration Tests:**
   - Test full pipeline with masking enabled
   - Verify extracted metadata is correctly re-mapped
   - Test with different masking configurations

3. **Security Tests:**
   - Verify no original data in API calls
   - Verify no original data in logs
   - Test key management

## Implementation Notes

1. **Performance:**
   - Masking adds processing time
   - Consider caching masked text for batch processing
   - Optimize regex patterns

2. **Accuracy:**
   - Masking may affect LLM extraction accuracy
   - Test with masked vs unmasked data
   - May need to adjust prompts for masked data

3. **Compatibility:**
   - Must work with all extraction modes
   - Must work with multimodal extraction
   - Must preserve document structure

## Next Steps

1. **Design Review:** Review masking strategy with security team
2. **Pattern Library:** Build comprehensive regex patterns
3. **Implementation:** Create `utils/data_masking.py` module
4. **Integration:** Integrate into GeminiClient and extractors
5. **Testing:** Comprehensive testing with masked data
6. **Documentation:** Update user guides with masking configuration

## References

- [GDPR Compliance](https://gdpr.eu/)
- [CCPA Compliance](https://oag.ca.gov/privacy/ccpa)
- [PII Definition](https://www.dol.gov/general/ppii)
- [Data Masking Best Practices](https://www.owasp.org/index.php/Data_Masking)

