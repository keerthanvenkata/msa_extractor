# MSA Metadata Extraction Requirements

This document defines the canonical schema and field definitions for MSA metadata extraction. **All code, prompts, and validation must reference this document.**

## Schema Definition

### Contract Lifecycle

| Field Name | Definition / Description | Example / Format |
|------------|-------------------------|------------------|
| **Party A** | Name of the first party to the agreement (typically the client or service recipient). | `Adaequare Inc.` |
| **Party B** | Name of the second party to the agreement (typically the vendor or service provider). | `Orbit Inc.` |
| **Execution Date** | Date when both parties have signed the agreement. | `2025-03-14` |
| **Effective Date** | Date the MSA becomes legally effective (may differ from execution). | `2025-04-01` |
| **Expiration / Termination Date** | Date on which the agreement expires or terminates unless renewed. | `2028-03-31` or `Evergreen` |
| **Authorized Signatory - Party A** | Name and designation of the individual authorized to sign on behalf of Party A. | `John Doe, VP of Operations` |
| **Authorized Signatory - Party B** | Name and designation of the individual authorized to sign on behalf of Party B. | `Jane Smith, CEO` |

### Commercial Operations

| Field Name | Definition / Description | Example / Format |
|------------|-------------------------|------------------|
| **Billing Frequency** | How often invoices are issued under the MSA. | `Monthly`, `Quarterly`, `Milestone-based` |
| **Payment Terms** | Time allowed for payment after invoice submission. | `Net 30 days from invoice date` |
| **Expense Reimbursement Rules** | Terms governing travel, lodging, and other reimbursable expenses. | `Reimbursed as per client travel policy, pre-approval required` |

### Risk & Compliance

| Field Name | Definition / Description | Example / Format |
|------------|-------------------------|------------------|
| **Indemnification Clause Reference** | Clause defining indemnity obligations and covered risks. | `Section 12 – Indemnification` |
| **Limitation of Liability Cap** | Maximum financial liability for either party. | `Aggregate liability not to exceed fees paid in previous 12 months` |
| **Insurance Requirements** | Types and minimum coverage levels required by client. | `CGL $2M per occurrence; Workers Comp as per law` |
| **Warranties / Disclaimers** | Assurances or disclaimers related to service performance or quality. | `Services to be performed in a professional manner; no other warranties implied` |

## JSON Schema Structure

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

## Field Rules

1. **Missing Values**: If a field cannot be determined, return `"Not Found"` (never null, empty list, or other placeholders).

2. **Date Format**: 
   - Preferred: ISO format `yyyy-mm-dd` (e.g., `2025-03-14`)
   - If ambiguous: Return the literal text found and include `"AmbiguousDate"` as a flag in the result value
   - Example: `"March 14, 2025 (AmbiguousDate)"` or `"Q1 2025 (AmbiguousDate)"`

3. **Clause References**: 
   - Return the section heading/number and a 1–2 sentence excerpt
   - Example: `"Section 12 – Indemnification: Each party agrees to indemnify..."`

4. **Expiration Date Special Cases**:
   - If contract is "Evergreen" (auto-renews): Return `"Evergreen"`
   - If no explicit expiration: Return `"Not Found"`

5. **Party Identification**:
   - Extract full legal entity names as stated in the contract
   - Party A is typically the client/service recipient
   - Party B is typically the vendor/service provider
   - If party names are ambiguous, use the order they appear in the contract

6. **Authorized Signatories**:
   - Extract separately for each party from signature pages or execution sections
   - Include full name and title/designation
   - If multiple signatories for one party, combine with semicolons
   - Example: `"John Doe, VP of Operations; Jane Smith, CFO"` (for Party A)

## Affected Components

When updating requirements, ensure these components are synchronized:

### Core Configuration
- **`config.py`** - `METADATA_SCHEMA` dictionary
- **`ai/schema.py`** - Schema validation and normalization

### LLM Integration
- **`ai/gemini_client.py`** - Prompt template with field definitions
- **`PROMPT.md`** - Project prompt template (if used directly)

### Documentation
- **`docs/REQUIREMENTS.md`** - This file (canonical source)
- **`README.md`** - Output schema example
- **`docs/configuration.md`** - Schema reference

### Validation & Processing
- **`ai/schema.py`** - JSON Schema validation rules
- **`processors/postprocess.py`** - Date normalization, field cleaning (future)

## Update Checklist

When modifying requirements:

- [ ] Update `docs/REQUIREMENTS.md` (this file)
- [ ] Update `config.py` - `METADATA_SCHEMA`
- [ ] Update `ai/schema.py` - JSON Schema validation
- [ ] Update `ai/gemini_client.py` - Prompt template
- [ ] Update `README.md` - Schema example
- [ ] Update `docs/configuration.md` - Schema reference
- [ ] Update `PROMPT.md` - If prompt template is used directly
- [ ] Run tests to ensure validation still works
- [ ] Update any downstream processors that reference specific fields

## Version History

- **November 14, 2025**: Added Party A, Party B, and separate authorized signatories for each party
- **November 11, 2025**: Initial requirements definition with exact field definitions and examples

