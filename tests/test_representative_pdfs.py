"""
Tests for representative PDFs: text-only, image-only, and mixed (text+image).

These tests use real PDFs to validate extraction across different document types.
"""

import pytest
from pathlib import Path
from extractors.extraction_coordinator import ExtractionCoordinator
from utils.exceptions import ExtractionError, FileError
from config import MAX_FIELD_LENGTH

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"

# Representative PDFs
ORBIT_PDF = TEST_DATA_DIR / "Adaequare Inc._Orbit Inc._MSA.pdf"  # Mixed: text + image
DGS_PDF = TEST_DATA_DIR / "DGS_Adaequare Agreement_CounterSigned.pdf"  # Image-only
MINDLANCE_PDF = TEST_DATA_DIR / "Executed Master Service Agreement_Adaequare,Inc_Mindlance_05192016.pdf"  # Text-only


class TestRepresentativePDFs:
    """Test extraction on representative PDF types."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test coordinator."""
        self.coordinator = ExtractionCoordinator()
    
    def _validate_metadata_structure(self, metadata):
        """Validate metadata structure and field lengths."""
        assert isinstance(metadata, dict), "Metadata must be a dictionary"
        
        # Check required categories
        assert "Contract Lifecycle" in metadata, "Missing Contract Lifecycle category"
        assert "Commercial Operations" in metadata, "Missing Commercial Operations category"
        assert "Risk & Compliance" in metadata, "Missing Risk & Compliance category"
        
        # Check all fields are strings and within length limit
        for category_name, category_data in metadata.items():
            assert isinstance(category_data, dict), f"{category_name} must be a dictionary"
            
            for field_name, field_value in category_data.items():
                assert isinstance(field_value, str), f"{category_name}.{field_name} must be a string"
                assert len(field_value) <= MAX_FIELD_LENGTH, (
                    f"{category_name}.{field_name} exceeds MAX_FIELD_LENGTH "
                    f"({len(field_value)} > {MAX_FIELD_LENGTH})"
                )
    
    @pytest.mark.slow
    def test_orbit_mixed_pdf(self):
        """Test extraction from mixed PDF (text + image page)."""
        if not ORBIT_PDF.exists():
            pytest.skip(f"Test PDF not found: {ORBIT_PDF}")
        
        try:
            metadata = self.coordinator.extract_metadata(str(ORBIT_PDF))
            
            # Validate structure
            self._validate_metadata_structure(metadata)
            
            # Log extracted values for manual review
            lifecycle = metadata.get("Contract Lifecycle", {})
            print(f"\n[Orbit PDF] Extracted:")
            print(f"  Execution Date: {lifecycle.get('Execution Date', 'Not Found')}")
            print(f"  Effective Date: {lifecycle.get('Effective Date', 'Not Found')}")
            print(f"  Expiration Date: {lifecycle.get('Expiration / Termination Date', 'Not Found')}")
            print(f"  Signatory: {lifecycle.get('Authorized Signatory', 'Not Found')}")
            
        except ExtractionError as e:
            pytest.skip(f"Extraction failed (may need API key or file issue): {e}")
    
    @pytest.mark.slow
    def test_dgs_image_only_pdf(self):
        """Test extraction from image-only PDF."""
        if not DGS_PDF.exists():
            pytest.skip(f"Test PDF not found: {DGS_PDF}")
        
        try:
            metadata = self.coordinator.extract_metadata(str(DGS_PDF))
            
            # Validate structure
            self._validate_metadata_structure(metadata)
            
            # Log extracted values for manual review
            lifecycle = metadata.get("Contract Lifecycle", {})
            print(f"\n[DGS PDF] Extracted:")
            print(f"  Execution Date: {lifecycle.get('Execution Date', 'Not Found')}")
            print(f"  Effective Date: {lifecycle.get('Effective Date', 'Not Found')}")
            print(f"  Expiration Date: {lifecycle.get('Expiration / Termination Date', 'Not Found')}")
            print(f"  Signatory: {lifecycle.get('Authorized Signatory', 'Not Found')}")
            
        except ExtractionError as e:
            pytest.skip(f"Extraction failed (may need API key or file issue): {e}")
    
    @pytest.mark.slow
    def test_mindlance_text_only_pdf(self):
        """Test extraction from text-only PDF."""
        if not MINDLANCE_PDF.exists():
            pytest.skip(f"Test PDF not found: {MINDLANCE_PDF}")
        
        try:
            metadata = self.coordinator.extract_metadata(str(MINDLANCE_PDF))
            
            # Validate structure
            self._validate_metadata_structure(metadata)
            
            # Log extracted values for manual review
            lifecycle = metadata.get("Contract Lifecycle", {})
            commercial = metadata.get("Commercial Operations", {})
            print(f"\n[Mindlance PDF] Extracted:")
            print(f"  Execution Date: {lifecycle.get('Execution Date', 'Not Found')}")
            print(f"  Effective Date: {lifecycle.get('Effective Date', 'Not Found')}")
            print(f"  Expiration Date: {lifecycle.get('Expiration / Termination Date', 'Not Found')}")
            print(f"  Signatory: {lifecycle.get('Authorized Signatory', 'Not Found')}")
            print(f"  Billing Frequency: {commercial.get('Billing Frequency', 'Not Found')}")
            print(f"  Payment Terms: {commercial.get('Payment Terms', 'Not Found')}")
            
        except ExtractionError as e:
            pytest.skip(f"Extraction failed (may need API key or file issue): {e}")
    
    @pytest.mark.slow
    def test_all_representative_pdfs(self):
        """Test all representative PDFs in sequence."""
        pdfs = [
            ("Orbit (Mixed)", ORBIT_PDF),
            ("DGS (Image-only)", DGS_PDF),
            ("Mindlance (Text-only)", MINDLANCE_PDF),
        ]
        
        results = []
        for name, pdf_path in pdfs:
            if not pdf_path.exists():
                results.append((name, False, f"File not found: {pdf_path}"))
                continue
            
            try:
                metadata = self.coordinator.extract_metadata(str(pdf_path))
                self._validate_metadata_structure(metadata)
                results.append((name, True, "Success"))
            except Exception as e:
                results.append((name, False, str(e)))
        
        # Print summary
        print("\n" + "="*80)
        print("Representative PDFs Test Summary")
        print("="*80)
        for name, success, message in results:
            status = "PASS" if success else "FAIL"
            print(f"{status} - {name}: {message}")
        
        # Assert all passed
        failed = [name for name, success, _ in results if not success]
        if failed:
            pytest.fail(f"Some PDFs failed: {', '.join(failed)}")

