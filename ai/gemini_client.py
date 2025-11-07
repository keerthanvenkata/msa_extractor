"""
Gemini API client for text and vision processing.

Handles both text-based LLM calls and vision model calls for metadata extraction.
"""

import json
import logging
from typing import Dict, Any, Optional, List
import google.generativeai as genai

from config import (
    GEMINI_API_KEY,
    GEMINI_TEXT_MODEL,
    GEMINI_VISION_MODEL,
    METADATA_SCHEMA,
    NOT_FOUND_VALUE,
    MAX_TEXT_LENGTH
)
from .schema import SchemaValidator

logger = logging.getLogger(__name__)


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
            raise ValueError("GEMINI_API_KEY not set in environment or config")
        
        genai.configure(api_key=self.api_key)
        self.text_model = genai.GenerativeModel(GEMINI_TEXT_MODEL)
        self.vision_model = genai.GenerativeModel(GEMINI_VISION_MODEL)
        self.schema_validator = SchemaValidator()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_metadata_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract metadata from text using Gemini text model.
        
        Args:
            text: Contract text to analyze
        
        Returns:
            Dictionary with extracted metadata matching schema
        """
        # Truncate text if too long
        if len(text) > MAX_TEXT_LENGTH:
            self.logger.warning(
                f"Text length ({len(text)}) exceeds MAX_TEXT_LENGTH ({MAX_TEXT_LENGTH}). "
                "Truncating text."
            )
            text = text[:MAX_TEXT_LENGTH]
        
        # Build prompt
        prompt = self._build_extraction_prompt(text)
        
        try:
            # Call Gemini API
            response = self.text_model.generate_content(prompt)
            
            # Parse JSON response
            metadata = self._parse_json_response(response.text)
            
            # Normalize to schema
            metadata = self.schema_validator.normalize(metadata)
            
            # Validate
            is_valid, error = self.schema_validator.validate(metadata)
            if not is_valid:
                self.logger.warning(f"Schema validation failed: {error}")
                # Return normalized data anyway (it will have correct structure)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata: {e}")
            # Return empty schema on error
            return self.schema_validator.get_empty_schema()
    
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
            
            # Normalize to schema
            metadata = self.schema_validator.normalize(metadata)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata from image: {e}")
            return self.schema_validator.get_empty_schema()
    
    def _build_extraction_prompt(self, text: str) -> str:
        """
        Build extraction prompt following PROMPT.md template.
        
        Args:
            text: Contract text (empty for vision model)
        
        Returns:
            Formatted prompt string
        """
        schema_json = json.dumps(METADATA_SCHEMA, indent=2)
        
        if text:
            prompt = f"""You are a contract analyst. Extract the following metadata fields from the given Master Service Agreement and return VALID JSON ONLY matching this schema:

{schema_json}

Rules:
1. If a field cannot be determined, use "{NOT_FOUND_VALUE}".
2. For dates, attempt ISO yyyy-mm-dd; if ambiguous, return the text found and include "AmbiguousDate" as a flag (in the result value).
3. For clause references, return the section heading/number and a 1–2 sentence excerpt.
4. Return no commentary, no extra keys, and no markdown — JSON only.

MSA TEXT:
\"\"\"{text}\"\"\"
"""
        else:
            # For vision model, text will be extracted from image
            prompt = f"""You are a contract analyst. Extract the following metadata fields from the given Master Service Agreement image and return VALID JSON ONLY matching this schema:

{schema_json}

Rules:
1. If a field cannot be determined, use "{NOT_FOUND_VALUE}".
2. For dates, attempt ISO yyyy-mm-dd; if ambiguous, return the text found and include "AmbiguousDate" as a flag (in the result value).
3. For clause references, return the section heading/number and a 1–2 sentence excerpt.
4. Return no commentary, no extra keys, and no markdown — JSON only.

Extract all text from the image and analyze it to fill in the schema above.
"""
        
        return prompt
    
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
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.debug(f"Response text: {response_text[:500]}")
            # Return empty schema on parse error
            return self.schema_validator.get_empty_schema()

