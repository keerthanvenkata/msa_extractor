"""
Pytest configuration and fixtures for MSA Metadata Extractor tests.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "scratch"


@pytest.fixture
def sample_pdf_path():
    """Return path to a sample PDF file."""
    # Use a small PDF for testing
    pdf_files = [
        "Adaequare Inc._Orbit Inc._MSA.pdf",
        "Executed Subcontracting Agreement_Adaequare Inc_DISYS_07222020.pdf_R1407[5-24-2021]",
    ]
    
    for pdf_file in pdf_files:
        pdf_path = TEST_DATA_DIR / pdf_file
        if pdf_path.exists():
            return str(pdf_path)
    
    pytest.skip("No sample PDF files found in scratch directory")


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client for testing."""
    mock_client = Mock()
    mock_client.extract_metadata_from_text = Mock(return_value={
        "Contract Lifecycle": {
            "Execution Date": "2025-03-14",
            "Effective Date": "2025-04-01",
            "Expiration / Termination Date": "2028-03-31",
            "Authorized Signatory": "John Doe, VP of Operations"
        },
        "Commercial Operations": {
            "Billing Frequency": "Monthly",
            "Payment Terms": "Net 30 days from invoice date",
            "Expense Reimbursement Rules": "Reimbursed as per client travel policy"
        },
        "Risk & Compliance": {
            "Indemnification Clause Reference": "Section 12 – Indemnification",
            "Limitation of Liability Cap": "Aggregate liability not to exceed fees paid in previous 12 months",
            "Insurance Requirements": "CGL $2M per occurrence; Workers Comp as per law",
            "Warranties / Disclaimers": "Services to be performed in a professional manner"
        }
    })
    mock_client.schema_validator = Mock()
    mock_client.schema_validator.validate = Mock(return_value=(True, None))
    mock_client.schema_validator.normalize = Mock(side_effect=lambda x: x)
    return mock_client


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir

