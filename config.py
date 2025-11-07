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

# JSON Schema structure (as defined in PROMPT.md)
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

# Default value for missing fields
NOT_FOUND_VALUE = "Not Found"

# ============================================================================
# LLM Prompt Configuration
# ============================================================================

# Maximum text length for LLM processing (characters)
# For longer docs, implement chunking + aggregation
MAX_TEXT_LENGTH = 12000

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

