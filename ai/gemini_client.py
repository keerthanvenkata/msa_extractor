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
    FIELD_INSTRUCTIONS,
    TEMPLATE_REFERENCES,
    MATCH_FLAG_VALUES,
    VALIDATION_STATUS_VALUES,
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
        
        # Build sections
        definitions_text = self._build_field_definitions_text()
        instructions_text = self._build_field_instructions_text()
        template_refs_text = self._build_template_references_text()
        
        if text:
            prompt = f"""You are a contract analyst. Extract the following metadata fields from the given Master Service Agreement (MSA) or Non-Disclosure Agreement (NDA). Focus on MSA extraction; detect NDA but do not extract NDA-specific fields. Return VALID JSON ONLY matching this schema:

{schema_json}

FIELD DEFINITIONS:
{definitions_text}

FIELD-SPECIFIC INSTRUCTIONS:
{instructions_text}
"""
            
            # Add template references if available
            if template_refs_text:
                prompt += f"""
TEMPLATE REFERENCES (Use as examples for extraction):
{template_refs_text}
"""
            
            prompt += f"""
================================================================================
EXTRACTION RULES
================================================================================

GENERAL RULES:
1. If a field cannot be determined, use "{NOT_FOUND_VALUE}" (never null, empty list, or other placeholders).
2. Each field value must not exceed {MAX_FIELD_LENGTH} characters. If a field would exceed this limit, truncate it appropriately while preserving the most important information.
3. Return no commentary, no extra keys, and no markdown — JSON only.
4. For EACH field in the schema, you MUST provide a complete object with:
   - extracted_value: The actual extracted value (string)
   - match_flag: One of the allowed values below (string)
   - validation: A validation object with score, status, and notes (object)

MATCH FLAG VALUES (choose exactly one per field):
- "same_as_template": Extracted value exactly matches template example (if template provided)
- "similar_not_exact": Extracted value is similar to template but with minor differences (format, wording, slight variations)
- "different_from_template": Extracted value differs significantly from template or uses different approach
- "flag_for_review": Value extracted but needs human review (ambiguous, unusual format, complex scenario, or unclear)
- "not_found": Field not found in document (set extracted_value to "{NOT_FOUND_VALUE}")

VALIDATION REQUIREMENTS (required for EVERY field):
For each field, you MUST provide a validation object with:
- score: Integer 0-100 (required)
  * 100: Perfect match with template (if provided), complete, correct, and properly formatted
  * 90-99: Excellent quality, minor formatting differences
  * 75-89: Good quality, acceptable with minor issues or deviations
  * 50-74: Acceptable but deviates from template or has moderate issues
  * 25-49: Significant issues, deviations, or quality concerns
  * 0-24: Poor quality, missing critical information, or incorrect format
- status: One of the allowed values below (required)
  * "valid": Field is correct, complete, and properly formatted
  * "warning": Field has minor issues, deviations, or needs attention
  * "invalid": Field has significant problems, incorrect format, or missing required information
  * "not_found": Field not found in document
- notes: String (optional, max 500 chars) with validation insights, deviations from template, recommendations, or explanations

IMPORTANT: You must provide validation for ALL fields, even if the field is "not_found". 
For "not_found" fields: set score to 0, status to "not_found", and notes explaining why it wasn't found.

FIELD-SPECIFIC EXTRACTION GUIDANCE:
Refer to FIELD-SPECIFIC INSTRUCTIONS above for detailed guidance on each field.
Use TEMPLATE REFERENCES (if provided) as examples to guide extraction and determine match_flag values.

IMPORTANT NOTE ON NEGOTIABLE FIELDS:
- For fields marked as "negotiable" in FIELD-SPECIFIC INSTRUCTIONS, the extracted values do NOT need to match the template.
- These fields (e.g., Party A, Party B, Execution Date, Payment Terms, Currency) will naturally vary between contracts.
- When setting match_flag for negotiable fields:
  * Use "same_as_template" only if the STRUCTURE/FORMAT matches (e.g., both use "Net 30 days" format)
  * Use "different_from_template" if the actual VALUES differ (e.g., different party names, different dates, different payment terms)
  * The match_flag should reflect structural similarity, not value similarity for negotiable fields
- For non-negotiable fields (e.g., Limitation of Liability Cap, Warranties), the match_flag should reflect how closely the extracted clause matches the template clause structure and content.

================================================================================
SEARCH GUIDANCE (Organized by Logical Groups)
================================================================================

DOCUMENT-LEVEL INFORMATION:
- Document Type: Check document title/header (typically Page 1)
- Organization Name: Look in preamble/opening party identification (typically Page 1)

PARTY INFORMATION:
- Party A and Party B: Contract header, "Parties" section, or first paragraph
- Authorized Signatories: Signature pages or execution sections (typically last page or last few pages)

DATE INFORMATION:
- Execution Date: Signature pages or execution sections
- Effective Date: May be in header, execution section, or defined relative to Execution Date
- Expiration / Termination Date: Look in termination sections or contract header
- Termination Notice Period: Look in termination sections (e.g., "Section Four – Termination")

COMMERCIAL TERMS:
- Pricing Model Type: Check sections about work orders, rate schedules, or commercial terms (e.g., "Section Three – Work Orders")
- Currency: May appear in any monetary amounts (e.g., insurance limits, payment terms, rate schedules)
- Contract Value: Check Work Orders/SOW references; return "{NOT_FOUND_VALUE}" if not explicitly defined in main agreement
- Billing Frequency, Payment Terms: Sections named "Payment", "Fees", "Compensation", "Commercial Terms", "Financial Terms", or similar
- Expense Reimbursement Rules: Look in expense, travel, or reimbursement sections

LEGAL TERMS:
- Governing Law: Sections named "Governing Law", "Jurisdiction", or "Applicable Law" (e.g., "Section Seventeen – Governing Law")
- Confidentiality Clause Reference: Sections about confidential information (e.g., "Section Eight – Confidential Information")
- Force Majeure Clause Reference: Search for "Force Majeure" explicitly; if absent, return "{NOT_FOUND_VALUE}"
- Indemnification, Limitation of Liability, Insurance: Sections named "Risk", "Liability", "Indemnification", "Insurance", "Warranties", or "General Provisions"

GENERAL SEARCH PRINCIPLES:
- Agreements may have different structures and section names. Search the ENTIRE document thoroughly.
- Information may appear in: main body, signature pages, appendices, exhibits, schedules, or footers/headers.
- Look for information regardless of exact section names - focus on content and context.
- Cross-reference related fields (e.g., Effective Date may be defined relative to Execution Date).

================================================================================
CONTRACT TEXT
================================================================================

MSA TEXT:
\"\"\"{text}\"\"\"
"""
        else:
            # For vision model, text will be extracted from image
            prompt = f"""You are a contract analyst. Extract the following metadata fields from the given Master Service Agreement (MSA) or Non-Disclosure Agreement (NDA) image. Focus on MSA extraction; detect NDA but do not extract NDA-specific fields. Return VALID JSON ONLY matching this schema:

{schema_json}

FIELD DEFINITIONS:
{definitions_text}

FIELD-SPECIFIC INSTRUCTIONS:
{instructions_text}
"""
            
            # Add template references if available
            if template_refs_text:
                prompt += f"""
TEMPLATE REFERENCES (Use as examples for extraction):
{template_refs_text}
"""
            
            prompt += f"""
================================================================================
EXTRACTION RULES
================================================================================

GENERAL RULES:
1. If a field cannot be determined, use "{NOT_FOUND_VALUE}" (never null, empty list, or other placeholders).
2. Each field value must not exceed {MAX_FIELD_LENGTH} characters. If a field would exceed this limit, truncate it appropriately while preserving the most important information.
3. Return no commentary, no extra keys, and no markdown — JSON only.
4. For EACH field in the schema, you MUST provide a complete object with:
   - extracted_value: The actual extracted value (string)
   - match_flag: One of the allowed values below (string)
   - validation: A validation object with score, status, and notes (object)

MATCH FLAG VALUES (choose exactly one per field):
- "same_as_template": Extracted value exactly matches template example (if template provided)
- "similar_not_exact": Extracted value is similar to template but with minor differences (format, wording, slight variations)
- "different_from_template": Extracted value differs significantly from template or uses different approach
- "flag_for_review": Value extracted but needs human review (ambiguous, unusual format, complex scenario, or unclear)
- "not_found": Field not found in document (set extracted_value to "{NOT_FOUND_VALUE}")

VALIDATION REQUIREMENTS (required for EVERY field):
For each field, you MUST provide a validation object with:
- score: Integer 0-100 (required)
  * 100: Perfect match with template (if provided), complete, correct, and properly formatted
  * 90-99: Excellent quality, minor formatting differences
  * 75-89: Good quality, acceptable with minor issues or deviations
  * 50-74: Acceptable but deviates from template or has moderate issues
  * 25-49: Significant issues, deviations, or quality concerns
  * 0-24: Poor quality, missing critical information, or incorrect format
- status: One of the allowed values below (required)
  * "valid": Field is correct, complete, and properly formatted
  * "warning": Field has minor issues, deviations, or needs attention
  * "invalid": Field has significant problems, incorrect format, or missing required information
  * "not_found": Field not found in document
- notes: String (optional, max 500 chars) with validation insights, deviations from template, recommendations, or explanations

IMPORTANT: You must provide validation for ALL fields, even if the field is "not_found". 
For "not_found" fields: set score to 0, status to "not_found", and notes explaining why it wasn't found.

FIELD-SPECIFIC EXTRACTION GUIDANCE:
Refer to FIELD-SPECIFIC INSTRUCTIONS above for detailed guidance on each field.
Use TEMPLATE REFERENCES (if provided) as examples to guide extraction and determine match_flag values.

IMPORTANT NOTE ON NEGOTIABLE FIELDS:
- For fields marked as "negotiable" in FIELD-SPECIFIC INSTRUCTIONS, the extracted values do NOT need to match the template.
- These fields (e.g., Party A, Party B, Execution Date, Payment Terms, Currency) will naturally vary between contracts.
- When setting match_flag for negotiable fields:
  * Use "same_as_template" only if the STRUCTURE/FORMAT matches (e.g., both use "Net 30 days" format)
  * Use "different_from_template" if the actual VALUES differ (e.g., different party names, different dates, different payment terms)
  * The match_flag should reflect structural similarity, not value similarity for negotiable fields
- For non-negotiable fields (e.g., Limitation of Liability Cap, Warranties), the match_flag should reflect how closely the extracted clause matches the template clause structure and content.

================================================================================
SEARCH GUIDANCE (Organized by Logical Groups)
================================================================================

DOCUMENT-LEVEL INFORMATION:
- Document Type: Check document title/header (typically Page 1)
- Organization Name: Look in preamble/opening party identification (typically Page 1)

PARTY INFORMATION:
- Party A and Party B: Contract header, "Parties" section, or first paragraph
- Authorized Signatories: Signature pages or execution sections (typically last page or last few pages)

DATE INFORMATION:
- Execution Date: Signature pages or execution sections
- Effective Date: May be in header, execution section, or defined relative to Execution Date
- Expiration / Termination Date: Look in termination sections or contract header
- Termination Notice Period: Look in termination sections (e.g., "Section Four – Termination")

COMMERCIAL TERMS:
- Pricing Model Type: Check sections about work orders, rate schedules, or commercial terms (e.g., "Section Three – Work Orders")
- Currency: May appear in any monetary amounts (e.g., insurance limits, payment terms, rate schedules)
- Contract Value: Check Work Orders/SOW references; return "{NOT_FOUND_VALUE}" if not explicitly defined in main agreement
- Billing Frequency, Payment Terms: Sections named "Payment", "Fees", "Compensation", "Commercial Terms", "Financial Terms", or similar
- Expense Reimbursement Rules: Look in expense, travel, or reimbursement sections

LEGAL TERMS:
- Governing Law: Sections named "Governing Law", "Jurisdiction", or "Applicable Law" (e.g., "Section Seventeen – Governing Law")
- Confidentiality Clause Reference: Sections about confidential information (e.g., "Section Eight – Confidential Information")
- Force Majeure Clause Reference: Search for "Force Majeure" explicitly; if absent, return "{NOT_FOUND_VALUE}"
- Indemnification, Limitation of Liability, Insurance: Sections named "Risk", "Liability", "Indemnification", "Insurance", "Warranties", or "General Provisions"

GENERAL SEARCH PRINCIPLES:
- Agreements may have different structures and section names. Search the ENTIRE document thoroughly.
- Information may appear in: main body, signature pages, appendices, exhibits, schedules, or footers/headers.
- Look for information regardless of exact section names - focus on content and context.
- Cross-reference related fields (e.g., Effective Date may be defined relative to Execution Date).

Extract all text from the image(s) and analyze it to fill in the schema above.
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
    
    def _build_field_instructions_text(self) -> str:
        """
        Build field-specific instructions text for prompt.
        
        Returns:
            Formatted field instructions string
        """
        lines = []
        
        for category, fields in FIELD_INSTRUCTIONS.items():
            lines.append(f"{category}:")
            for field_name, field_data in fields.items():
                lines.append(f"  - {field_name}:")
                
                # Extract instruction and metadata
                instruction = field_data.get("instruction", "")
                mandatory_field = field_data.get("mandatory_field", "").strip()
                negotiable = field_data.get("negotiable", "").strip()
                expected_position = field_data.get("expected_position", "").strip()
                
                # Add instruction text
                if instruction:
                    instruction_lines = instruction.strip().split('\n')
                    for line in instruction_lines:
                        if line.strip():
                            lines.append(f"    {line.strip()}")
                
                # Add metadata if available
                if mandatory_field or negotiable or expected_position:
                    lines.append("")
                    if mandatory_field:
                        lines.append(f"    Mandatory Field: {mandatory_field}")
                    if negotiable:
                        lines.append(f"    Negotiable: {negotiable}")
                    if expected_position:
                        lines.append(f"    Expected Position: {expected_position}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _build_template_references_text(self) -> str:
        """
        Build template references text for prompt (if available).
        
        Returns:
            Formatted template references string, or empty if not populated
        """
        lines = []
        has_references = False
        
        for category, fields in TEMPLATE_REFERENCES.items():
            category_lines = []
            for field_name, ref_data in fields.items():
                clause_excerpt = ref_data.get("clause_excerpt", "").strip()
                sample_answer = ref_data.get("sample_answer", "").strip()
                clause_name = ref_data.get("clause_name", "").strip()
                
                if clause_excerpt or sample_answer or clause_name:
                    has_references = True
                    category_lines.append(f"  - {field_name}:")
                    if clause_name:
                        category_lines.append(f"    Template Section: {clause_name}")
                    if clause_excerpt:
                        category_lines.append(f"    Template Clause: {clause_excerpt}")
                    if sample_answer:
                        category_lines.append(f"    Sample Answer: {sample_answer}")
            
            if category_lines:
                lines.append(f"{category}:")
                lines.extend(category_lines)
                lines.append("")
        
        if has_references:
            return "\n".join(lines)
        else:
            return ""  # Return empty if no template references populated yet
    
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

