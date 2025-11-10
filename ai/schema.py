"""
JSON schema validation for MSA metadata extraction.

Defines the canonical schema and provides validation utilities.
"""

import json
import jsonschema
from typing import Dict, Any, Optional

from config import METADATA_SCHEMA, NOT_FOUND_VALUE
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
            
            for field_name in fields.keys():
                schema["properties"][category]["properties"][field_name] = {
                    "type": "string"
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
        
        Args:
            data: Dictionary to normalize
        
        Returns:
            Normalized dictionary matching schema
        """
        normalized = {}
        
        for category, fields in METADATA_SCHEMA.items():
            normalized[category] = {}
            
            for field_name in fields.keys():
                # Get value from data if present
                value = data.get(category, {}).get(field_name, NOT_FOUND_VALUE)
                
                # Ensure it's a string
                if value is None:
                    value = NOT_FOUND_VALUE
                elif not isinstance(value, str):
                    value = str(value)
                
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

