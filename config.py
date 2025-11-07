"""
Configuration module for MSA Metadata Extractor.

Handles environment variable loading, API keys, model selection,
and other configuration constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# API Configuration
# ============================================================================

# Gemini API Key (required)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Gemini Model Selection (default: gemini-pro)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

# ============================================================================
# File Paths
# ============================================================================

# Base directory (project root)
BASE_DIR = Path(__file__).parent

# Output directory for results
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "results"))
OUTPUT_DIR.mkdir(exist_ok=True)

# Database path
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "msa_extractor.db"))

# Contracts directory (for batch processing)
CONTRACTS_DIR = BASE_DIR / "contracts"
CONTRACTS_DIR.mkdir(exist_ok=True)

# ============================================================================
# Logging Configuration
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================================================
# Schema Constants
# ============================================================================

# JSON Schema structure (as defined in docs/REQUIREMENTS.md)
# See docs/REQUIREMENTS.md for field definitions, examples, and update checklist
METADATA_SCHEMA = {
    "Contract Lifecycle": {
        "Execution Date": "",
        "Effective Date": "",
        "Expiration / Termination Date": "",
        "Authorized Signatory": ""
    },
    "Commercial Operations": {
        "Billing Frequency": "",
        "Payment Terms": "",
        "Expense Reimbursement Rules": ""
    },
    "Risk & Compliance": {
        "Indemnification Clause Reference": "",
        "Limitation of Liability Cap": "",
        "Insurance Requirements": "",
        "Warranties / Disclaimers": ""
    }
}

# Field definitions for LLM prompts (from docs/REQUIREMENTS.md)
FIELD_DEFINITIONS = {
    "Contract Lifecycle": {
        "Execution Date": "Date when both parties have signed the agreement. Format: ISO yyyy-mm-dd (e.g., 2025-03-14)",
        "Effective Date": "Date the MSA becomes legally effective (may differ from execution). Format: ISO yyyy-mm-dd (e.g., 2025-04-01)",
        "Expiration / Termination Date": "Date on which the agreement expires or terminates unless renewed. Format: ISO yyyy-mm-dd or 'Evergreen' if auto-renews (e.g., 2028-03-31 or Evergreen)",
        "Authorized Signatory": "Name and designation of the individual authorized to sign on behalf of each party. Format: Full name and title (e.g., John Doe, VP of Operations). If multiple, separate with semicolons."
    },
    "Commercial Operations": {
        "Billing Frequency": "How often invoices are issued under the MSA. Examples: Monthly, Quarterly, Milestone-based, As-invoiced",
        "Payment Terms": "Time allowed for payment after invoice submission. Format: Terms as stated (e.g., Net 30 days from invoice date)",
        "Expense Reimbursement Rules": "Terms governing travel, lodging, and other reimbursable expenses. Format: Rules as stated (e.g., Reimbursed as per client travel policy, pre-approval required)"
    },
    "Risk & Compliance": {
        "Indemnification Clause Reference": "Clause defining indemnity obligations and covered risks. Format: Section heading/number and 1-2 sentence excerpt (e.g., Section 12 – Indemnification: Each party agrees to indemnify...)",
        "Limitation of Liability Cap": "Maximum financial liability for either party. Format: Cap as stated (e.g., Aggregate liability not to exceed fees paid in previous 12 months)",
        "Insurance Requirements": "Types and minimum coverage levels required by client. Format: Requirements as stated (e.g., CGL $2M per occurrence; Workers Comp as per law)",
        "Warranties / Disclaimers": "Assurances or disclaimers related to service performance or quality. Format: Text as stated (e.g., Services to be performed in a professional manner; no other warranties implied)"
    }
}

# Default value for missing fields
NOT_FOUND_VALUE = "Not Found"

# ============================================================================
# LLM Prompt Configuration
# ============================================================================

# Maximum text length for LLM processing (characters)
# For longer docs, implement chunking + aggregation
MAX_TEXT_LENGTH = 50000

# ============================================================================
# PDF Preprocessing Configuration
# ============================================================================

# DPI for rendering PDF pages as images (150, 300, 600)
# Higher DPI = better quality but larger files
# 300 DPI is optimal for OCR (balance between quality and size)
PDF_PREPROCESSING_DPI = int(os.getenv("PDF_PREPROCESSING_DPI", "300"))

# Enable OpenCV preprocessing for scanned PDFs
ENABLE_IMAGE_PREPROCESSING = os.getenv("ENABLE_IMAGE_PREPROCESSING", "true").lower() == "true"

# Individual preprocessing steps (can be toggled)
ENABLE_DESKEW = os.getenv("ENABLE_DESKEW", "true").lower() == "true"
ENABLE_DENOISE = os.getenv("ENABLE_DENOISE", "true").lower() == "true"
ENABLE_ENHANCE = os.getenv("ENABLE_ENHANCE", "true").lower() == "true"
ENABLE_BINARIZE = os.getenv("ENABLE_BINARIZE", "true").lower() == "true"

# ============================================================================
# Extraction Strategy Configuration
# ============================================================================

# Extraction strategy selection
EXTRACTION_STRATEGY = os.getenv("EXTRACTION_STRATEGY", "auto")
# Options: "auto", "text_extraction", "gemini_vision", "tesseract", "gcv"

# OCR Engine (for image-based PDFs when not using Gemini Vision)
OCR_ENGINE = os.getenv("OCR_ENGINE", "tesseract")
# Options: "tesseract", "gcv"
# Note: "gemini_vision" is handled separately (no OCR step needed)

# Gemini Model Configuration
GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash")  # For text LLM
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-flash")  # For vision LLM

# Google Cloud Vision Configuration (for Strategy 3)
GCV_CREDENTIALS_PATH = os.getenv("GCV_CREDENTIALS_PATH", "")
GCV_PROJECT_ID = os.getenv("GCV_PROJECT_ID", "")

# ============================================================================
# Validation
# ============================================================================

def validate_config():
    """
    Validate that required configuration is present.
    
    Raises:
        ValueError: If required configuration is missing.
    """
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY not found in environment variables. "
            "Please set it in your .env file or environment."
        )

