"""
Tests for schema validation and normalization.
"""

import pytest
from ai.schema import SchemaValidator, validate_metadata, normalize_metadata
from config import NOT_FOUND_VALUE


class TestSchemaValidator:
    """Test SchemaValidator class."""
    
    def test_validate_complete_metadata(self):
        """Test validation of complete metadata."""
        validator = SchemaValidator()
        metadata = {
            "Contract Lifecycle": {
                "Execution Date": "2025-03-14",
                "Effective Date": "2025-04-01",
                "Expiration / Termination Date": "2028-03-31",
                "Authorized Signatory": "John Doe"
            },
            "Commercial Operations": {
                "Billing Frequency": "Monthly",
                "Payment Terms": "Net 30",
                "Expense Reimbursement Rules": "As per policy"
            },
            "Risk & Compliance": {
                "Indemnification Clause Reference": "Section 12",
                "Limitation of Liability Cap": "Not to exceed fees",
                "Insurance Requirements": "CGL $2M",
                "Warranties / Disclaimers": "Professional manner"
            }
        }
        
        is_valid, error = validator.validate(metadata)
        assert is_valid is True
        assert error is None
    
    def test_validate_incomplete_metadata(self):
        """Test validation of incomplete metadata."""
        validator = SchemaValidator()
        metadata = {
            "Contract Lifecycle": {
                "Execution Date": "2025-03-14"
                # Missing other fields
            }
        }
        
        is_valid, error = validator.validate(metadata)
        assert is_valid is False
        assert error is not None
    
    def test_normalize_fills_missing_fields(self):
        """Test normalization fills missing fields."""
        validator = SchemaValidator()
        metadata = {
            "Contract Lifecycle": {
                "Execution Date": "2025-03-14"
                # Missing other fields
            }
        }
        
        normalized = validator.normalize(metadata)
        
        # Check that all fields are present
        assert "Contract Lifecycle" in normalized
        assert "Execution Date" in normalized["Contract Lifecycle"]
        assert normalized["Contract Lifecycle"]["Execution Date"] == "2025-03-14"
        
        # Check missing fields are filled
        assert "Effective Date" in normalized["Contract Lifecycle"]
        assert normalized["Contract Lifecycle"]["Effective Date"] == NOT_FOUND_VALUE
    
    def test_normalize_handles_none_values(self):
        """Test normalization handles None values."""
        validator = SchemaValidator()
        metadata = {
            "Contract Lifecycle": {
                "Execution Date": None
            }
        }
        
        normalized = validator.normalize(metadata)
        assert normalized["Contract Lifecycle"]["Execution Date"] == NOT_FOUND_VALUE
    
    def test_get_empty_schema(self):
        """Test getting empty schema."""
        validator = SchemaValidator()
        empty = validator.get_empty_schema()
        
        # Check structure
        assert "Contract Lifecycle" in empty
        assert "Commercial Operations" in empty
        assert "Risk & Compliance" in empty
        
        # Check all fields are NOT_FOUND_VALUE
        for category in empty.values():
            for field_value in category.values():
                assert field_value == NOT_FOUND_VALUE


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_validate_metadata_function(self):
        """Test validate_metadata convenience function."""
        metadata = {
            "Contract Lifecycle": {
                "Execution Date": "2025-03-14",
                "Effective Date": "2025-04-01",
                "Expiration / Termination Date": "2028-03-31",
                "Authorized Signatory": "John Doe"
            },
            "Commercial Operations": {
                "Billing Frequency": "Monthly",
                "Payment Terms": "Net 30",
                "Expense Reimbursement Rules": "As per policy"
            },
            "Risk & Compliance": {
                "Indemnification Clause Reference": "Section 12",
                "Limitation of Liability Cap": "Not to exceed fees",
                "Insurance Requirements": "CGL $2M",
                "Warranties / Disclaimers": "Professional manner"
            }
        }
        
        is_valid, error = validate_metadata(metadata)
        assert is_valid is True
    
    def test_normalize_metadata_function(self):
        """Test normalize_metadata convenience function."""
        metadata = {
            "Contract Lifecycle": {
                "Execution Date": "2025-03-14"
            }
        }
        
        normalized = normalize_metadata(metadata)
        assert "Effective Date" in normalized["Contract Lifecycle"]
        assert normalized["Contract Lifecycle"]["Effective Date"] == NOT_FOUND_VALUE

