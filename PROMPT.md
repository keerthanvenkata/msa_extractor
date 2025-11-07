# Project Prompt

You are helping build a Python-based contract intelligence system called **MSA Metadata Extractor**.
The system’s purpose is to read *Master Service Agreements (MSAs)* and extract a stable, well-defined set of metadata fields into structured, machine-readable JSON for downstream workflows.

---


GOAL
----
- Ingest contracts (PDF / DOCX), extract text, and produce a validated JSON metadata object that follows a fixed schema.
- Provide clause-level references when present (e.g., "Section 12 – Indemnification").
- Be modular and extensible — this prompt should serve as the long-lived project intent and style guide.

Primary use-cases:
1. Single-file extract → JSON output (for manual review).
2. Batch processing of multiple MSAs.
3. Later: clause linking, export to CSV/Excel, and searchable contract store.

---

CORE METADATA SCHEMA
--------------------
All outputs MUST follow this exact JSON structure. If a value cannot be found, return the string `"Not Found"` (do not return null, empty list, or other placeholders).

**IMPORTANT**: See `docs/REQUIREMENTS.md` for the canonical field definitions, examples, and update checklist.

{
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

**Field Definitions** (see `docs/REQUIREMENTS.md` for complete definitions):

**Contract Lifecycle:**
- Execution Date: Date when both parties have signed the agreement. Format: ISO yyyy-mm-dd (e.g., 2025-03-14)
- Effective Date: Date the MSA becomes legally effective (may differ from execution). Format: ISO yyyy-mm-dd (e.g., 2025-04-01)
- Expiration / Termination Date: Date on which the agreement expires or terminates unless renewed. Format: ISO yyyy-mm-dd or "Evergreen" if auto-renews (e.g., 2028-03-31 or Evergreen)
- Authorized Signatory: Name and designation of the individual authorized to sign on behalf of each party. Format: Full name and title (e.g., John Doe, VP of Operations). If multiple, separate with semicolons.

**Commercial Operations:**
- Billing Frequency: How often invoices are issued under the MSA. Examples: Monthly, Quarterly, Milestone-based, As-invoiced
- Payment Terms: Time allowed for payment after invoice submission. Format: Terms as stated (e.g., Net 30 days from invoice date)
- Expense Reimbursement Rules: Terms governing travel, lodging, and other reimbursable expenses. Format: Rules as stated (e.g., Reimbursed as per client travel policy, pre-approval required)

**Risk & Compliance:**
- Indemnification Clause Reference: Clause defining indemnity obligations and covered risks. Format: Section heading/number and 1-2 sentence excerpt (e.g., Section 12 – Indemnification: Each party agrees to indemnify...)
- Limitation of Liability Cap: Maximum financial liability for either party. Format: Cap as stated (e.g., Aggregate liability not to exceed fees paid in previous 12 months)
- Insurance Requirements: Types and minimum coverage levels required by client. Format: Requirements as stated (e.g., CGL $2M per occurrence; Workers Comp as per law)
- Warranties / Disclaimers: Assurances or disclaimers related to service performance or quality. Format: Text as stated (e.g., Services to be performed in a professional manner; no other warranties implied)

---

LLM PROMPTING PHILOSOPHY
-------------------------
- Always ask the LLM to **return valid JSON only** in the schema above.
- Use an explicit role: "You are a contract analyst".
- Provide the schema in the prompt (literal JSON).
- Ask the model to fill "Not Found" for missing fields.
- Prefer concise contextual text: limit request to ~10–12k characters. For longer docs, implement chunking + aggregation (future).
- When extracting clause references, ask for the nearest heading/section number and a short excerpt (1-2 sentences).
- Add a follow-up step to validate/parse dates into ISO format; if ambiguous, return the literal string the model found and flag as "AmbiguousDate".

Example prompt template (use exactly this pattern in code when calling Gemini):
"""
You are a contract analyst. Extract the following metadata fields from the given Master Service Agreement and return VALID JSON ONLY matching this schema:

<insert full JSON schema here>

Rules:
1. If a field cannot be determined, use "Not Found" (never null, empty list, or other placeholders).
2. For dates:
   - Preferred format: ISO yyyy-mm-dd (e.g., 2025-03-14)
   - If ambiguous or unclear: Return the literal text found and include "(AmbiguousDate)" as a flag
   - Example: "March 14, 2025 (AmbiguousDate)" or "Q1 2025 (AmbiguousDate)"
3. For "Expiration / Termination Date":
   - If contract is "Evergreen" (auto-renews): Return "Evergreen"
   - If no explicit expiration: Return "Not Found"
4. For "Indemnification Clause Reference":
   - Return the section heading/number and a 1–2 sentence excerpt
   - Example: "Section 12 – Indemnification: Each party agrees to indemnify..."
5. For fields with multiple values (e.g., multiple signatories):
   - Combine with semicolons
   - Example: "John Doe, VP of Operations; Jane Smith, CFO"
6. Return no commentary, no extra keys, and no markdown — JSON only.

MSA TEXT:
\"\"\"<contract text here>\"\"\"
"""

---

SYSTEM ARCHITECTURE (recommended phases)
---------------------------------------
Phase 1 — Stable foundation (this project base)
- Pipeline:
  1. File upload (PDF/DOCX)
  2. Text extraction (PyMuPDF for PDFs, python-docx for DOCX)
  3. Optional OCR fallback for scanned PDFs (Tesseract or Google Vision, future)
  4. LLM call (Gemini via google-generativeai) using the prompt template
  5. Post-process: JSON validation, date normalization, CSV/Excel export
  6. UI: Streamlit or Gradio for human review and file upload
- Persistence: store JSON results in a local SQLite DB or files/JSON directory.

Phase 2 — improvements
- Chunking with retrieval, embeddings for long contracts.
- Clause-level linking (store clause text + offsets).
- Confidence scoring per field (model-provided or heuristic).
- Better OCR workflow and noise cleaning.

Phase 3 — enterprise
- Multi-contract analytics, role-based access, audit logs.
- Integration with contract lifecycle management (CLM) systems.
- Fine-tuning or supervised LLM workflow for higher accuracy.

---

TECH STACK & LIBRARIES
----------------------
- Python 3.10+
- LLM: Google Gemini (google-generativeai)
- PDF Text: PyMuPDF (fitz)
- DOCX: python-docx
- OCR (optional/future): Tesseract or cloud OCR
- UI: Streamlit (recommended) or Gradio
- Data: pandas, openpyxl for exports; SQLite for persistence
- Testing: pytest for unit tests
- Optional later: LangChain/LlamaIndex for chunking/retrieval

---

RECOMMENDED PROJECT STRUCTURE
-----------------------------
msa_extractor/
├── main.py                   # CLI / Streamlit entry
├── config.py                 # env var loader, model selection, constants
├── extractors/
│   ├── pdf_extractor.py      # PyMuPDF text extraction + OCR fallback hooks
│   ├── docx_extractor.py     # DOCX extraction
│   └── __init__.py
├── ai/
│   ├── gemini_client.py      # LLM prompt templates + request/response wrapper
│   └── schema.py             # canonical JSON schema + validator
├── processors/
│   ├── postprocess.py        # date normalization, field cleaning, confidence heuristics
│   └── clause_finder.py      # clause extraction & reference finder
├── storage/
│   ├── sqlite_store.py       # save results / metadata
│   └── file_store.py         # json/csv export helpers
├── ui/
│   ├── streamlit_app.py
│   └── gradio_app.py         # optional
├── tests/
│   ├── test_extraction.py
│   └── test_gemini_prompts.py
└── README.md

Coding style:
- Write clear docstrings with example inputs/outputs.
- Keep LLM prompts versioned and in a separate file or module.
- Use .env for API keys (never hardcode).
- Make components testable / mockable (e.g., ability to mock Gemini responses).

---

DEVELOPMENT PRINCIPLES (long-term)
---------------------------------
- Backwards compatibility: do not change the JSON schema without a migration plan.
- Prompts are first-class: store them under ai/prompts/ with names and versions.
- Separate concerns: text extraction, LLM prompting, post-processing, and storage should be independently replaceable.
- Observability: log inputs, prompt versions, and outputs (redact secrets).
- QA: build a small labeled dataset of ~20–50 representative MSAs to validate changes.
- Security/privacy: encrypt stored contracts if used with real data; follow org policies.

---

WHEN GENERATING CODE
--------------------
- Respect the project folder layout above.
- Add defensive checks for file types and text extraction failures.
- Include unit tests for extraction and JSON validation.
- Use the exact JSON schema shown for all outputs.
- Provide clear README entries for how to run locally (including `.env` setup).
- When suggesting prompt changes, provide before/after prompt text and a short rationale.

---

EXAMPLE CLI USAGE (developer convenience)
----------------------------------------
# Single-file run
python main.py --file ./contracts/example_msa.pdf --out ./results/example_msa.json

# Batch run
python main.py --dir ./contracts --out-dir ./results --parallel 4

---

CURSOR / AI AGENT BEHAVIOR
-------------------------
When operating inside Cursor IDE (or any AI-assisted code generation for this project):
- Always follow this project prompt as authoritative.
- When asked to write code, include tests and docstrings.
- Suggest improvements but avoid breaking the schema.
- For changes that could affect downstream users, propose a migration plan.
- Default to using Gemini for tasks involving contract understanding unless explicitly asked to switch.

---


END OF PROMPT
