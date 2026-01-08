"""
JSON schema validation for MSA metadata extraction.

Defines the canonical schema and provides validation utilities.
"""

import json
import jsonschema
from typing import Dict, Any, Optional

from config import (
    METADATA_SCHEMA, 
    NOT_FOUND_VALUE, 
    MAX_FIELD_LENGTH,
    MATCH_FLAG_VALUES,
    VALIDATION_STATUS_VALUES
)
from utils.logger import get_logger
from utils.exceptions import ValidationError

logger = get_logger(__name__)

# Module-level singleton instance for convenience functions
_shared_validator = None


def _get_shared_validator():
    """Get or create shared SchemaValidator instance."""
    global _shared_validator
    if _shared_validator is None:
        _shared_validator = SchemaValidator()
    return _shared_validator


class SchemaValidator:
    """Validate extracted metadata against the canonical schema."""
    
    def __init__(self):
        """Initialize schema validator."""
        self.schema = self._build_json_schema()
        self.logger = get_logger(self.__class__.__module__)
    
    def _build_json_schema(self) -> Dict[str, Any]:
        """
        Build JSON Schema from METADATA_SCHEMA structure.
        
        Returns:
            JSON Schema dictionary
        """
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for category, fields in METADATA_SCHEMA.items():
            schema["properties"][category] = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for field_name, field_structure in fields.items():
                # Check if field is enhanced structure (dict) or legacy (string)
                if isinstance(field_structure, dict):
                    # Enhanced structure with extracted_value, match_flag, validation
                    schema["properties"][category]["properties"][field_name] = {
                        "type": "object",
                        "properties": {
                            "extracted_value": {
                                "type": "string",
                                "maxLength": MAX_FIELD_LENGTH
                            },
                            "match_flag": {
                                "type": "string",
                                "enum": MATCH_FLAG_VALUES
                            },
                            "validation": {
                                "type": "object",
                                "properties": {
                                    "score": {
                                        "type": "integer",
                                        "minimum": 0,
                                        "maximum": 100
                                    },
                                    "status": {
                                        "type": "string",
                                        "enum": VALIDATION_STATUS_VALUES
                                    },
                                    "notes": {
                                        "type": "string",
                                        "maxLength": 500
                                    }
                                },
                                "required": ["score", "status"]
                            }
                        },
                        "required": ["extracted_value", "match_flag", "validation"]
                    }
                else:
                    # Legacy structure (string) - for backward compatibility
                    schema["properties"][category]["properties"][field_name] = {
                        "type": "string",
                        "maxLength": MAX_FIELD_LENGTH
                    }
                schema["properties"][category]["required"].append(field_name)
        
        return schema
    
    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate data against schema.
        
        Args:
            data: Dictionary to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            jsonschema.validate(instance=data, schema=self.schema)
            return True, None
        except jsonschema.ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize data to match schema structure.
        
        Fills missing fields with NOT_FOUND_VALUE and ensures structure matches.
        Handles both enhanced structure (with match_flag, validation) and legacy structure.
        
        Args:
            data: Dictionary to normalize
        
        Returns:
            Normalized dictionary matching schema
        """
        normalized = {}
        
        for category, fields in METADATA_SCHEMA.items():
            normalized[category] = {}
            
            for field_name, field_structure in fields.items():
                # Check if field is enhanced structure (dict) or legacy (string)
                if isinstance(field_structure, dict):
                    # Enhanced structure with extracted_value, match_flag, validation
                    field_data = data.get(category, {}).get(field_name, {})
                    
                    # Get extracted_value
                    if isinstance(field_data, dict):
                        extracted_value = field_data.get("extracted_value", NOT_FOUND_VALUE)
                        match_flag = field_data.get("match_flag", "not_found")
                        validation = field_data.get("validation", {})
                    else:
                        # Legacy format: just a string value
                        extracted_value = field_data if field_data else NOT_FOUND_VALUE
                        match_flag = "not_found" if extracted_value == NOT_FOUND_VALUE else "flag_for_review"
                        validation = {}
                    
                    # Ensure extracted_value is a string
                    if extracted_value is None:
                        extracted_value = NOT_FOUND_VALUE
                    elif not isinstance(extracted_value, str):
                        extracted_value = str(extracted_value)
                    
                    # Truncate if exceeds MAX_FIELD_LENGTH (with warning)
                    if extracted_value != NOT_FOUND_VALUE and len(extracted_value) > MAX_FIELD_LENGTH:
                        original_length = len(extracted_value)
                        extracted_value = extracted_value[:MAX_FIELD_LENGTH]
                        self.logger.warning(
                            f"Field '{category}.{field_name}' exceeded MAX_FIELD_LENGTH ({MAX_FIELD_LENGTH} chars). "
                            f"Truncated from {original_length} to {MAX_FIELD_LENGTH} characters."
                        )
                    
                    # Validate match_flag
                    if match_flag not in MATCH_FLAG_VALUES:
                        match_flag = "not_found"
                    
                    # Normalize validation
                    validation_score = validation.get("score", 0) if isinstance(validation, dict) else 0
                    validation_status = validation.get("status", "not_found") if isinstance(validation, dict) else "not_found"
                    validation_notes = validation.get("notes", "") if isinstance(validation, dict) else ""
                    
                    # Validate status
                    if validation_status not in VALIDATION_STATUS_VALUES:
                        validation_status = "not_found"
                    
                    # Ensure score is in range
                    validation_score = max(0, min(100, int(validation_score)))
                    
                    # Truncate notes if needed
                    if len(validation_notes) > 500:
                        validation_notes = validation_notes[:500]
                    
                    normalized[category][field_name] = {
                        "extracted_value": extracted_value,
                        "match_flag": match_flag,
                        "validation": {
                            "score": validation_score,
                            "status": validation_status,
                            "notes": validation_notes
                        }
                    }
                else:
                    # Legacy structure (string) - for backward compatibility
                    value = data.get(category, {}).get(field_name, NOT_FOUND_VALUE)
                    
                    # Ensure it's a string
                    if value is None:
                        value = NOT_FOUND_VALUE
                    elif not isinstance(value, str):
                        value = str(value)
                    
                    # Truncate if exceeds MAX_FIELD_LENGTH (with warning)
                    if value != NOT_FOUND_VALUE and len(value) > MAX_FIELD_LENGTH:
                        original_length = len(value)
                        value = value[:MAX_FIELD_LENGTH]
                        self.logger.warning(
                            f"Field '{category}.{field_name}' exceeded MAX_FIELD_LENGTH ({MAX_FIELD_LENGTH} chars). "
                            f"Truncated from {original_length} to {MAX_FIELD_LENGTH} characters."
                        )
                    
                    normalized[category][field_name] = value
        
        return normalized
    
    def get_empty_schema(self) -> Dict[str, Any]:
        """
        Get empty schema structure with all fields set to NOT_FOUND_VALUE.
        
        Returns:
            Empty schema dictionary
        """
        return self.normalize({})


def validate_metadata(metadata: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate metadata against schema.
    
    Convenience function for quick validation.
    Reuses shared SchemaValidator instance for performance.
    
    Args:
        metadata: Metadata dictionary to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = _get_shared_validator()
    return validator.validate(metadata)


def normalize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize metadata to match schema.
    
    Convenience function for quick normalization.
    Reuses shared SchemaValidator instance for performance.
    
    Args:
        metadata: Metadata dictionary to normalize
    
    Returns:
        Normalized metadata dictionary
    """
    validator = _get_shared_validator()
    return validator.normalize(metadata)

