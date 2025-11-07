"""
JSON schema validation for MSA metadata extraction.

Defines the canonical schema and provides validation utilities.
"""

import json
import jsonschema
from typing import Dict, Any, Optional
import logging

from config import METADATA_SCHEMA, NOT_FOUND_VALUE

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validate extracted metadata against the canonical schema."""
    
    def __init__(self):
        """Initialize schema validator."""
        self.schema = self._build_json_schema()
        self.logger = logging.getLogger(self.__class__.__name__)
    
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
    
    Args:
        metadata: Metadata dictionary to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = SchemaValidator()
    return validator.validate(metadata)


def normalize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize metadata to match schema.
    
    Convenience function for quick normalization.
    
    Args:
        metadata: Metadata dictionary to normalize
    
    Returns:
        Normalized metadata dictionary
    """
    validator = SchemaValidator()
    return validator.normalize(metadata)

