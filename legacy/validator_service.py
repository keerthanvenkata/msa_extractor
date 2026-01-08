"""
DEPRECATED: Validation service for MSA metadata extraction.

This service is deprecated. Validation is now integrated directly into the extraction
process via the GeminiClient. The LLM now returns validation scores, match flags, and
notes as part of the extraction response.

This file is kept for reference only and should not be used in new code.
Validation is handled in ai/gemini_client.py as part of the extraction prompt.

Validates extracted metadata against industry-standard templates and examples.
Adds validation scores, flags, and additional insights to the extracted metadata.
"""

from typing import Dict, Any, Optional, List
import json

from ai.gemini_client import GeminiClient
from config import METADATA_SCHEMA, NOT_FOUND_VALUE
from utils.logger import get_logger
from utils.exceptions import LLMError

logger = get_logger(__name__)


class ValidatorService:
    """
    Service for validating extracted metadata against templates and examples.
    
    Uses a separate LLM call to:
    1. Compare extracted fields against standard templates/examples
    2. Add validation scores and flags
    3. Add additional insights and recommendations
    4. Identify negotiable vs compulsory fields
    5. Flag acceptable deviations
    """
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize validator service.
        
        Args:
            gemini_client: Gemini client instance (creates new if not provided)
        """
        self.gemini_client = gemini_client or GeminiClient()
        self.logger = get_logger(self.__class__.__module__)
        # TODO: Load validation templates/examples from config
        self.validation_templates = self._load_validation_templates()
    
    def validate_metadata(
        self, 
        extracted_metadata: Dict[str, Any],
        original_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate extracted metadata and add validation results.
        
        Args:
            extracted_metadata: Extracted metadata from initial extraction
            original_text: Original contract text (optional, for context)
        
        Returns:
            Enhanced metadata dictionary with validation results added:
            - Original extracted fields (preserved)
            - Validation scores per field/category
            - Validation flags (e.g., "missing_required", "deviates_from_standard")
            - Additional insights and recommendations
            - Negotiability indicators
        """
        self.logger.info("Starting metadata validation")
        
        try:
            # Build validation prompt
            prompt = self._build_validation_prompt(extracted_metadata, original_text)
            
            # Call LLM for validation
            response = self.gemini_client._call_with_retry(
                lambda: self.gemini_client.text_model.generate_content(prompt),
                operation="validate_metadata"
            )
            
            # Parse validation results
            validation_results = self._parse_validation_response(response.text)
            
            # Merge validation results with extracted metadata
            enhanced_metadata = self._merge_validation_results(
                extracted_metadata, 
                validation_results
            )
            
            self.logger.info("Metadata validation completed")
            return enhanced_metadata
            
        except LLMError:
            # Re-raise LLM errors
            raise
        except Exception as e:
            self.logger.error("Error validating metadata", exc_info=True)
            # Return original metadata with error flag if validation fails
            return self._add_validation_error(extracted_metadata, str(e))
    
    def _load_validation_templates(self) -> Dict[str, Any]:
        """
        Load validation templates and examples.
        
        TODO: Load from config file or database
        Each template should include:
        - Example value from standard template
        - What to look for
        - Whether field is negotiable or compulsory
        - Acceptable deviations
        - Scoring criteria
        
        Returns:
            Dictionary of validation templates by field/category
        """
        # Placeholder - will be populated from config
        return {
            # Example structure:
            # "Contract Lifecycle": {
            #     "Execution Date": {
            #         "example": "2025-03-14",
            #         "description": "ISO format date when contract was signed",
            #         "negotiable": False,
            #         "compulsory": True,
            #         "acceptable_deviations": ["AmbiguousDate flag acceptable"],
            #         "scoring_criteria": "Present and valid format = 100, Missing = 0"
            #     },
            #     ...
            # }
        }
    
    def _build_validation_prompt(
        self, 
        extracted_metadata: Dict[str, Any],
        original_text: Optional[str] = None
    ) -> str:
        """
        Build validation prompt for LLM.
        
        Args:
            extracted_metadata: Extracted metadata to validate
            original_text: Original contract text (optional)
        
        Returns:
            Formatted prompt string
        """
        metadata_json = json.dumps(extracted_metadata, indent=2)
        templates_json = json.dumps(self.validation_templates, indent=2)
        
        prompt = f"""You are a contract validation expert. Validate the extracted metadata against industry-standard templates and examples.

EXTRACTED METADATA:
{metadata_json}

VALIDATION TEMPLATES & EXAMPLES:
{templates_json}

VALIDATION TASKS:
1. Compare each extracted field against the template examples
2. Score each field (0-100) based on:
   - Presence and completeness
   - Format correctness
   - Alignment with standard templates
   - Acceptable deviations
3. Add flags for:
   - Missing required/compulsory fields
   - Deviations from standard templates
   - Negotiable fields that may need attention
   - Fields that exceed acceptable deviations
4. Provide insights and recommendations for each category
5. Identify which fields are negotiable vs compulsory

OUTPUT FORMAT (JSON):
{{
  "validation_summary": {{
    "overall_score": 85,
    "total_fields": 22,
    "validated_fields": 20,
    "missing_required": 2,
    "deviations": 3
  }},
  "field_validations": {{
    "Contract Lifecycle": {{
      "Execution Date": {{
        "score": 100,
        "status": "valid",
        "flags": [],
        "deviation": null,
        "negotiable": false,
        "compulsory": true,
        "insights": "Date format is correct and present"
      }},
      ...
    }}
  }},
  "category_scores": {{
    "Contract Lifecycle": 95,
    "Commercial Operations": 80,
    ...
  }},
  "recommendations": [
    "Missing Termination Notice Period - should be included",
    "Payment Terms deviate from standard - review recommended"
  ]
}}

Return VALID JSON ONLY, no markdown or commentary.
"""
        
        if original_text:
            prompt += f"\n\nORIGINAL CONTRACT TEXT (for context):\n{original_text[:5000]}"
        
        return prompt
    
    def _parse_validation_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse validation response from LLM.
        
        Args:
            response_text: Raw response text from LLM
        
        Returns:
            Parsed validation results dictionary
        """
        # Remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
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
                "Failed to parse validation response from LLM",
                exc_info=True,
                extra={"response_preview": response_text[:500]}
            )
            # Return empty validation structure on parse error
            return self._get_empty_validation_results()
    
    def _merge_validation_results(
        self,
        extracted_metadata: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge validation results with extracted metadata.
        
        Args:
            extracted_metadata: Original extracted metadata
            validation_results: Validation results from LLM
        
        Returns:
            Enhanced metadata with validation results added
        """
        enhanced = {
            "metadata": extracted_metadata,  # Preserve original
            "validation": validation_results  # Add validation layer
        }
        
        return enhanced
    
    def _get_empty_validation_results(self) -> Dict[str, Any]:
        """
        Get empty validation results structure.
        
        Returns:
            Empty validation results dictionary
        """
        return {
            "validation_summary": {
                "overall_score": 0,
                "total_fields": 0,
                "validated_fields": 0,
                "missing_required": 0,
                "deviations": 0,
                "error": "Validation failed to parse"
            },
            "field_validations": {},
            "category_scores": {},
            "recommendations": []
        }
    
    def _add_validation_error(
        self,
        extracted_metadata: Dict[str, Any],
        error_message: str
    ) -> Dict[str, Any]:
        """
        Add validation error to metadata.
        
        Args:
            extracted_metadata: Original extracted metadata
            error_message: Error message
        
        Returns:
            Metadata with error flag in validation section
        """
        return {
            "metadata": extracted_metadata,
            "validation": {
                "validation_summary": {
                    "overall_score": 0,
                    "error": error_message,
                    "validation_failed": True
                },
                "field_validations": {},
                "category_scores": {},
                "recommendations": []
            }
        }

