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
# Strip whitespace/newlines from API key (Secret Manager may include trailing newlines)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# FastAPI Server Configuration
# Cloud Run sets PORT automatically, fallback to API_PORT or 8000
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))  # PORT for Cloud Run, API_PORT for local
API_WORKERS = int(os.getenv("API_WORKERS", "1"))
API_RELOAD = os.getenv("API_RELOAD", "false").lower() == "true"  # For development

# File Upload Configuration
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))  # Maximum file upload size in MB
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert to bytes

# Background Task Configuration
API_MAX_CONCURRENT_EXTRACTIONS = int(os.getenv("API_MAX_CONCURRENT_EXTRACTIONS", "5"))  # Max concurrent background extraction tasks

# Authentication Configuration
API_ENABLE_AUTH = os.getenv("API_ENABLE_AUTH", "false").lower() == "true"  # Enable API key authentication
API_KEY_RAW = os.getenv("API_KEY", "")  # API key(s) for authentication (if enabled)
# Support multiple keys: comma-separated list (e.g., "key1,key2,key3")
# Empty keys are filtered out
API_KEYS = {key.strip() for key in API_KEY_RAW.split(",") if key.strip()} if API_KEY_RAW else set()
# For backward compatibility, also provide single key (first key if multiple)
API_KEY = list(API_KEYS)[0] if API_KEYS else ""
# Note: For Iteration 1, using simple API key. Future: Upgrade to JWT/OAuth2


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
# Handle both relative paths (./storage/msa_extractor.db) and absolute paths
db_path_env = os.getenv("DB_PATH", "")
if db_path_env:
    # Remove leading ./ if present, then resolve relative to BASE_DIR
    db_path_clean = db_path_env.lstrip("./")
    if os.path.isabs(db_path_clean):
        # Absolute path
        DB_PATH = Path(db_path_clean)
    else:
        # Relative path - resolve from BASE_DIR
        DB_PATH = BASE_DIR / db_path_clean
else:
    # Default: use storage directory
    DB_PATH = STORAGE_DIR / "msa_extractor.db"

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
# Enhanced structure with extracted_value, match_flag, and validation per field
METADATA_SCHEMA = {
    "Org Details": {
        "Organization Name": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        }
    },
    "Contract Lifecycle": {
        "Party A": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Party B": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Execution Date": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Effective Date": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Expiration / Termination Date": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Authorized Signatory - Party A": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Authorized Signatory - Party B": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        }
    },
    "Business Terms": {
        "Document Type": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Termination Notice Period": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        }
    },
    "Commercial Operations": {
        "Billing Frequency": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Payment Terms": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Expense Reimbursement Rules": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        }
    },
    "Finance Terms": {
        "Pricing Model Type": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Currency": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Contract Value": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        }
    },
    "Risk & Compliance": {
        "Indemnification Clause Reference": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Limitation of Liability Cap": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Insurance Requirements": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Warranties / Disclaimers": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        }
    },
    "Legal Terms": {
        "Governing Law": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Confidentiality Clause Reference": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        },
        "Force Majeure Clause Reference": {
            "extracted_value": "",
            "match_flag": "",
            "validation": {
                "score": 0,
                "status": "",
                "notes": ""
            }
        }
    }
}

# Match flag allowed values
MATCH_FLAG_VALUES = [
    "same_as_template",
    "similar_not_exact",
    "different_from_template",
    "flag_for_review",
    "not_found"
]

# Validation status allowed values
VALIDATION_STATUS_VALUES = [
    "valid",
    "warning",
    "invalid",
    "not_found"
]

# Field definitions for LLM prompts (from docs/REQUIREMENTS.md)
FIELD_DEFINITIONS = {
    "Org Details": {
        "Organization Name": "Full legal name of the contracting organization (parent company/business entity). If a brand is mentioned elsewhere in the document, map that brand to Organization Name. If no brand is mentioned, use the same value as the legal entity name (Party A or Party B, whichever is the primary contracting organization). Format: As stated in the agreement (e.g., 'Adaequare Inc')"
    },
    "Contract Lifecycle": {
        "Party A": "Name of the first party to the agreement (typically the client or service recipient). Format: Full legal entity name as stated in the contract (e.g., Adaequare Inc.)",
        "Party B": "Name of the second party to the agreement (typically the vendor or service provider). Format: Full legal entity name as stated in the contract (e.g., Orbit Inc.)",
        "Execution Date": "Date when both parties have signed the agreement. Format: ISO yyyy-mm-dd (e.g., 2025-03-14)",
        "Effective Date": "Date the MSA becomes legally effective (may differ from execution). Format: ISO yyyy-mm-dd (e.g., 2025-04-01)",
        "Expiration / Termination Date": "Date on which the agreement expires or terminates unless renewed. Format: ISO yyyy-mm-dd or 'Evergreen' if auto-renews (e.g., 2028-03-31 or Evergreen)",
        "Authorized Signatory - Party A": "Name and designation of the individual authorized to sign on behalf of Party A. Format: Full name and title (e.g., John Doe, VP of Operations). Extract from signature page or execution section.",
        "Authorized Signatory - Party B": "Name and designation of the individual authorized to sign on behalf of Party B. Format: Full name and title (e.g., Jane Smith, CEO). Extract from signature page or execution section."
    },
    "Business Terms": {
        "Document Type": "Type of agreement as stated by the title or heading. Use 'MSA' for Master/Professional Services Agreement or 'Services Agreement'. Use 'NDA' for Non-Disclosure Agreement. Edge cases: If document contains both MSA and NDA elements, set to 'MSA' if commercial terms (pricing, payment, termination) exist; otherwise 'NDA'. If unclear (e.g., just 'Services Agreement'), default to 'MSA' if pricing/term/termination are found; else 'NDA'. Format: 'MSA' or 'NDA'",
        "Termination Notice Period": "Minimum written notice required to terminate the agreement. Accept various formats: '30 days', 'thirty (30) calendar days', '1 month', '60 business days'. Normalize units: '1 month' = '30 days', '1 year' = '365 days'. Format: '<number> days' (e.g., '30 days'). Extract the primary/default notice period for the main agreement. If multiple periods exist (e.g., different for work orders), return the primary agreement notice. Examples: '30 calendar days' → '30 days', '1 month' → '30 days', 'sixty (60) business days' → '60 days'"
    },
    "Commercial Operations": {
        "Billing Frequency": "How often invoices are issued under the MSA. Examples: Monthly, Quarterly, Milestone-based, As-invoiced",
        "Payment Terms": "Time allowed for payment after invoice submission. Format: Terms as stated (e.g., Net 30 days from invoice date)",
        "Expense Reimbursement Rules": "Terms governing travel, lodging, and other reimbursable expenses. Format: Rules as stated (e.g., Reimbursed as per client travel policy, pre-approval required)"
    },
    "Finance Terms": {
        "Pricing Model Type": "Commercial structure indicated by references to hourly rates, work orders, and rate schedules. Must be exactly one of: 'Fixed', 'T&M', 'Subscription', or 'Hybrid' (case-sensitive). Normalize 'Time and Materials' or 'Time & Materials' to 'T&M'. Use 'T&M' if billed by hourly rates. Use 'Fixed' or 'Subscription' only if explicitly stated. If hybrid model (e.g., fixed base + hourly), set to 'Hybrid'. Format: Enum ['Fixed','T&M','Subscription','Hybrid'].",
        "Currency": "Settlement/monetary currency. Limited allowlist: 'USD' or 'INR' only (expandable later). If currency symbol detected: Infer ($ → USD, ₹ → INR). If currency explicitly stated: Use that value if it's USD or INR. If currency absent or not in allowlist: Return 'Not Found'. If multiple currencies mentioned, prefer the primary settlement currency. Format: 'USD', 'INR', or 'Not Found'.",
        "Contract Value": "Total contract value if explicitly stated; otherwise return 'Not Found'. Always include decimals (e.g., '50000.00' not '50000'). Keep the format as stated in the agreement (preserve decimal precision). Remove currency symbols and commas (e.g., '$50,000' → '50000.00'). Many PSAs/MSAs defer value to Work Orders/SOWs. Format: Decimal number with decimals (e.g., '50000.00') or 'Not Found' if not specified."
    },
    "Risk & Compliance": {
        "Indemnification Clause Reference": "Clause defining indemnity obligations and covered risks. Format: Section heading/number and 1-2 sentence excerpt (e.g., Section 12 – Indemnification: Each party agrees to indemnify...)",
        "Limitation of Liability Cap": "Maximum financial liability for either party. Format: Cap as stated (e.g., Aggregate liability not to exceed fees paid in previous 12 months)",
        "Insurance Requirements": "Types and minimum coverage levels required by client. Format: Requirements as stated (e.g., CGL $2M per occurrence; Workers Comp as per law)",
        "Warranties / Disclaimers": "Assurances or disclaimers related to service performance or quality. Format: Text as stated (e.g., Services to be performed in a professional manner; no other warranties implied)"
    },
    "Legal Terms": {
        "Governing Law": "Jurisdiction whose laws govern the agreement, including venue/court location if specified. Format: Text as stated (e.g., 'Texas, USA' or 'Laws of the State of Texas; courts of Collin County, Texas')",
        "Confidentiality Clause Reference": "Clause title/number and a brief excerpt describing confidentiality obligations and return of materials. If no explicit clause exists, return 'Not Found'. Format: 'Section <number> – <title>: <1–2 sentence excerpt>' or 'Not Found'",
        "Force Majeure Clause Reference": "Clause title/number and short excerpt describing relief from obligations due to extraordinary events. If no explicit clause exists, return 'Not Found'. Note: Consistent with all clause references - all return 'Not Found' if absent. Format: 'Section <number> – <title>: <1–2 sentence excerpt>' or 'Not Found'"
    }
}

# Default value for missing fields
NOT_FOUND_VALUE = "Not Found"

# ============================================================================
# Field-Specific LLM Instructions
# ============================================================================

# Field-specific instructions for LLM extraction
# These are additional instructions beyond the basic field definitions
# Structure: {category: {field_name: {instruction, mandatory_field, negotiable, expected_position}}}
# - instruction: Detailed extraction guidance text (required)
# - mandatory_field: "yes" or "no" - whether this is a mandatory clause in the template
# - negotiable: "yes" or "no" - whether this field is typically negotiable
# - expected_position: Brief description of the expected/standard answer (from template)
FIELD_INSTRUCTIONS = {
    "Org Details": {
        "Organization Name": {
            "instruction": """Full legal name of the contracting organization (parent company/business entity).
If a brand is mentioned elsewhere in the document, map that brand to Organization Name.
If no brand is mentioned, use the same value as the legal entity name (Party A or Party B, whichever is the primary contracting organization).
Look in preamble/opening party identification (typically Page 1).""",
            "mandatory_field": "",  # To be filled from spreadsheet
            "negotiable": "",  # To be filled from spreadsheet
            "expected_position": ""  # To be filled from spreadsheet
        }
    },
    "Contract Lifecycle": {
        "Party A": {
            "instruction": """Extract full legal entity names as stated in the contract header.
Party A is typically the client/service recipient (first party mentioned).
Prefer legal entity names from the contract header over brand names.
Look in the contract header, "Parties" section, or first paragraph.""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Party B": {
            "instruction": """Extract full legal entity names as stated in the contract header.
Party B is typically the vendor/service provider (second party mentioned).
Prefer legal entity names from the contract header over brand names.
Look in the contract header, "Parties" section, or first paragraph.""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Execution Date": {
            "instruction": """Preferred format: ISO yyyy-mm-dd (e.g., 2025-03-14).
If ambiguous or unclear: Return the literal text found and include "(AmbiguousDate)" as a flag.
Example: "March 14, 2025 (AmbiguousDate)" or "Q1 2025 (AmbiguousDate)".
Look in signature pages or execution sections.""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Effective Date": {
            "instruction": """Preferred format: ISO yyyy-mm-dd (e.g., 2025-04-01).
If ambiguous or unclear: Return the literal text found and include "(AmbiguousDate)" as a flag.
Example: "March 14, 2025 (AmbiguousDate)" or "Q1 2025 (AmbiguousDate)".
May be defined relative to Execution Date. Look in "Effective Date" clause or "Commencement" section.""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Expiration / Termination Date": {
            "instruction": """If contract is "Evergreen" (auto-renews): Return "Evergreen".
If no explicit expiration: Return "Not Found".
Preferred format: ISO yyyy-mm-dd (e.g., 2028-03-31).
If ambiguous: Return the literal text found and include "(AmbiguousDate)" as a flag.
Look in "Term" or "Termination" section.""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Authorized Signatory - Party A": {
            "instruction": """Extract separately for each party from signature pages or execution sections.
Include full name and title/designation.
If multiple signatories for one party, combine with semicolons.
Example: "John Doe, VP of Operations; Jane Smith, CFO" (for Party A).
Look in signature pages (typically last page or last few pages).""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Authorized Signatory - Party B": {
            "instruction": """Extract separately for each party from signature pages or execution sections.
Include full name and title/designation.
If multiple signatories for one party, combine with semicolons.
Example: "Jane Smith, CEO; John Doe, CFO" (for Party B).
Look in signature pages (typically last page or last few pages).""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        }
    },
    "Business Terms": {
        "Document Type": {
            "instruction": """Must be exactly "MSA" or "NDA" (case-sensitive).
Use "MSA" for Master/Professional Services Agreement or "Services Agreement".
Use "NDA" for Non-Disclosure Agreement.
Determine from document title or heading.
Edge cases:
- If document contains both MSA and NDA elements: Set to "MSA" if commercial terms (pricing, payment, termination) exist; otherwise "NDA"
- If unclear (e.g., just "Services Agreement"): Default to "MSA" if pricing/term/termination are found; else "NDA"
Look in document title/header (typically Page 1).""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Termination Notice Period": {
            "instruction": """Accept various formats: "30 days", "thirty (30) calendar days", "1 month", "60 business days".
Normalize units: "1 month" = "30 days", "1 year" = "365 days".
Format: "<number> days" (e.g., "30 days").
Note the day type if specified (calendar days vs business days) in the extracted text.
Extract the primary/default notice period for the main agreement.
If multiple periods exist (e.g., different for work orders), return the primary agreement notice.
Examples:
- "30 calendar days" → "30 days"
- "1 month" → "30 days"
- "sixty (60) business days" → "60 days"
Look in termination sections (e.g., "Section Four – Termination").""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        }
    },
    "Commercial Operations": {
        "Billing Frequency": {
            "instruction": """Extract as stated in the document.
Look in sections named: "Payment", "Fees", "Compensation", "Commercial Terms", "Financial Terms", or similar.
Examples: Monthly, Quarterly, Milestone-based, As-invoiced.""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Payment Terms": {
            "instruction": """Extract as stated in the document.
Look in sections named: "Payment", "Fees", "Compensation", "Commercial Terms", "Financial Terms", or similar.
Format: Terms as stated (e.g., Net 30 days from invoice date).""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Expense Reimbursement Rules": {
            "instruction": """Extract as stated in the document.
Look in sections named: "Payment", "Fees", "Compensation", "Commercial Terms", "Financial Terms", or similar.
May also be in "Expenses", "Reimbursement", or "Travel" sections.
Format: Rules as stated (e.g., Reimbursed as per client travel policy, pre-approval required).""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        }
    },
    "Finance Terms": {
        "Pricing Model Type": {
            "instruction": """Must be exactly one of: "Fixed", "T&M", "Subscription", or "Hybrid" (case-sensitive).
Normalize "Time and Materials" or "Time & Materials" to "T&M".
Use "T&M" if billed by hourly rates.
Use "Fixed" or "Subscription" only if explicitly stated.
If hybrid model (e.g., fixed base + hourly): Set to "Hybrid".
Note: For hybrid models, the raw text description will be captured in the extracted value.
Look in sections about work orders, rate schedules, or commercial terms (e.g., "Section Three – Work Orders").""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Currency": {
            "instruction": """Limited allowlist: "USD" or "INR" only (expandable later).
If currency symbol detected: Infer ($ → USD, ₹ → INR).
If currency explicitly stated: Use that value if it's USD or INR.
If currency absent or not in allowlist: Return "Not Found".
If multiple currencies mentioned, prefer the primary settlement currency.
May appear in any monetary amounts (e.g., insurance limits, payment terms, rate schedules).""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Contract Value": {
            "instruction": """Always include decimals (e.g., "50000.00" not "50000").
Keep the format as stated in the agreement (preserve decimal precision).
Remove currency symbols and commas (e.g., "$50,000" → "50000.00").
Many MSAs defer value to Work Orders/SOWs - return "Not Found" if not specified in main agreement.
Check Work Orders/SOW references.""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        }
    },
    "Risk & Compliance": {
        "Indemnification Clause Reference": {
            "instruction": """If no explicit clause exists, return "Not Found" (consistent across all clause references).
If clause exists: Return the section heading/number and a 1–2 sentence excerpt.
Example: "Section 12 – Indemnification: Each party agrees to indemnify..."
Look in sections named: "Risk", "Liability", "Indemnification", "Insurance", "Warranties", or "General Provisions".""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Limitation of Liability Cap": {
            "instruction": """Extract as stated in the document.
Look in sections named: "Risk", "Liability", "Limitation of Liability", "Insurance", "Warranties", or "General Provisions".
Format: Cap as stated (e.g., Aggregate liability not to exceed fees paid in previous 12 months).""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Insurance Requirements": {
            "instruction": """Extract as stated in the document.
Look in sections named: "Risk", "Liability", "Indemnification", "Insurance", "Warranties", or "General Provisions".
Format: Requirements as stated (e.g., CGL $2M per occurrence; Workers Comp as per law).""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Warranties / Disclaimers": {
            "instruction": """Extract as stated in the document.
Look in sections named: "Risk", "Liability", "Indemnification", "Insurance", "Warranties", or "General Provisions".
May also be in "Service Level" or "Performance" sections.
Format: Text as stated (e.g., Services to be performed in a professional manner; no other warranties implied).""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        }
    },
    "Legal Terms": {
        "Governing Law": {
            "instruction": """Extract jurisdiction and venue/court location if specified.
Look in sections named "Governing Law", "Jurisdiction", or "Applicable Law" (e.g., "Section Seventeen – Governing Law").
Format: Text as stated (e.g., 'Texas, USA' or 'Laws of the State of Texas; courts of Collin County, Texas').""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Confidentiality Clause Reference": {
            "instruction": """If no explicit clause exists, return "Not Found" (consistent across all clause references).
If clause exists: Return the section heading/number and a 1–2 sentence excerpt.
Example: "Section 8 – Confidential Information: Each party agrees to maintain confidentiality..."
Check sections about confidential information (e.g., "Section Eight – Confidential Information").""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        },
        "Force Majeure Clause Reference": {
            "instruction": """If no explicit clause exists, return "Not Found" (consistent across all clause references).
If clause exists: Return the section heading/number and a 1–2 sentence excerpt.
Example: "Section 15 – Force Majeure: Neither party shall be liable..."
Search for "Force Majeure" explicitly; if absent, return "Not Found".
Note: Consistent with all clause references - all return "Not Found" if absent.""",
            "mandatory_field": "",
            "negotiable": "",
            "expected_position": ""
        }
    }
}

# ============================================================================
# Template References (Clause Excerpts and Sample Answers)
# ============================================================================

# Template clause references from standard MSA template
# Structure: {category: {field_name: {clause_excerpt, sample_answer, clause_name}}}
# To be populated from template PDF
TEMPLATE_REFERENCES = {
    "Org Details": {
        "Organization Name": {
            "clause_excerpt": "",  # Full clause for small ones, excerpt for large ones
            "sample_answer": "",
            "clause_name": ""  # Section/clause name (e.g., "Section 1 - Parties")
        }
    },
    "Contract Lifecycle": {
        "Party A": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Party B": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Execution Date": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Effective Date": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Expiration / Termination Date": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Authorized Signatory - Party A": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Authorized Signatory - Party B": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        }
    },
    "Business Terms": {
        "Document Type": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Termination Notice Period": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        }
    },
    "Commercial Operations": {
        "Billing Frequency": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Payment Terms": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Expense Reimbursement Rules": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        }
    },
    "Finance Terms": {
        "Pricing Model Type": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Currency": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Contract Value": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        }
    },
    "Risk & Compliance": {
        "Indemnification Clause Reference": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Limitation of Liability Cap": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Insurance Requirements": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Warranties / Disclaimers": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        }
    },
    "Legal Terms": {
        "Governing Law": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Confidentiality Clause Reference": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        },
        "Force Majeure Clause Reference": {
            "clause_excerpt": "",
            "sample_answer": "",
            "clause_name": ""
        }
    }
}

# ============================================================================
# LLM Prompt Configuration
# ============================================================================

# Maximum text length for LLM processing (characters)
# For longer docs, implement chunking + aggregation (deferred to next iteration)
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "50000"))

# Maximum length per metadata field (characters)
# Each field value must not exceed this limit (default: 1000)
MAX_FIELD_LENGTH = int(os.getenv("MAX_FIELD_LENGTH", "1000"))

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
#   - text_llm: Send all text (direct + OCR) to text LLM
#   - vision_llm: Send all images to vision LLM
#   - multimodal: Send text + images together to vision LLM in single call (default)
#   - dual_llm: Send text to text LLM + images to vision LLM separately, then merge
LLM_PROCESSING_MODE = os.getenv("LLM_PROCESSING_MODE", "multimodal")

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

