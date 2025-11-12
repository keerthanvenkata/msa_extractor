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


# ============================================================================
# File Paths
# ============================================================================

# Base directory (project root)
BASE_DIR = Path(__file__).parent

# Output directory for results
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "results"))
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# Persistence & Storage Configuration
# ============================================================================

# Storage directory (for database)
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

# Database path (SQLite)
DB_PATH = Path(os.getenv("DB_PATH", STORAGE_DIR / "msa_extractor.db"))

# Uploads directory (for temporary PDFs)
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", BASE_DIR / "uploads"))
UPLOADS_DIR.mkdir(exist_ok=True)

# Results directory (for legacy mode - file-based JSON storage)
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", BASE_DIR / "results"))
RESULTS_DIR.mkdir(exist_ok=True)

# Logs directory (for legacy mode - file-based log storage)
LOGS_DIR = Path(os.getenv("LOGS_DIR", BASE_DIR / "logs"))
LOGS_DIR.mkdir(exist_ok=True)

# Cleanup configuration
CLEANUP_PDF_DAYS = int(os.getenv("CLEANUP_PDF_DAYS", "7"))  # Delete PDFs older than N days
CLEANUP_PDF_MAX_COUNT = int(os.getenv("CLEANUP_PDF_MAX_COUNT", "1000"))  # Max PDFs to keep
CLEANUP_PDF_MIN_COUNT = int(os.getenv("CLEANUP_PDF_MIN_COUNT", "500"))  # Min PDFs to keep before cleanup

# GCP Configuration (for future iterations - TODO)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_STORAGE_BUCKET = os.getenv("GCP_STORAGE_BUCKET", "")
GCP_CLOUD_SQL_INSTANCE = os.getenv("GCP_CLOUD_SQL_INSTANCE", "")
USE_GCS = os.getenv("USE_GCS", "false").lower() == "true"
USE_CLOUD_SQL = os.getenv("USE_CLOUD_SQL", "false").lower() == "true"
# Note: Iteration 1 uses SQLite + local storage only

# Contracts directory (for batch processing)
CONTRACTS_DIR = BASE_DIR / "contracts"
CONTRACTS_DIR.mkdir(exist_ok=True)

# ============================================================================
# Logging Configuration
# ============================================================================

# Overall log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# File logging
LOG_FILE_ENABLED = os.getenv("LOG_FILE_ENABLED", "true").lower() == "true"
LOG_FILE_PATH = Path(os.getenv("LOG_FILE_PATH", BASE_DIR / "logs"))
LOG_FILE_FORMAT = os.getenv("LOG_FILE_FORMAT", "text")  # text or json
LOG_FILE_ROTATION_DAYS = int(os.getenv("LOG_FILE_ROTATION_DAYS", "30"))
LOG_FILE_MAX_SIZE_MB = int(os.getenv("LOG_FILE_MAX_SIZE_MB", "10"))

# Console logging
LOG_CONSOLE_ENABLED = os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true"
LOG_CONSOLE_FORMAT = os.getenv("LOG_CONSOLE_FORMAT", "text")  # text or json

# Module-specific log levels
# Can override default LOG_LEVEL for specific modules
LOG_LEVELS = {
    "msa_extractor": LOG_LEVEL,
    "msa_extractor.extractors": os.getenv("LOG_LEVEL_EXTRACTORS", "DEBUG"),
    "msa_extractor.ai": os.getenv("LOG_LEVEL_AI", "INFO"),
    "msa_extractor.extractors.ocr_handler": os.getenv("LOG_LEVEL_OCR", "WARNING"),
}

# Create logs directory if file logging enabled
if LOG_FILE_ENABLED:
    LOG_FILE_PATH.mkdir(parents=True, exist_ok=True)

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
# For longer docs, implement chunking + aggregation (deferred to next iteration)
MAX_TEXT_LENGTH = 50000

# Maximum length per metadata field (characters)
# Each field value must not exceed this limit
MAX_FIELD_LENGTH = 1000

# ============================================================================
# Retry Configuration
# ============================================================================

# Maximum number of retry attempts for API calls
API_MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "3"))

# Initial retry delay in seconds (exponential backoff)
API_RETRY_INITIAL_DELAY = float(os.getenv("API_RETRY_INITIAL_DELAY", "1.0"))

# Maximum retry delay in seconds (caps exponential backoff)
API_RETRY_MAX_DELAY = float(os.getenv("API_RETRY_MAX_DELAY", "30.0"))

# Retry on these HTTP status codes
API_RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

# Retry on these exception types
API_RETRY_EXCEPTIONS = [
    "google.api_core.exceptions.ResourceExhausted",  # Rate limit
    "google.api_core.exceptions.ServiceUnavailable",  # Service unavailable
    "google.api_core.exceptions.InternalServerError",  # Internal server error
    "google.api_core.exceptions.DeadlineExceeded",  # Timeout
]

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
# Extraction Configuration
# ============================================================================

# Extraction Method: How to extract content from PDF pages
# Options:
#   - text_direct: Extract text directly from text pages, ignore image pages
#   - ocr_all: Convert all pages to images and run OCR on all pages
#   - ocr_images_only: Extract text from text pages + OCR only image pages (default)
#   - vision_all: Convert all pages to images (no OCR, for vision LLM)
#   - hybrid: Extract text from text pages + convert image pages to images (flexible)
EXTRACTION_METHOD = os.getenv("EXTRACTION_METHOD", "hybrid")

# LLM Processing Mode: How to process extracted content with LLMs
# Options:
#   - text_llm: Send all text (direct + OCR) to text LLM (default)
#   - vision_llm: Send all images to vision LLM
#   - multimodal: Send text + images together to vision LLM in single call
#   - dual_llm: Send text to text LLM + images to vision LLM separately, then merge
LLM_PROCESSING_MODE = os.getenv("LLM_PROCESSING_MODE", "text_llm")

# OCR Engine: Which OCR engine to use when OCR is needed
# Options: "tesseract", "gcv"
# Note: Only used when EXTRACTION_METHOD requires OCR (ocr_all, ocr_images_only)
# Note: vision_all and multimodal don't use OCR
OCR_ENGINE = os.getenv("OCR_ENGINE", "tesseract")


# ============================================================================
# Tesseract OCR Configuration
# ============================================================================

# Tesseract executable path (optional, for non-standard installations)
# If not set, pytesseract will look for tesseract in PATH
# Cross-platform: Use forward slashes or raw strings, pathlib will handle it
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
# Windows example: C:\Program Files\Tesseract-OCR\tesseract.exe
# Linux example: /usr/bin/tesseract
# Docker example: /usr/bin/tesseract (usually in PATH)

# Tesseract language(s) for OCR
# Use ISO 639-2 language codes (e.g., "eng", "eng+fra" for multiple languages)
# Default: "eng" (English)
TESSERACT_LANG = os.getenv("TESSERACT_LANG", "eng")

# Tesseract data directory (optional, for custom tessdata location)
# If not set, uses default tessdata location
# Cross-platform: Use forward slashes or raw strings, pathlib will handle it
TESSDATA_PREFIX = os.getenv("TESSDATA_PREFIX", "")
# Windows example: C:\Program Files\Tesseract-OCR\tessdata
# Linux example: /usr/share/tesseract-ocr/5/tessdata
# Docker example: /usr/share/tesseract-ocr/5/tessdata (usually default)

# Gemini Model Configuration
GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-pro")  # For text LLM
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-pro")  # For vision LLM

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
        ConfigurationError: If required configuration is missing.
    """
    from utils.exceptions import ConfigurationError
    
    if not GEMINI_API_KEY:
        raise ConfigurationError(
            "GEMINI_API_KEY not found in environment variables. "
            "Please set it in your .env file or environment."
        )

