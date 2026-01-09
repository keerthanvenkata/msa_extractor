# Metadata Fields Sent to Gemini

This document lists all metadata fields, descriptions, and configuration that are sent to the Gemini API for MSA metadata extraction.

## Overview

The system sends the following to Gemini:
1. **JSON Schema Structure** - The exact structure expected in the response (enhanced with match_flag and validation)
2. **Field Definitions** - Detailed descriptions for each field
3. **Field-Specific Instructions** - LLM extraction instructions with metadata (mandatory_field, negotiable, expected_position)
4. **Template References** - Clause excerpts, sample answers, and clause names from standard template (when available)
5. **Extraction Rules** - Specific rules for handling edge cases, match flags, and validation
6. **Search Guidance** - Instructions on where to find information in documents
7. **Contract Text/Images** - The actual contract content to analyze

---

## JSON Schema Structure

The following JSON schema is sent to Gemini (from `METADATA_SCHEMA` in `config.py`). **Note:** As of v2.0.0, each field is an enhanced object with `extracted_value`, `match_flag`, and `validation`:

```json
{
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
```

**Field Structure (v2.0.0):**
- `extracted_value`: The actual extracted value (string)
- `match_flag`: One of `"same_as_template"`, `"similar_not_exact"`, `"different_from_template"`, `"flag_for_review"`, or `"not_found"`
- `validation`: Object with:
  - `score`: Integer 0-100 (quality score)
  - `status`: One of `"valid"`, `"warning"`, `"invalid"`, or `"not_found"`
  - `notes`: Optional string (max 500 chars) with insights

---

## Field Definitions

### Org Details

#### Organization Name
- **Description**: Full legal name of the contracting organization (counterparty).
- **Format**: As stated in the agreement (e.g., 'Adaequare Inc')
- **Example**: `Adaequare Inc`
- **Note**: Look in preamble/opening party identification (typically Page 1)

---

### Contract Lifecycle

#### Party A
- **Description**: Name of the first party to the agreement (typically the client or service recipient).
- **Format**: Full legal entity name as stated in the contract (e.g., Adaequare Inc.)
- **Example**: `Adaequare Inc.`

#### Party B
- **Description**: Name of the second party to the agreement (typically the vendor or service provider).
- **Format**: Full legal entity name as stated in the contract (e.g., Orbit Inc.)
- **Example**: `Orbit Inc.`

#### Execution Date
- **Description**: Date when both parties have signed the agreement.
- **Format**: ISO yyyy-mm-dd (e.g., 2025-03-14)
- **Example**: `2025-03-14`

#### Effective Date
- **Description**: Date the MSA becomes legally effective (may differ from execution).
- **Format**: ISO yyyy-mm-dd (e.g., 2025-04-01)
- **Example**: `2025-04-01`

#### Expiration / Termination Date
- **Description**: Date on which the agreement expires or terminates unless renewed.
- **Format**: ISO yyyy-mm-dd or 'Evergreen' if auto-renews (e.g., 2028-03-31 or Evergreen)
- **Example**: `2028-03-31` or `Evergreen`

#### Authorized Signatory - Party A
- **Description**: Name and designation of the individual authorized to sign on behalf of Party A.
- **Format**: Full name and title (e.g., John Doe, VP of Operations). Extract from signature page or execution section.
- **Example**: `John Doe, VP of Operations`
- **Note**: If multiple signatories for one party, combine with semicolons (e.g., "John Doe, VP of Operations; Jane Smith, CFO")

#### Authorized Signatory - Party B
- **Description**: Name and designation of the individual authorized to sign on behalf of Party B.
- **Format**: Full name and title (e.g., Jane Smith, CEO). Extract from signature page or execution section.
- **Example**: `Jane Smith, CEO`
- **Note**: If multiple signatories for one party, combine with semicolons

---

### Business Terms

#### Document Type
- **Description**: Type of agreement as stated by the title or heading. Use 'MSA' for Master/Professional Services Agreement and 'NDA' for Non-Disclosure Agreement.
- **Format**: Must be exactly "MSA" or "NDA" (case-sensitive)
- **Example**: `MSA` or `NDA`
- **Note**: Determine from document title or heading (typically Page 1)

#### Termination Notice Period
- **Description**: Minimum written notice required to terminate the agreement. Extract the default notice period and note any special cases.
- **Format**: "<number> <unit>" (e.g., "30 days", "3 months")
- **Example**: `30 days`
- **Note**: Extract the primary/default notice period for the main agreement. If multiple periods exist (e.g., different for work orders), return the primary agreement notice. Look in termination sections (e.g., "Section Four – Termination").

---

### Commercial Operations

#### Billing Frequency
- **Description**: How often invoices are issued under the MSA.
- **Format**: Terms as stated
- **Examples**: `Monthly`, `Quarterly`, `Milestone-based`, `As-invoiced`

#### Payment Terms
- **Description**: Time allowed for payment after invoice submission.
- **Format**: Terms as stated (e.g., Net 30 days from invoice date)
- **Example**: `Net 30 days from invoice date`

#### Expense Reimbursement Rules
- **Description**: Terms governing travel, lodging, and other reimbursable expenses.
- **Format**: Rules as stated (e.g., Reimbursed as per client travel policy, pre-approval required)
- **Example**: `Reimbursed as per client travel policy, pre-approval required`

---

### Finance Terms

#### Pricing Model Type
- **Description**: Commercial structure indicated by references to hourly rates, work orders, and rate schedules. Use 'T&M' if billed by hourly rates; use 'Fixed' or 'Subscription' only if explicitly stated.
- **Format**: Must be exactly one of: "Fixed", "T&M", or "Subscription" (case-sensitive)
- **Example**: `Fixed`, `T&M`, or `Subscription`
- **Note**: Use "T&M" if billed by hourly rates. Use "Fixed" or "Subscription" only if explicitly stated. Check sections about work orders, rate schedules, or commercial terms (e.g., "Section Three – Work Orders").

#### Currency
- **Description**: Settlement/monetary currency inferred from currency symbols or stated amounts.
- **Format**: ISO currency code (e.g., "USD", "INR", "EUR", "GBP")
- **Example**: `USD`, `INR`, `EUR`, `GBP`
- **Note**: Infer from currency symbols ($, ₹, €, £) or explicitly stated amounts. If multiple currencies mentioned, prefer the primary settlement currency. May appear in any monetary amounts (e.g., insurance limits, payment terms, rate schedules).

#### Contract Value
- **Description**: Total contract value if explicitly stated; otherwise return 'Not Found'. Many PSAs/MSAs defer value to Work Orders/SOWs.
- **Format**: Decimal number or "Not Found" if not specified
- **Example**: `50000.00` or `Not Found`
- **Note**: Return decimal number if explicitly stated (e.g., "50000.00" or "50000"). Many MSAs defer value to Work Orders/SOWs - return "Not Found" if not specified in main agreement. Normalize commas if present. Check Work Orders/SOW references.

---

### Risk & Compliance

#### Indemnification Clause Reference
- **Description**: Clause defining indemnity obligations and covered risks.
- **Format**: Section heading/number and 1-2 sentence excerpt (e.g., Section 12 – Indemnification: Each party agrees to indemnify...)
- **Example**: `Section 12 – Indemnification: Each party agrees to indemnify...`
- **Note**: Should include section heading/number and a brief excerpt

#### Limitation of Liability Cap
- **Description**: Maximum financial liability for either party.
- **Format**: Cap as stated (e.g., Aggregate liability not to exceed fees paid in previous 12 months)
- **Example**: `Aggregate liability not to exceed fees paid in previous 12 months`

#### Insurance Requirements
- **Description**: Types and minimum coverage levels required by client.
- **Format**: Requirements as stated (e.g., CGL $2M per occurrence; Workers Comp as per law)
- **Example**: `CGL $2M per occurrence; Workers Comp as per law`

#### Warranties / Disclaimers
- **Description**: Assurances or disclaimers related to service performance or quality.
- **Format**: Text as stated (e.g., Services to be performed in a professional manner; no other warranties implied)
- **Example**: `Services to be performed in a professional manner; no other warranties implied`

---

### Legal Terms

#### Governing Law
- **Description**: Jurisdiction whose laws govern the agreement, including venue/court location if specified.
- **Format**: Text as stated (e.g., 'Texas, USA' or 'Laws of the State of Texas; courts of Collin County, Texas')
- **Example**: `Texas, USA` or `Laws of the State of Texas; courts of Collin County, Texas`
- **Note**: Look in sections named "Governing Law", "Jurisdiction", or "Applicable Law" (e.g., "Section Seventeen – Governing Law").

#### Confidentiality Clause Reference
- **Description**: Clause title/number and a brief excerpt describing confidentiality obligations and return of materials.
- **Format**: 'Section <number> – <title>: <1–2 sentence excerpt>'
- **Example**: `Section 8 – Confidential Information: Each party agrees to maintain confidentiality...`
- **Note**: Check sections about confidential information (e.g., "Section Eight – Confidential Information").

#### Force Majeure Clause Reference
- **Description**: Clause title/number and short excerpt describing relief from obligations due to extraordinary events. If no explicit clause exists, return 'Not Found'.
- **Format**: Section heading/number and brief excerpt, or "Not Found" if not present
- **Example**: `Section 15 – Force Majeure: Neither party shall be liable...` or `Not Found`
- **Note**: Search for "Force Majeure" explicitly; if absent, return "Not Found".

---

## Extraction Rules

The following rules are sent to Gemini in the prompt:

1. **Enhanced Field Structure**: For EACH field, you MUST provide a complete object with:
   - `extracted_value`: The actual extracted value (string)
   - `match_flag`: One of the allowed values (see Match Flag Values below)
   - `validation`: A validation object with score, status, and notes (see Validation Requirements below)

2. **Missing Values**: If a field cannot be determined, use `"Not Found"` for `extracted_value` (never null, empty list, or other placeholders). Set `match_flag` to `"not_found"` and `validation.status` to `"not_found"`.

3. **Date Formatting**:
   - Preferred format: ISO yyyy-mm-dd (e.g., 2025-03-14)
   - If ambiguous or unclear: Return the literal text found and include "(AmbiguousDate)" as a flag
   - Example: "March 14, 2025 (AmbiguousDate)" or "Q1 2025 (AmbiguousDate)"

4. **Expiration / Termination Date**:
   - If contract is "Evergreen" (auto-renews): Return "Evergreen"
   - If no explicit expiration: Return "Not Found"

5. **Document Type**:
   - Must be exactly "MSA" or "NDA" (case-sensitive)
   - Use "MSA" for Master/Professional Services Agreement
   - Use "NDA" for Non-Disclosure Agreement
   - Determine from document title or heading

6. **Termination Notice Period**:
   - Format: "<number> <unit>" (e.g., "30 days", "3 months")
   - Extract the primary/default notice period for the main agreement
   - If multiple periods exist (e.g., different for work orders), return the primary agreement notice

7. **Pricing Model Type**:
   - Must be exactly one of: "Fixed", "T&M", or "Subscription" (case-sensitive)
   - Use "T&M" if billed by hourly rates
   - Use "Fixed" or "Subscription" only if explicitly stated

8. **Currency**:
   - Limited allowlist: "USD" or "INR" only (expandable later)
   - Infer from currency symbols ($ → USD, ₹ → INR)
   - If currency explicitly stated: Use that value if it's USD or INR
   - If currency absent or not in allowlist: Return "Not Found"
   - If multiple currencies mentioned, prefer the primary settlement currency

9. **Contract Value**:
   - Return decimal number if explicitly stated (e.g., "50000.00" or "50000")
   - Many MSAs defer value to Work Orders/SOWs - return "Not Found" if not specified in main agreement
   - Normalize commas if present

10. **Force Majeure Clause Reference**:
   - If no explicit clause exists, return "Not Found"
   - Otherwise, return section heading/number and brief excerpt

11. **Clause References** (Indemnification, Confidentiality, Force Majeure):
    - Return the section heading/number and a 1–2 sentence excerpt
    - Example: "Section 12 – Indemnification: Each party agrees to indemnify..."

12. **Party A and Party B**:
   - Extract full legal entity names as stated in the contract
   - Party A is typically the client/service recipient (first party mentioned)
   - Party B is typically the vendor/service provider (second party mentioned)
   - Look in the contract header, "Parties" section, or first paragraph

13. **Authorized Signatories**:
    - Extract separately for each party from signature pages or execution sections
    - Include full name and title/designation
    - If multiple signatories for one party, combine with semicolons
    - Example: "John Doe, VP of Operations; Jane Smith, CFO" (for Party A)

14. **Field Length Limits**: Each field value must not exceed `MAX_FIELD_LENGTH` characters (default: 1000). If a field would exceed this limit, truncate it appropriately while preserving the most important information.

15. **Response Format**: Return no commentary, no extra keys, and no markdown — JSON only.

16. **Match Flag Values** (choose exactly one per field):
    - `"same_as_template"`: Extracted value exactly matches template example (if template provided)
    - `"similar_not_exact"`: Extracted value is similar to template but with minor differences (format, wording, slight variations)
    - `"different_from_template"`: Extracted value differs significantly from template or uses different approach
    - `"flag_for_review"`: Value extracted but needs human review (ambiguous, unusual format, complex scenario, or unclear)
    - `"not_found"`: Field not found in document (set extracted_value to `"Not Found"`)

17. **Validation Requirements** (required for EVERY field):
    - `score`: Integer 0-100 (required)
      * 100: Perfect match with template (if provided), complete, correct, and properly formatted
      * 90-99: Excellent quality, minor formatting differences
      * 75-89: Good quality, acceptable with minor issues or deviations
      * 50-74: Acceptable but deviates from template or has moderate issues
      * 25-49: Significant issues, deviations, or quality concerns
      * 0-24: Poor quality, missing critical information, or incorrect format
    - `status`: One of `"valid"`, `"warning"`, `"invalid"`, or `"not_found"` (required)
    - `notes`: String (optional, max 500 chars) with validation insights, deviations from template, recommendations, or explanations

18. **Negotiable Fields Guidance**:
    - For fields marked as "negotiable" in FIELD-SPECIFIC INSTRUCTIONS, the extracted values do NOT need to match the template.
    - These fields (e.g., Party A, Party B, Execution Date, Payment Terms, Currency) will naturally vary between contracts.
    - When setting match_flag for negotiable fields:
      * Use `"same_as_template"` only if the STRUCTURE/FORMAT matches (e.g., both use "Net 30 days" format)
      * Use `"different_from_template"` if the actual VALUES differ (e.g., different party names, different dates, different payment terms)
      * The match_flag should reflect structural similarity, not value similarity for negotiable fields
    - For non-negotiable fields (e.g., Limitation of Liability Cap, Warranties), the match_flag should reflect how closely the extracted clause matches the template clause structure and content.

---

## Search Guidance

The following guidance is provided to Gemini on where to find information:

- **Document Structure**: Agreements may have different structures and section names. Search the ENTIRE document thoroughly.
- **Information Locations**: Information may appear in: main body, signature pages, appendices, exhibits, schedules, or footers/headers.
- **Organization Name**: Look in preamble/opening party identification (typically Page 1).
- **Document Type**: Check document title/header (typically Page 1).
- **Party Information**: Party A and Party B names are typically in the contract header, "Parties" section, or first paragraph.
- **Execution Information**: Execution Date and Authorized Signatories are often on signature pages (typically last page or last few pages).
- **Termination Notice Period**: Look in termination sections (e.g., "Section Four – Termination").
- **Pricing Model Type**: Check sections about work orders, rate schedules, or commercial terms (e.g., "Section Three – Work Orders").
- **Currency**: May appear in any monetary amounts (e.g., insurance limits, payment terms, rate schedules).
- **Contract Value**: Check Work Orders/SOW references; return "Not Found" if not explicitly defined in main agreement.
- **Commercial Terms**: Payment Terms, Billing Frequency may be in sections named: "Payment", "Fees", "Compensation", "Commercial Terms", "Financial Terms", or similar.
- **Governing Law**: Look in sections named "Governing Law", "Jurisdiction", or "Applicable Law" (e.g., "Section Seventeen – Governing Law").
- **Confidentiality Clause Reference**: Check sections about confidential information (e.g., "Section Eight – Confidential Information").
- **Force Majeure Clause Reference**: Search for "Force Majeure" explicitly; if absent, return "Not Found".
- **Risk Terms**: Indemnification, Limitation of Liability, Insurance may be in: "Risk", "Liability", "Indemnification", "Insurance", "Warranties", or "General Provisions".
- **Flexibility**: Look for information regardless of exact section names - focus on content and context.
- **Cross-Referencing**: Cross-reference related fields (e.g., Effective Date may be defined relative to Execution Date).

---

## Configuration Constants

The following configuration values are used in the prompt:

- **NOT_FOUND_VALUE**: `"Not Found"` (default value for missing fields)
- **MAX_FIELD_LENGTH**: `1000` characters (maximum length per metadata field)
- **MAX_TEXT_LENGTH**: `50000` characters (maximum text length for LLM processing)

---

## Prompt Structure

The prompt sent to Gemini follows this structure:

1. **Role Definition**: "You are a contract analyst."
2. **Task**: "Extract the following metadata fields from the given Master Service Agreement and return VALID JSON ONLY matching this schema:"
3. **Schema**: The JSON schema structure (indented, pretty-printed) with enhanced structure
4. **Field Definitions**: All field definitions organized by category
5. **Field-Specific Instructions**: LLM extraction instructions with metadata (mandatory_field, negotiable, expected_position) from `FIELD_INSTRUCTIONS` in `config.py`
6. **Template References**: Clause excerpts, sample answers, and clause names from standard template (when available) from `TEMPLATE_REFERENCES` in `config.py`
7. **Extraction Rules**: The 18 extraction rules listed above (including match flags and validation)
8. **Search Guidance**: Instructions on where to find information
9. **Contract Content**: Either:
   - For text model: The contract text wrapped in triple quotes
   - For vision model: Instructions to extract text from the image(s) provided

---

## Model Configuration

- **Text Model**: `gemini-2.5-pro` (default, configurable via `GEMINI_TEXT_MODEL`)
- **Vision Model**: `gemini-2.5-pro` (default, configurable via `GEMINI_VISION_MODEL`)

---

## Response Handling

After receiving the response from Gemini:

1. **JSON Parsing**: The response is parsed, handling cases where it might be wrapped in markdown code blocks
2. **Schema Validation**: The response is validated against the schema (before normalization)
3. **Normalization**: Missing fields are filled with `"Not Found"` to match the complete schema
4. **Error Handling**: If JSON parsing fails, an empty schema is returned as fallback

---

## Related Files

- **Schema Definition**: `config.py` (lines 149-194)
- **Prompt Building**: `ai/gemini_client.py` (lines 236-344)
- **Field Definitions Source**: `docs/REQUIREMENTS.md`
- **Schema Validation**: `ai/schema.py`

---

## Summary

**Total Fields**: 22 metadata fields across 7 categories
- Org Details: 1 field
- Contract Lifecycle: 7 fields
- Business Terms: 2 fields
- Commercial Operations: 3 fields
- Finance Terms: 3 fields
- Risk & Compliance: 4 fields
- Legal Terms: 3 fields

**Categories**:
1. Org Details (1 field)
2. Contract Lifecycle (7 fields)
3. Business Terms (2 fields)
4. Commercial Operations (3 fields)
5. Finance Terms (3 fields)
6. Risk & Compliance (4 fields)
7. Legal Terms (3 fields)

**Special Handling**:
- Enhanced Structure: Each field includes `extracted_value`, `match_flag`, and `validation` object
- Match Flags: Template comparison flags for compliance tracking
- Validation: Per-field quality scores (0-100) and status (valid/warning/invalid/not_found)
- Dates: ISO format preferred, with ambiguous date flagging
- Evergreen contracts: Special "Evergreen" value for expiration
- Missing values: Always use "Not Found" (never null/empty)
- Field length: Maximum 1000 characters per field
- Multiple signatories: Combine with semicolons
- Document Type: Must be exactly "MSA" or "NDA" (case-sensitive)
- Pricing Model Type: Must be exactly "Fixed", "T&M", "Subscription", or "Hybrid" (case-sensitive)
- Currency: Limited allowlist "USD" or "INR" only (expandable later)
- Contract Value: Decimal number or "Not Found" if not specified
- Force Majeure: Returns "Not Found" if clause doesn't exist
- Negotiable Fields: Match flags reflect structural similarity, not value similarity


