# Metadata Fields Sent to Gemini

This document lists all metadata fields, descriptions, and configuration that are sent to the Gemini API for MSA metadata extraction.

## Overview

The system sends the following to Gemini:
1. **JSON Schema Structure** - The exact structure expected in the response
2. **Field Definitions** - Detailed descriptions for each field
3. **Extraction Rules** - Specific rules for handling edge cases
4. **Search Guidance** - Instructions on where to find information in documents
5. **Contract Text/Images** - The actual contract content to analyze

---

## JSON Schema Structure

The following JSON schema is sent to Gemini (from `METADATA_SCHEMA` in `config.py`):

```json
{
  "Contract Lifecycle": {
    "Party A": "",
    "Party B": "",
    "Execution Date": "",
    "Effective Date": "",
    "Expiration / Termination Date": "",
    "Authorized Signatory - Party A": "",
    "Authorized Signatory - Party B": ""
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
```

---

## Field Definitions

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

## Extraction Rules

The following rules are sent to Gemini in the prompt:

1. **Missing Values**: If a field cannot be determined, use `"Not Found"` (never null, empty list, or other placeholders).

2. **Date Formatting**:
   - Preferred format: ISO yyyy-mm-dd (e.g., 2025-03-14)
   - If ambiguous or unclear: Return the literal text found and include "(AmbiguousDate)" as a flag
   - Example: "March 14, 2025 (AmbiguousDate)" or "Q1 2025 (AmbiguousDate)"

3. **Expiration / Termination Date**:
   - If contract is "Evergreen" (auto-renews): Return "Evergreen"
   - If no explicit expiration: Return "Not Found"

4. **Indemnification Clause Reference**:
   - Return the section heading/number and a 1–2 sentence excerpt
   - Example: "Section 12 – Indemnification: Each party agrees to indemnify..."

5. **Party A and Party B**:
   - Extract full legal entity names as stated in the contract
   - Party A is typically the client/service recipient (first party mentioned)
   - Party B is typically the vendor/service provider (second party mentioned)
   - Look in the contract header, "Parties" section, or first paragraph

6. **Authorized Signatories**:
   - Extract separately for each party from signature pages or execution sections
   - Include full name and title/designation
   - If multiple signatories for one party, combine with semicolons
   - Example: "John Doe, VP of Operations; Jane Smith, CFO" (for Party A)

7. **Field Length Limits**: Each field value must not exceed `MAX_FIELD_LENGTH` characters (default: 1000). If a field would exceed this limit, truncate it appropriately while preserving the most important information.

8. **Response Format**: Return no commentary, no extra keys, and no markdown — JSON only.

---

## Search Guidance

The following guidance is provided to Gemini on where to find information:

- **Document Structure**: Agreements may have different structures and section names. Search the ENTIRE document thoroughly.
- **Information Locations**: Information may appear in: main body, signature pages, appendices, exhibits, schedules, or footers/headers.
- **Party Information**: Party A and Party B names are typically in the contract header, "Parties" section, or first paragraph.
- **Execution Information**: Execution Date and Authorized Signatories are often on signature pages (typically last page or last few pages).
- **Commercial Terms**: Payment Terms, Billing Frequency may be in sections named: "Payment", "Fees", "Compensation", "Commercial Terms", "Financial Terms", or similar.
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
3. **Schema**: The JSON schema structure (indented, pretty-printed)
4. **Field Definitions**: All field definitions organized by category
5. **Extraction Rules**: The 8 extraction rules listed above
6. **Search Guidance**: Instructions on where to find information
7. **Contract Content**: Either:
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

**Total Fields**: 13 metadata fields across 3 categories
- Contract Lifecycle: 7 fields
- Commercial Operations: 3 fields
- Risk & Compliance: 4 fields

**Categories**:
1. Contract Lifecycle (7 fields)
2. Commercial Operations (3 fields)
3. Risk & Compliance (4 fields)

**Special Handling**:
- Dates: ISO format preferred, with ambiguous date flagging
- Evergreen contracts: Special "Evergreen" value for expiration
- Missing values: Always use "Not Found" (never null/empty)
- Field length: Maximum 1000 characters per field
- Multiple signatories: Combine with semicolons


