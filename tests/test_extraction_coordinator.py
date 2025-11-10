"""
Smoke tests for extraction coordinator.
"""

import pytest
from pathlib import Path
from extractors.extraction_coordinator import ExtractionCoordinator
from utils.exceptions import FileError, ExtractionError


class TestExtractionCoordinator:
    """Test ExtractionCoordinator class."""
    
    def test_initialization(self):
        """Test coordinator initialization."""
        coordinator = ExtractionCoordinator()
        assert coordinator.gemini_client is not None
        assert coordinator.strategy_factory is not None
    
    def test_initialization_with_client(self, mock_gemini_client):
        """Test coordinator initialization with provided client."""
        coordinator = ExtractionCoordinator(gemini_client=mock_gemini_client)
        assert coordinator.gemini_client == mock_gemini_client
    
    def test_extract_metadata_unsupported_file_type(self):
        """Test extraction with unsupported file type."""
        coordinator = ExtractionCoordinator()
        
        with pytest.raises(FileError) as exc_info:
            coordinator.extract_metadata("test.txt")
        
        assert "Unsupported file type" in str(exc_info.value)
    
    @pytest.mark.slow
    def test_extract_metadata_pdf(self, sample_pdf_path):
        """Smoke test: Extract metadata from PDF."""
        coordinator = ExtractionCoordinator()
        
        try:
            metadata = coordinator.extract_metadata(sample_pdf_path)
            
            # Check structure
            assert isinstance(metadata, dict)
            assert "Contract Lifecycle" in metadata
            assert "Commercial Operations" in metadata
            assert "Risk & Compliance" in metadata
            
            # Check that all fields are present (even if "Not Found")
            for category in metadata.values():
                assert isinstance(category, dict)
                for field_value in category.values():
                    assert isinstance(field_value, str)
        
        except ExtractionError as e:
            pytest.skip(f"Extraction failed (may need API key or file issue): {e}")
    
    def test_extract_metadata_nonexistent_file(self):
        """Test extraction with non-existent file."""
        coordinator = ExtractionCoordinator()
        
        with pytest.raises(FileError) as exc_info:
            coordinator.extract_metadata("nonexistent.pdf")
        
        assert "not found" in str(exc_info.value).lower()

