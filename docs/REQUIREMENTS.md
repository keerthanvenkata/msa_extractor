# MSA Metadata Extraction Requirements

This document defines the canonical schema and field definitions for MSA metadata extraction. **All code, prompts, and validation must reference this document.**

## Schema Definition

### Org Details

| Field Name | Definition / Description | Example / Format |
|------------|-------------------------|------------------|
| **Organization Name** | Full legal name of the contracting organization (counterparty). | `Adaequare Inc` |

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

### Business Terms

| Field Name | Definition / Description | Example / Format |
|------------|-------------------------|------------------|
| **Document Type** | Type of agreement as stated by the title or heading. Use 'MSA' for Master/Professional Services Agreement and 'NDA' for Non-Disclosure Agreement. | `MSA` or `NDA` |
| **Termination Notice Period** | Minimum written notice required to terminate the agreement. Extract the default notice period and note any special cases. | `30 days` |

### Commercial Operations

| Field Name | Definition / Description | Example / Format |
|------------|-------------------------|------------------|
| **Billing Frequency** | How often invoices are issued under the MSA. | `Monthly`, `Quarterly`, `Milestone-based` |
| **Payment Terms** | Time allowed for payment after invoice submission. | `Net 30 days from invoice date` |
| **Expense Reimbursement Rules** | Terms governing travel, lodging, and other reimbursable expenses. | `Reimbursed as per client travel policy, pre-approval required` |

### Finance Terms

| Field Name | Definition / Description | Example / Format |
|------------|-------------------------|------------------|
| **Pricing Model Type** | Commercial structure indicated by references to hourly rates, work orders, and rate schedules. Use 'T&M' if billed by hourly rates; use 'Fixed' or 'Subscription' only if explicitly stated. | `Fixed`, `T&M`, or `Subscription` |
| **Currency** | Settlement/monetary currency inferred from currency symbols or stated amounts. | `USD`, `INR`, `EUR`, `GBP` |
| **Contract Value** | Total contract value if explicitly stated; otherwise return 'Not Found'. Many PSAs/MSAs defer value to Work Orders/SOWs. | `50000.00` or `Not Found` |

### Risk & Compliance

| Field Name | Definition / Description | Example / Format |
|------------|-------------------------|------------------|
| **Indemnification Clause Reference** | Clause defining indemnity obligations and covered risks. | `Section 12 – Indemnification` |
| **Limitation of Liability Cap** | Maximum financial liability for either party. | `Aggregate liability not to exceed fees paid in previous 12 months` |
| **Insurance Requirements** | Types and minimum coverage levels required by client. | `CGL $2M per occurrence; Workers Comp as per law` |
| **Warranties / Disclaimers** | Assurances or disclaimers related to service performance or quality. | `Services to be performed in a professional manner; no other warranties implied` |

### Legal Terms

| Field Name | Definition / Description | Example / Format |
|------------|-------------------------|------------------|
| **Governing Law** | Jurisdiction whose laws govern the agreement, including venue/court location if specified. | `Texas, USA` or `Laws of the State of Texas; courts of Collin County, Texas` |
| **Confidentiality Clause Reference** | Clause title/number and a brief excerpt describing confidentiality obligations and return of materials. | `Section 8 – Confidential Information: Each party agrees to maintain confidentiality...` |
| **Force Majeure Clause Reference** | Clause title/number and short excerpt describing relief from obligations due to extraordinary events. If no explicit clause exists, return 'Not Found'. | `Section 15 – Force Majeure: Neither party shall be liable...` or `Not Found` |

## JSON Schema Structure

```json
{
  "Org Details": {
    "Organization Name": ""
  },
  "Contract Lifecycle": {
    "Party A": "",
    "Party B": "",
    "Execution Date": "",
    "Effective Date": "",
    "Expiration / Termination Date": "",
    "Authorized Signatory - Party A": "",
    "Authorized Signatory - Party B": ""
  },
  "Business Terms": {
    "Document Type": "",
    "Termination Notice Period": ""
  },
  "Commercial Operations": {
    "Billing Frequency": "",
    "Payment Terms": "",
    "Expense Reimbursement Rules": ""
  },
  "Finance Terms": {
    "Pricing Model Type": "",
    "Currency": "",
    "Contract Value": ""
  },
  "Risk & Compliance": {
    "Indemnification Clause Reference": "",
    "Limitation of Liability Cap": "",
    "Insurance Requirements": "",
    "Warranties / Disclaimers": ""
  },
  "Legal Terms": {
    "Governing Law": "",
    "Confidentiality Clause Reference": "",
    "Force Majeure Clause Reference": ""
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

7. **Document Type**:
   - Must be exactly "MSA" or "NDA" (case-sensitive)
   - Use "MSA" for Master/Professional Services Agreement
   - Use "NDA" for Non-Disclosure Agreement
   - Determine from document title or heading

8. **Termination Notice Period**:
   - Format: "<number> <unit>" (e.g., "30 days", "3 months")
   - Extract the primary/default notice period for the main agreement
   - If multiple periods exist (e.g., different for work orders), return the primary agreement notice

9. **Pricing Model Type**:
   - Must be exactly one of: "Fixed", "T&M", or "Subscription" (case-sensitive)
   - Use "T&M" if billed by hourly rates
   - Use "Fixed" or "Subscription" only if explicitly stated

10. **Currency**:
    - Use ISO currency code (e.g., "USD", "INR", "EUR", "GBP")
    - Infer from currency symbols ($, ₹, €, £) or explicitly stated amounts
    - If multiple currencies mentioned, prefer the primary settlement currency

11. **Contract Value**:
    - Return decimal number if explicitly stated (e.g., "50000.00" or "50000")
    - Many MSAs defer value to Work Orders/SOWs - return "Not Found" if not specified in main agreement
    - Normalize commas if present

12. **Force Majeure Clause Reference**:
    - If no explicit clause exists, return "Not Found"
    - Otherwise, return section heading/number and brief excerpt

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

- **December 2025**: Added new fields: Organization Name, Document Type, Termination Notice Period, Pricing Model Type, Currency, Contract Value, Governing Law, Confidentiality Clause Reference, and Force Majeure Clause Reference. Added new categories: Org Details, Business Terms, Finance Terms, and Legal Terms.
- **November 14, 2025**: Added Party A, Party B, and separate authorized signatories for each party
- **November 11, 2025**: Initial requirements definition with exact field definitions and examples

