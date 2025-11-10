"""
Gemini API client for text and vision processing.

Handles both text-based LLM calls and vision model calls for metadata extraction.
"""

import json
from typing import Dict, Any, Optional, List
import google.generativeai as genai

from config import (
    GEMINI_API_KEY,
    GEMINI_TEXT_MODEL,
    GEMINI_VISION_MODEL,
    METADATA_SCHEMA,
    FIELD_DEFINITIONS,
    NOT_FOUND_VALUE,
    MAX_TEXT_LENGTH
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
            # Call Gemini API
            response = self.text_model.generate_content(prompt)
            
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
            # Call Gemini Vision API
            response = self.vision_model.generate_content([
                prompt,
                {
                    "mime_type": image_mime_type,
                    "data": image_bytes
                }
            ])
            
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
4. For "Indemnification Clause Reference":
   - Return the section heading/number and a 1–2 sentence excerpt
   - Example: "Section 12 – Indemnification: Each party agrees to indemnify..."
5. For fields with multiple values (e.g., multiple signatories):
   - Combine with semicolons
   - Example: "John Doe, VP of Operations; Jane Smith, CFO"
6. Return no commentary, no extra keys, and no markdown — JSON only.

SEARCH GUIDANCE:
- Agreements may have different structures and section names. Search the ENTIRE document thoroughly.
- Information may appear in: main body, signature pages, appendices, exhibits, schedules, or footers/headers.
- Execution Date and Authorized Signatory are often on signature pages (typically last page or last few pages).
- Payment Terms, Billing Frequency may be in sections named: "Payment", "Fees", "Compensation", "Commercial Terms", "Financial Terms", or similar.
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
4. For "Indemnification Clause Reference":
   - Return the section heading/number and a 1–2 sentence excerpt
   - Example: "Section 12 – Indemnification: Each party agrees to indemnify..."
5. For fields with multiple values (e.g., multiple signatories):
   - Combine with semicolons
   - Example: "John Doe, VP of Operations; Jane Smith, CFO"
6. Return no commentary, no extra keys, and no markdown — JSON only.

SEARCH GUIDANCE:
- Agreements may have different structures and section names. Search the ENTIRE document thoroughly.
- Information may appear in: main body, signature pages, appendices, exhibits, schedules, or footers/headers.
- Execution Date and Authorized Signatory are often on signature pages (typically last page or last few pages).
- Payment Terms, Billing Frequency may be in sections named: "Payment", "Fees", "Compensation", "Commercial Terms", "Financial Terms", or similar.
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

