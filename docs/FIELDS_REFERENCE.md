# MSA Metadata Fields Reference

**Version:** v2.0.0  
**Date:** January 2026  
**Purpose:** Complete reference of all extractable fields with descriptions and typical section locations

This document lists all metadata fields currently extracted from MSAs, their descriptions, formats, and typical locations in contracts. Use this to map fields to your template's clause numbers.

---

## Field Summary

**Total Fields:** 22 fields across 7 categories

| Category | Field Count |
|----------|------------|
| Org Details | 1 |
| Contract Lifecycle | 7 |
| Business Terms | 2 |
| Commercial Operations | 3 |
| Finance Terms | 3 |
| Risk & Compliance | 4 |
| Legal Terms | 3 |

---

## 1. Org Details

### Organization Name
- **Description:** Full legal name of the contracting organization (parent company/business entity). If a brand is mentioned elsewhere in the document, map that brand to Organization Name. If no brand is mentioned, use the same value as the legal entity name (Party A or Party B, whichever is the primary contracting organization).
- **Format:** As stated in the agreement (e.g., 'Adaequare Inc')
- **Example:** `Adaequare Inc`
- **Typical Location:** 
  - Preamble/opening party identification (typically Page 1)
  - Contract header
  - "Parties" section
- **Section Reference:** *(To be filled from template)*
- **Notes:** 
  - Distinguish from Party A/Party B (legal entities)
  - May be a brand name if different from legal entity

---

## 2. Contract Lifecycle

### Party A
- **Description:** Name of the first party to the agreement (typically the client or service recipient).
- **Format:** Full legal entity name as stated in the contract (e.g., Adaequare Inc.)
- **Example:** `Adaequare Inc.`
- **Typical Location:**
  - Contract header (typically Page 1)
  - "Parties" section
  - First paragraph
- **Section Reference:** *(To be filled from template)*
- **Notes:** 
  - Prefer legal entity names from contract header over brand names
  - Party A is typically the client/service recipient

### Party B
- **Description:** Name of the second party to the agreement (typically the vendor or service provider).
- **Format:** Full legal entity name as stated in the contract (e.g., Orbit Inc.)
- **Example:** `Orbit Inc.`
- **Typical Location:**
  - Contract header (typically Page 1)
  - "Parties" section
  - First paragraph
- **Section Reference:** *(To be filled from template)*
- **Notes:** 
  - Prefer legal entity names from contract header over brand names
  - Party B is typically the vendor/service provider

### Execution Date
- **Description:** Date when both parties have signed the agreement.
- **Format:** ISO yyyy-mm-dd (e.g., 2025-03-14)
- **Example:** `2025-03-14`
- **Typical Location:**
  - Signature pages (typically last page or last few pages)
  - Execution section
  - May be near Effective Date
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - May differ from Effective Date
  - If ambiguous, include "(AmbiguousDate)" flag

### Effective Date
- **Description:** Date the MSA becomes legally effective (may differ from execution).
- **Format:** ISO yyyy-mm-dd (e.g., 2025-04-01)
- **Example:** `2025-04-01`
- **Typical Location:**
  - "Effective Date" clause
  - "Commencement" section
  - May be defined relative to Execution Date
  - Near beginning of contract
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - May be same as Execution Date
  - If ambiguous, include "(AmbiguousDate)" flag

### Expiration / Termination Date
- **Description:** Date on which the agreement expires or terminates unless renewed.
- **Format:** ISO yyyy-mm-dd or 'Evergreen' if auto-renews (e.g., 2028-03-31 or Evergreen)
- **Example:** `2028-03-31` or `Evergreen`
- **Typical Location:**
  - "Term" or "Termination" section
  - "Expiration" clause
  - May be in renewal/extension provisions
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - Return "Evergreen" if contract auto-renews
  - Return "Not Found" if no explicit expiration

### Authorized Signatory - Party A
- **Description:** Name and designation of the individual authorized to sign on behalf of Party A.
- **Format:** Full name and title (e.g., John Doe, VP of Operations). Extract from signature page or execution section.
- **Example:** `John Doe, VP of Operations`
- **Typical Location:**
  - Signature pages (typically last page or last few pages)
  - Execution section
  - May be in "Authorized Signatories" clause
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - If multiple signatories, combine with semicolons
  - Include full name and title/designation

### Authorized Signatory - Party B
- **Description:** Name and designation of the individual authorized to sign on behalf of Party B.
- **Format:** Full name and title (e.g., Jane Smith, CEO). Extract from signature page or execution section.
- **Example:** `Jane Smith, CEO`
- **Typical Location:**
  - Signature pages (typically last page or last few pages)
  - Execution section
  - May be in "Authorized Signatories" clause
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - If multiple signatories, combine with semicolons
  - Include full name and title/designation

---

## 3. Business Terms

### Document Type
- **Description:** Type of agreement as stated by the title or heading. Use 'MSA' for Master/Professional Services Agreement or 'Services Agreement'. Use 'NDA' for Non-Disclosure Agreement.
- **Format:** Must be exactly "MSA" or "NDA" (case-sensitive)
- **Example:** `MSA` or `NDA`
- **Typical Location:**
  - Document title/header (typically Page 1)
  - First page heading
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - Edge cases:
    - If document contains both MSA and NDA elements: Set to "MSA" if commercial terms (pricing, payment, termination) exist; otherwise "NDA"
    - If unclear (e.g., just "Services Agreement"): Default to "MSA" if pricing/term/termination are found; else "NDA"

### Termination Notice Period
- **Description:** Minimum written notice required to terminate the agreement.
- **Format:** "<number> days" (e.g., "30 days")
- **Example:** `30 days`
- **Typical Location:**
  - Termination sections (e.g., "Section Four – Termination")
  - "Notice" clause
  - "Termination" provisions
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - Accept various formats: "30 days", "thirty (30) calendar days", "1 month", "60 business days"
  - Normalize units: "1 month" = "30 days", "1 year" = "365 days"
  - Extract primary/default notice period for main agreement
  - If multiple periods exist, return primary agreement notice

---

## 4. Commercial Operations

### Billing Frequency
- **Description:** How often invoices are issued under the MSA.
- **Format:** Terms as stated
- **Example:** `Monthly`, `Quarterly`, `Milestone-based`, `As-invoiced`
- **Typical Location:**
  - "Payment" section
  - "Fees" section
  - "Compensation" section
  - "Commercial Terms" or "Financial Terms" sections
- **Section Reference:** *(To be filled from template)*
- **Notes:** May be in various section names related to payment/billing

### Payment Terms
- **Description:** Time allowed for payment after invoice submission.
- **Format:** Terms as stated (e.g., Net 30 days from invoice date)
- **Example:** `Net 30 days from invoice date`
- **Typical Location:**
  - "Payment" section
  - "Fees" section
  - "Compensation" section
  - "Commercial Terms" or "Financial Terms" sections
- **Section Reference:** *(To be filled from template)*
- **Notes:** May be in various section names related to payment/billing

### Expense Reimbursement Rules
- **Description:** Terms governing travel, lodging, and other reimbursable expenses.
- **Format:** Rules as stated (e.g., Reimbursed as per client travel policy, pre-approval required)
- **Example:** `Reimbursed as per client travel policy, pre-approval required`
- **Typical Location:**
  - "Expenses" section
  - "Reimbursement" clause
  - "Travel" or "Travel and Expenses" section
  - May be in "Payment" or "Compensation" sections
- **Section Reference:** *(To be filled from template)*
- **Notes:** May be embedded in payment/compensation sections

---

## 5. Finance Terms

### Pricing Model Type
- **Description:** Commercial structure indicated by references to hourly rates, work orders, and rate schedules.
- **Format:** Must be exactly one of: "Fixed", "T&M", "Subscription", or "Hybrid" (case-sensitive)
- **Example:** `Fixed`, `T&M`, `Subscription`, or `Hybrid`
- **Typical Location:**
  - Sections about work orders (e.g., "Section Three – Work Orders")
  - Rate schedules
  - "Commercial Terms" section
  - "Pricing" or "Compensation" sections
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - Normalize "Time and Materials" or "Time & Materials" to "T&M"
  - Use "T&M" if billed by hourly rates
  - Use "Fixed" or "Subscription" only if explicitly stated
  - If hybrid model (e.g., fixed base + hourly), set to "Hybrid"

### Currency
- **Description:** Settlement/monetary currency.
- **Format:** "USD", "INR", or "Not Found"
- **Example:** `USD`, `INR`, or `Not Found`
- **Typical Location:**
  - Any monetary amounts (e.g., insurance limits, payment terms, rate schedules)
  - "Payment" section
  - Rate schedules
  - Insurance requirements
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - Limited allowlist: "USD" or "INR" only (expandable later)
  - Infer from currency symbols ($ → USD, ₹ → INR)
  - If currency absent or not in allowlist: Return "Not Found"
  - If multiple currencies mentioned, prefer primary settlement currency

### Contract Value
- **Description:** Total contract value if explicitly stated; otherwise return "Not Found".
- **Format:** Decimal number with decimals (e.g., "50000.00") or "Not Found"
- **Example:** `50000.00` or `Not Found`
- **Typical Location:**
  - Work Orders/SOW references
  - "Contract Value" or "Total Value" clause
  - May be in preamble or summary
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - Always include decimals (e.g., "50000.00" not "50000")
  - Remove currency symbols and commas (e.g., "$50,000" → "50000.00")
  - Many MSAs defer value to Work Orders/SOWs - return "Not Found" if not specified in main agreement

---

## 6. Risk & Compliance

### Indemnification Clause Reference
- **Description:** Clause defining indemnity obligations and covered risks.
- **Format:** Section heading/number and 1-2 sentence excerpt (e.g., Section 12 – Indemnification: Each party agrees to indemnify...)
- **Example:** `Section 12 – Indemnification: Each party agrees to indemnify...`
- **Typical Location:**
  - "Risk" section
  - "Liability" section
  - "Indemnification" section
  - "Insurance" section
  - "Warranties" or "General Provisions" sections
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - Return "Not Found" if no explicit clause exists
  - Include section heading/number and brief excerpt

### Limitation of Liability Cap
- **Description:** Maximum financial liability for either party.
- **Format:** Cap as stated (e.g., Aggregate liability not to exceed fees paid in previous 12 months)
- **Example:** `Aggregate liability not to exceed fees paid in previous 12 months`
- **Typical Location:**
  - "Risk" section
  - "Liability" section
  - "Limitation of Liability" clause
  - "General Provisions" section
- **Section Reference:** *(To be filled from template)*
- **Notes:** May be in various liability-related sections

### Insurance Requirements
- **Description:** Types and minimum coverage levels required by client.
- **Format:** Requirements as stated (e.g., CGL $2M per occurrence; Workers Comp as per law)
- **Example:** `CGL $2M per occurrence; Workers Comp as per law`
- **Typical Location:**
  - "Insurance" section
  - "Risk" section
  - "Liability" section
  - May be in "General Provisions"
- **Section Reference:** *(To be filled from template)*
- **Notes:** May specify types (CGL, Workers Comp, etc.) and amounts

### Warranties / Disclaimers
- **Description:** Assurances or disclaimers related to service performance or quality.
- **Format:** Text as stated (e.g., Services to be performed in a professional manner; no other warranties implied)
- **Example:** `Services to be performed in a professional manner; no other warranties implied`
- **Typical Location:**
  - "Warranties" section
  - "Disclaimers" clause
  - "General Provisions" section
  - May be in "Service Level" or "Performance" sections
- **Section Reference:** *(To be filled from template)*
- **Notes:** May include both warranties and disclaimers

---

## 7. Legal Terms

### Governing Law
- **Description:** Jurisdiction whose laws govern the agreement, including venue/court location if specified.
- **Format:** Text as stated (e.g., 'Texas, USA' or 'Laws of the State of Texas; courts of Collin County, Texas')
- **Example:** `Texas, USA` or `Laws of the State of Texas; courts of Collin County, Texas`
- **Typical Location:**
  - Sections named "Governing Law"
  - "Jurisdiction" section
  - "Applicable Law" clause
  - "General Provisions" section
  - (e.g., "Section Seventeen – Governing Law")
- **Section Reference:** *(To be filled from template)*
- **Notes:** May include both governing law and venue/court location

### Confidentiality Clause Reference
- **Description:** Clause title/number and a brief excerpt describing confidentiality obligations and return of materials.
- **Format:** 'Section <number> – <title>: <1–2 sentence excerpt>'
- **Example:** `Section 8 – Confidential Information: Each party agrees to maintain confidentiality...`
- **Typical Location:**
  - Sections about confidential information (e.g., "Section Eight – Confidential Information")
  - "Confidentiality" section
  - "Non-Disclosure" clause
  - May be in "General Provisions"
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - Return "Not Found" if no explicit clause exists
  - Include section heading/number and brief excerpt

### Force Majeure Clause Reference
- **Description:** Clause title/number and short excerpt describing relief from obligations due to extraordinary events.
- **Format:** Section heading/number and brief excerpt, or "Not Found" if not present
- **Example:** `Section 15 – Force Majeure: Neither party shall be liable...` or `Not Found`
- **Typical Location:**
  - "Force Majeure" section (if present)
  - "General Provisions" section
  - May be embedded in other clauses
- **Section Reference:** *(To be filled from template)*
- **Notes:**
  - Return "Not Found" if no explicit clause exists
  - Search for "Force Majeure" explicitly
  - Consistent with all clause references - all return "Not Found" if absent

---

## Template Mapping Instructions

### For Each Field:
1. **Identify the clause/section number** from your template PDF
2. **Note the section heading** as it appears in the template
3. **Extract a sample excerpt** (1-2 sentences) from that section
4. **Document any variations** or alternative section names

### Example Mapping Format:
```
Field: Execution Date
Template Section: Section 18 - Execution
Section Number: 18
Section Heading: "Execution"
Sample Excerpt: "This Agreement shall be executed on the date last written below by both parties..."
Alternative Names: "Signing Date", "Date of Execution"
```

---

## Notes for Template Integration

1. **Section Numbers:** Document the exact section/clause numbers from your template
2. **Section Headings:** Note the exact wording of section headings
3. **Sample Excerpts:** Extract 1-2 sentence examples from each section
4. **Alternative Names:** Document any alternative section names that might appear
5. **Field Additions:** Use this document to identify which new fields to add based on your template
6. **Validation vs Extraction:** Decide whether to:
   - Keep validation separate (current skeleton approach)
   - Integrate template examples into extraction prompt
   - Add validation fields alongside extraction

---

## Architecture Decision Points

### Option A: Separate Validation (Current Skeleton)
- **Pros:** 
  - Clear separation of concerns
  - Can be disabled independently
  - Two-stage process (extract, then validate)
- **Cons:**
  - Two LLM calls (cost/time)
  - Validation may not inform extraction

### Option B: Integrated Extraction with Examples
- **Pros:**
  - Single LLM call
  - Examples guide extraction directly
  - More efficient
- **Cons:**
  - Larger prompt
  - Less flexible (harder to update validation separately)

### Option C: Hybrid Approach
- **Pros:**
  - Examples in extraction prompt for guidance
  - Separate validation for scoring/flags
  - Best of both worlds
- **Cons:**
  - More complex
  - Still two LLM calls

---

**Next Steps:**
1. Fill in "Section Reference" for each field from your template
2. Add sample excerpts from template sections
3. Identify any new fields to add
4. Decide on architecture approach (A, B, or C)
5. Update extraction/validation accordingly

