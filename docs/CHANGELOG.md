# Changelog

All notable changes to the MSA Metadata Extractor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-08

### Added
- **Enhanced Schema Structure**: Each field now includes `extracted_value`, `match_flag`, and `validation` object
- **Per-Field Validation**: Integrated validation with scores (0-100), status (valid/warning/invalid/not_found), and optional notes
- **Match Flags**: Template comparison flags (`same_as_template`, `similar_not_exact`, `different_from_template`, `flag_for_review`, `not_found`)
- **Config Refactoring**: Separated `FIELD_INSTRUCTIONS` and `TEMPLATE_REFERENCES` from prompt builder
- **Template Integration**: Support for template clause references, sample answers, and clause names
- **Integrated Validation**: Validation performed in same LLM call as extraction (single API call, more efficient)
- **Architecture Decision Records (ADRs)**: Added ADRs for major architectural decisions

### Changed
- **Breaking Change**: Schema structure changed from simple strings to enhanced objects
- **Prompt Builder**: Now uses config-based instructions instead of hardcoded rules
- **Schema Validator**: Updated to handle enhanced structure with validation
- **API Response Models**: Updated examples to show new structure
- **Documentation**: Comprehensive updates across all documentation files

### Deprecated
- **Validator Service**: Moved to `legacy/` folder (deprecated in favor of integrated validation)

### Removed
- **Legacy Compatibility**: Removed backward compatibility code for simpler implementation

### Fixed
- Version references updated to v2.0.0 across all documentation
- Date references updated to January 2026

## [1.1.0] - 2025-12-XX

### Added
- New metadata fields: Organization Name, Document Type, Termination Notice Period, Pricing Model Type, Currency, Contract Value, Governing Law, Confidentiality Clause Reference, Force Majeure Clause Reference
- New categories: Org Details, Business Terms, Finance Terms, Legal Terms

## [1.0.0] - 2025-11-XX

### Added
- Initial release
- PDF and DOCX extraction
- Multimodal LLM processing
- RESTful API with FastAPI
- SQLite database for job tracking
- Schema validation and normalization

