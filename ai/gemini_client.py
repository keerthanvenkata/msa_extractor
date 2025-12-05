"""
Gemini API client for text and vision processing.

Handles both text-based LLM calls and vision model calls for metadata extraction.
"""

import json
import time
from typing import Dict, Any, Optional, List, Callable
import google.generativeai as genai

from config import (
    GEMINI_API_KEY,
    GEMINI_TEXT_MODEL,
    GEMINI_VISION_MODEL,
    METADATA_SCHEMA,
    FIELD_DEFINITIONS,
    NOT_FOUND_VALUE,
    MAX_TEXT_LENGTH,
    MAX_FIELD_LENGTH,
    API_MAX_RETRIES,
    API_RETRY_INITIAL_DELAY,
    API_RETRY_MAX_DELAY,
    API_RETRY_EXCEPTIONS
)
from .schema import SchemaValidator
from utils.logger import get_logger
from utils.exceptions import ConfigurationError, LLMError

logger = get_logger(__name__)


class GeminiClient:
    """Client for Gemini API (text and vision models)."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to config value)
        """
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ConfigurationError("GEMINI_API_KEY not set in environment or config")
        
        genai.configure(api_key=self.api_key)
        self.text_model = genai.GenerativeModel(GEMINI_TEXT_MODEL)
        self.vision_model = genai.GenerativeModel(GEMINI_VISION_MODEL)
        self.schema_validator = SchemaValidator()
        self.logger = get_logger(self.__class__.__module__)
    
    def extract_metadata_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract metadata from text using Gemini text model.
        
        Args:
            text: Contract text to analyze
        
        Returns:
            Dictionary with extracted metadata matching schema
        """
        # Truncate text if too long
        original_length = len(text)
        if original_length > MAX_TEXT_LENGTH:
            truncated_length = original_length - MAX_TEXT_LENGTH
            self.logger.warning(
                f"Text length ({original_length:,} chars) exceeds MAX_TEXT_LENGTH ({MAX_TEXT_LENGTH:,} chars). "
                f"Truncating {truncated_length:,} characters from the end. "
                f"This may result in missing metadata. Consider implementing chunking for long documents."
            )
            text = text[:MAX_TEXT_LENGTH]
        
        # Build prompt
        prompt = self._build_extraction_prompt(text)
        
        try:
            # Call Gemini API with retry logic
            response = self._call_with_retry(
                lambda: self.text_model.generate_content(prompt),
                operation="extract_metadata_from_text"
            )
            
            # Parse JSON response
            metadata = self._parse_json_response(response.text)
            
            # Validate BEFORE normalization to detect incomplete/malformed LLM responses
            is_valid, error = self.schema_validator.validate(metadata)
            if not is_valid:
                self.logger.warning(
                    f"Schema validation failed for raw LLM response: {error}. "
                    f"This indicates the LLM returned incomplete or malformed data. "
                    f"Normalizing to fill missing fields."
                )
            
            # Normalize to schema (fills missing fields with "Not Found")
            metadata = self.schema_validator.normalize(metadata)
            
            return metadata
            
        except LLMError:
            # Re-raise LLM errors
            raise
        except Exception as e:
            self.logger.error("Error extracting metadata from text", exc_info=True)
            raise LLMError(
                f"Failed to extract metadata from text: {e}",
                details={"text_length": len(text) if text else 0}
            ) from e
    
    def extract_metadata_from_image(self, image_bytes: bytes, 
                                    image_mime_type: str = "image/png") -> Dict[str, Any]:
        """
        Extract metadata from image using Gemini Vision model.
        
        Args:
            image_bytes: Image data as bytes
            image_mime_type: MIME type of image (default: image/png)
        
        Returns:
            Dictionary with extracted metadata matching schema
        """
        # Build prompt
        prompt = self._build_extraction_prompt("")
        
        try:
            # Call Gemini Vision API with retry logic
            response = self._call_with_retry(
                lambda: self.vision_model.generate_content([
                    prompt,
                    {
                        "mime_type": image_mime_type,
                        "data": image_bytes
                    }
                ]),
                operation="extract_metadata_from_image"
            )
            
            # Parse JSON response
            metadata = self._parse_json_response(response.text)
            
            # Validate BEFORE normalization to detect incomplete/malformed LLM responses
            is_valid, error = self.schema_validator.validate(metadata)
            if not is_valid:
                self.logger.warning(
                    f"Schema validation failed for raw LLM response: {error}. "
                    f"This indicates the LLM returned incomplete or malformed data. "
                    f"Normalizing to fill missing fields."
                )
            
            # Normalize to schema (fills missing fields with "Not Found")
            metadata = self.schema_validator.normalize(metadata)
            
            return metadata
            
        except LLMError:
            # Re-raise LLM errors
            raise
        except Exception as e:
            self.logger.error("Error extracting metadata from image", exc_info=True)
            raise LLMError(
                f"Failed to extract metadata from image: {e}",
                details={"image_mime_type": image_mime_type}
            ) from e
    
    def extract_metadata_multimodal(self, text: str, image_bytes_list: List[bytes],
                                   image_mime_type: str = "image/png") -> Dict[str, Any]:
        """
        Extract metadata from text and images using Gemini Vision model (multimodal input).
        
        This method sends both text and images together to the vision model, which is
        particularly useful for mixed PDFs where some pages are text-based and others
        are image-based (e.g., signature pages).
        
        Args:
            text: Contract text extracted from text-based pages
            image_bytes_list: List of image data as bytes (one per image page)
            image_mime_type: MIME type of images (default: image/png)
        
        Returns:
            Dictionary with extracted metadata matching schema
        """
        # Build prompt with text
        prompt = self._build_extraction_prompt(text)
        
        # Build content list: prompt + all images
        content = [prompt]
        for img_bytes in image_bytes_list:
            content.append({
                "mime_type": image_mime_type,
                "data": img_bytes
            })
        
        try:
            # Call Gemini Vision API with multimodal input (text + images)
            response = self._call_with_retry(
                lambda: self.vision_model.generate_content(content),
                operation="extract_metadata_multimodal"
            )
            
            # Parse JSON response
            metadata = self._parse_json_response(response.text)
            
            # Validate BEFORE normalization to detect incomplete/malformed LLM responses
            is_valid, error = self.schema_validator.validate(metadata)
            if not is_valid:
                self.logger.warning(
                    f"Schema validation failed for raw LLM response: {error}. "
                    f"This indicates the LLM returned incomplete or malformed data. "
                    f"Normalizing to fill missing fields."
                )
            
            # Normalize to fill missing fields
            metadata = self.schema_validator.normalize(metadata)
            
            self.logger.info(
                f"Multimodal extraction complete: {len(text)} chars text, "
                f"{len(image_bytes_list)} image(s)"
            )
            
            return metadata
            
        except LLMError:
            # Re-raise LLM errors
            raise
        except Exception as e:
            self.logger.error("Error extracting metadata from multimodal input", exc_info=True)
            raise LLMError(
                f"Failed to extract metadata from multimodal input: {e}",
                details={
                    "text_length": len(text) if text else 0,
                    "image_count": len(image_bytes_list)
                }
            ) from e
    
    def _build_extraction_prompt(self, text: str) -> str:
        """
        Build extraction prompt following docs/REQUIREMENTS.md specifications.
        
        Args:
            text: Contract text (empty for vision model)
        
        Returns:
            Formatted prompt string
        """
        schema_json = json.dumps(METADATA_SCHEMA, indent=2)
        
        # Build field definitions section
        definitions_text = self._build_field_definitions_text()
        
        if text:
            prompt = f"""You are a contract analyst. Extract the following metadata fields from the given Master Service Agreement and return VALID JSON ONLY matching this schema:

{schema_json}

FIELD DEFINITIONS:
{definitions_text}

EXTRACTION RULES:
1. If a field cannot be determined, use "{NOT_FOUND_VALUE}" (never null, empty list, or other placeholders).
2. For dates:
   - Preferred format: ISO yyyy-mm-dd (e.g., 2025-03-14)
   - If ambiguous or unclear: Return the literal text found and include "(AmbiguousDate)" as a flag
   - Example: "March 14, 2025 (AmbiguousDate)" or "Q1 2025 (AmbiguousDate)"
3. For "Expiration / Termination Date":
   - If contract is "Evergreen" (auto-renews): Return "Evergreen"
   - If no explicit expiration: Return "{NOT_FOUND_VALUE}"
4. For "Document Type":
   - Must be exactly "MSA" or "NDA" (case-sensitive)
   - Use "MSA" for Master/Professional Services Agreement
   - Use "NDA" for Non-Disclosure Agreement
   - Determine from document title or heading
5. For "Termination Notice Period":
   - Format: "<number> <unit>" (e.g., "30 days", "3 months")
   - Extract the primary/default notice period for the main agreement
   - If multiple periods exist (e.g., different for work orders), return the primary agreement notice
6. For "Pricing Model Type":
   - Must be exactly one of: "Fixed", "T&M", or "Subscription" (case-sensitive)
   - Use "T&M" if billed by hourly rates
   - Use "Fixed" or "Subscription" only if explicitly stated
7. For "Currency":
   - Use ISO currency code (e.g., "USD", "INR", "EUR", "GBP")
   - Infer from currency symbols ($, ₹, €, £) or explicitly stated amounts
   - If multiple currencies mentioned, prefer the primary settlement currency
8. For "Contract Value":
   - Return decimal number if explicitly stated (e.g., "50000.00" or "50000")
   - Many MSAs defer value to Work Orders/SOWs - return "{NOT_FOUND_VALUE}" if not specified in main agreement
   - Normalize commas if present
9. For "Force Majeure Clause Reference":
   - If no explicit clause exists, return "{NOT_FOUND_VALUE}"
   - Otherwise, return section heading/number and brief excerpt
10. For clause references (Indemnification, Confidentiality, Force Majeure):
    - Return the section heading/number and a 1–2 sentence excerpt
    - Example: "Section 12 – Indemnification: Each party agrees to indemnify..."
11. For Party A and Party B:
    - Extract full legal entity names as stated in the contract
    - Party A is typically the client/service recipient (first party mentioned)
    - Party B is typically the vendor/service provider (second party mentioned)
    - Look in the contract header, "Parties" section, or first paragraph
12. For Authorized Signatories:
    - Extract separately for each party from signature pages or execution sections
    - Include full name and title/designation
    - If multiple signatories for one party, combine with semicolons
    - Example: "John Doe, VP of Operations; Jane Smith, CFO" (for Party A)
13. Each field value must not exceed {MAX_FIELD_LENGTH} characters. If a field would exceed this limit, truncate it appropriately while preserving the most important information.
14. Return no commentary, no extra keys, and no markdown — JSON only.

SEARCH GUIDANCE:
- Agreements may have different structures and section names. Search the ENTIRE document thoroughly.
- Information may appear in: main body, signature pages, appendices, exhibits, schedules, or footers/headers.
- Organization Name: Look in preamble/opening party identification (typically Page 1).
- Document Type: Check document title/header (typically Page 1).
- Party A and Party B names are typically in the contract header, "Parties" section, or first paragraph.
- Execution Date and Authorized Signatories are often on signature pages (typically last page or last few pages).
- Termination Notice Period: Look in termination sections (e.g., "Section Four – Termination").
- Pricing Model Type: Check sections about work orders, rate schedules, or commercial terms (e.g., "Section Three – Work Orders").
- Currency: May appear in any monetary amounts (e.g., insurance limits, payment terms, rate schedules).
- Contract Value: Check Work Orders/SOW references; return "{NOT_FOUND_VALUE}" if not explicitly defined in main agreement.
- Payment Terms, Billing Frequency may be in sections named: "Payment", "Fees", "Compensation", "Commercial Terms", "Financial Terms", or similar.
- Governing Law: Look in sections named "Governing Law", "Jurisdiction", or "Applicable Law" (e.g., "Section Seventeen – Governing Law").
- Confidentiality Clause Reference: Check sections about confidential information (e.g., "Section Eight – Confidential Information").
- Force Majeure Clause Reference: Search for "Force Majeure" explicitly; if absent, return "{NOT_FOUND_VALUE}".
- Indemnification, Limitation of Liability, Insurance may be in: "Risk", "Liability", "Indemnification", "Insurance", "Warranties", or "General Provisions".
- Look for information regardless of exact section names - focus on content and context.
- Cross-reference related fields (e.g., Effective Date may be defined relative to Execution Date).

MSA TEXT:
\"\"\"{text}\"\"\"
"""
        else:
            # For vision model, text will be extracted from image
            prompt = f"""You are a contract analyst. Extract the following metadata fields from the given Master Service Agreement image and return VALID JSON ONLY matching this schema:

{schema_json}

FIELD DEFINITIONS:
{definitions_text}

EXTRACTION RULES:
1. If a field cannot be determined, use "{NOT_FOUND_VALUE}" (never null, empty list, or other placeholders).
2. For dates:
   - Preferred format: ISO yyyy-mm-dd (e.g., 2025-03-14)
   - If ambiguous or unclear: Return the literal text found and include "(AmbiguousDate)" as a flag
   - Example: "March 14, 2025 (AmbiguousDate)" or "Q1 2025 (AmbiguousDate)"
3. For "Expiration / Termination Date":
   - If contract is "Evergreen" (auto-renews): Return "Evergreen"
   - If no explicit expiration: Return "{NOT_FOUND_VALUE}"
4. For "Document Type":
   - Must be exactly "MSA" or "NDA" (case-sensitive)
   - Use "MSA" for Master/Professional Services Agreement
   - Use "NDA" for Non-Disclosure Agreement
   - Determine from document title or heading
5. For "Termination Notice Period":
   - Format: "<number> <unit>" (e.g., "30 days", "3 months")
   - Extract the primary/default notice period for the main agreement
   - If multiple periods exist (e.g., different for work orders), return the primary agreement notice
6. For "Pricing Model Type":
   - Must be exactly one of: "Fixed", "T&M", or "Subscription" (case-sensitive)
   - Use "T&M" if billed by hourly rates
   - Use "Fixed" or "Subscription" only if explicitly stated
7. For "Currency":
   - Use ISO currency code (e.g., "USD", "INR", "EUR", "GBP")
   - Infer from currency symbols ($, ₹, €, £) or explicitly stated amounts
   - If multiple currencies mentioned, prefer the primary settlement currency
8. For "Contract Value":
   - Return decimal number if explicitly stated (e.g., "50000.00" or "50000")
   - Many MSAs defer value to Work Orders/SOWs - return "{NOT_FOUND_VALUE}" if not specified in main agreement
   - Normalize commas if present
9. For "Force Majeure Clause Reference":
   - If no explicit clause exists, return "{NOT_FOUND_VALUE}"
   - Otherwise, return section heading/number and brief excerpt
10. For clause references (Indemnification, Confidentiality, Force Majeure):
    - Return the section heading/number and a 1–2 sentence excerpt
    - Example: "Section 12 – Indemnification: Each party agrees to indemnify..."
11. For Party A and Party B:
    - Extract full legal entity names as stated in the contract
    - Party A is typically the client/service recipient (first party mentioned)
    - Party B is typically the vendor/service provider (second party mentioned)
    - Look in the contract header, "Parties" section, or first paragraph
12. For Authorized Signatories:
    - Extract separately for each party from signature pages or execution sections
    - Include full name and title/designation
    - If multiple signatories for one party, combine with semicolons
    - Example: "John Doe, VP of Operations; Jane Smith, CFO" (for Party A)
13. Each field value must not exceed {MAX_FIELD_LENGTH} characters. If a field would exceed this limit, truncate it appropriately while preserving the most important information.
14. Return no commentary, no extra keys, and no markdown — JSON only.

SEARCH GUIDANCE:
- Agreements may have different structures and section names. Search the ENTIRE document thoroughly.
- Information may appear in: main body, signature pages, appendices, exhibits, schedules, or footers/headers.
- Organization Name: Look in preamble/opening party identification (typically Page 1).
- Document Type: Check document title/header (typically Page 1).
- Party A and Party B names are typically in the contract header, "Parties" section, or first paragraph.
- Execution Date and Authorized Signatories are often on signature pages (typically last page or last few pages).
- Termination Notice Period: Look in termination sections (e.g., "Section Four – Termination").
- Pricing Model Type: Check sections about work orders, rate schedules, or commercial terms (e.g., "Section Three – Work Orders").
- Currency: May appear in any monetary amounts (e.g., insurance limits, payment terms, rate schedules).
- Contract Value: Check Work Orders/SOW references; return "{NOT_FOUND_VALUE}" if not explicitly defined in main agreement.
- Payment Terms, Billing Frequency may be in sections named: "Payment", "Fees", "Compensation", "Commercial Terms", "Financial Terms", or similar.
- Governing Law: Look in sections named "Governing Law", "Jurisdiction", or "Applicable Law" (e.g., "Section Seventeen – Governing Law").
- Confidentiality Clause Reference: Check sections about confidential information (e.g., "Section Eight – Confidential Information").
- Force Majeure Clause Reference: Search for "Force Majeure" explicitly; if absent, return "{NOT_FOUND_VALUE}".
- Indemnification, Limitation of Liability, Insurance may be in: "Risk", "Liability", "Indemnification", "Insurance", "Warranties", or "General Provisions".
- Look for information regardless of exact section names - focus on content and context.
- Cross-reference related fields (e.g., Effective Date may be defined relative to Execution Date).

Extract all text from the image and analyze it to fill in the schema above.
"""
        
        return prompt
    
    def _build_field_definitions_text(self) -> str:
        """
        Build field definitions text for prompt.
        
        Returns:
            Formatted field definitions string
        """
        lines = []
        
        for category, fields in FIELD_DEFINITIONS.items():
            lines.append(f"{category}:")
            for field_name, definition in fields.items():
                lines.append(f"  - {field_name}: {definition}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _call_with_retry(self, api_call: Callable, operation: str = "api_call"):
        """
        Call API with retry logic and exponential backoff.
        
        Args:
            api_call: Callable that makes the API call
            operation: Name of operation for logging
        
        Returns:
            API response
        
        Raises:
            LLMError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(API_MAX_RETRIES + 1):
            try:
                return api_call()
            except Exception as e:
                last_exception = e
                exception_type = type(e).__name__
                exception_module = type(e).__module__
                full_exception_name = f"{exception_module}.{exception_type}"
                
                # Check if this exception should be retried
                should_retry = False
                
                # Check if exception type matches retryable exceptions
                for retryable_exception in API_RETRY_EXCEPTIONS:
                    if retryable_exception in full_exception_name or retryable_exception in exception_type:
                        should_retry = True
                        break
                
                # Also retry on common transient errors
                if not should_retry:
                    error_str = str(e).lower()
                    if any(keyword in error_str for keyword in [
                        "rate limit", "quota", "429", "503", "502", "500",
                        "timeout", "deadline", "unavailable", "retry"
                    ]):
                        should_retry = True
                
                # If this is the last attempt or shouldn't retry, raise
                if attempt == API_MAX_RETRIES or not should_retry:
                    if attempt > 0:
                        self.logger.error(
                            f"{operation} failed after {attempt + 1} attempts",
                            exc_info=True
                        )
                    raise LLMError(
                        f"API call failed: {e}",
                        details={
                            "operation": operation,
                            "attempts": attempt + 1,
                            "exception_type": full_exception_name
                        }
                    ) from e
                
                # Calculate exponential backoff delay
                delay = min(
                    API_RETRY_INITIAL_DELAY * (2 ** attempt),
                    API_RETRY_MAX_DELAY
                )
                
                self.logger.warning(
                    f"{operation} failed (attempt {attempt + 1}/{API_MAX_RETRIES + 1}): {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                time.sleep(delay)
        
        # Should never reach here, but just in case
        raise LLMError(
            f"API call failed after {API_MAX_RETRIES + 1} attempts",
            details={"operation": operation, "last_exception": str(last_exception)}
        ) from last_exception
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from Gemini response.
        
        Handles cases where response might be wrapped in markdown code blocks.
        
        Args:
            response_text: Raw response text from Gemini
        
        Returns:
            Parsed JSON dictionary
        """
        # Remove markdown code blocks if present
        text = response_text.strip()
        
        if text.startswith("```"):
            # Extract JSON from code block
            lines = text.split("\n")
            # Find first line with { and last line with }
            json_start = None
            json_end = None
            
            for i, line in enumerate(lines):
                if "{" in line and json_start is None:
                    json_start = i
                if "}" in line:
                    json_end = i
            
            if json_start is not None and json_end is not None:
                text = "\n".join(lines[json_start:json_end + 1])
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            self.logger.error(
                "Failed to parse JSON response from LLM",
                exc_info=True,
                extra={"response_preview": response_text[:500]}
            )
            # Return empty schema as fallback for parse errors
            # This is a recoverable error - LLM returned invalid JSON
            return self.schema_validator.get_empty_schema()

