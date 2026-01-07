"""
Validation templates and examples for MSA metadata validation.

Contains industry-standard examples, negotiability flags, and acceptable deviations
for each metadata field. Used by ValidatorService to validate extracted metadata.
"""

# TODO: Populate with actual templates and examples from widely accepted MSA templates
# Structure: Category -> Field -> Template Info

VALIDATION_TEMPLATES = {
    "Contract Lifecycle": {
        "Execution Date": {
            "example": "2025-03-14",
            "description": "ISO format date (yyyy-mm-dd) when contract was signed by both parties",
            "negotiable": False,
            "compulsory": True,
            "acceptable_deviations": [
                "AmbiguousDate flag acceptable if date format unclear",
                "Can be relative to Effective Date"
            ],
            "scoring_criteria": {
                "present_and_valid": 100,
                "present_with_ambiguous_flag": 90,
                "missing": 0
            },
            "what_to_look_for": [
                "Signature pages",
                "Execution section",
                "Date format consistency"
            ]
        },
        "Effective Date": {
            "example": "2025-04-01",
            "description": "ISO format date when contract becomes legally effective",
            "negotiable": True,
            "compulsory": True,
            "acceptable_deviations": [
                "May be same as Execution Date",
                "AmbiguousDate flag acceptable"
            ],
            "scoring_criteria": {
                "present_and_valid": 100,
                "present_with_ambiguous_flag": 90,
                "missing": 0
            },
            "what_to_look_for": [
                "Effective Date clause",
                "Commencement section",
                "May be defined relative to Execution Date"
            ]
        },
        # TODO: Add all other fields with templates
    },
    "Business Terms": {
        "Document Type": {
            "example": "MSA",
            "description": "Type of agreement: MSA or NDA",
            "negotiable": False,
            "compulsory": True,
            "acceptable_deviations": [],
            "scoring_criteria": {
                "exact_match_msa_or_nda": 100,
                "missing": 0
            },
            "what_to_look_for": [
                "Document title/header",
                "First page heading"
            ]
        },
        # TODO: Add other Business Terms fields
    },
    # TODO: Add all other categories
}

# Field-level validation rules
FIELD_VALIDATION_RULES = {
    "required_fields": [
        "Contract Lifecycle.Execution Date",
        "Contract Lifecycle.Effective Date",
        "Contract Lifecycle.Party A",
        "Contract Lifecycle.Party B",
        "Business Terms.Document Type"
    ],
    "negotiable_fields": [
        "Commercial Operations.Payment Terms",
        "Commercial Operations.Billing Frequency",
        "Finance Terms.Contract Value",
        "Risk & Compliance.Limitation of Liability Cap"
    ],
    "high_risk_fields": [
        "Risk & Compliance.Indemnification Clause Reference",
        "Risk & Compliance.Limitation of Liability Cap",
        "Legal Terms.Governing Law"
    ]
}


