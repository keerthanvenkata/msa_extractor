# Documentation Index

The `docs/` directory contains module-level guides and setup references for the MSA Metadata Extractor project.

## Requirements & Schema

- **[REQUIREMENTS.md](REQUIREMENTS.md)** — **Canonical source** for field definitions, examples, extraction rules, and update checklist. **Always reference this when modifying the schema.**

## Project Management

- **[ISSUES_AND_TODOS.md](ISSUES_AND_TODOS.md)** — Tracked bugs, TODOs, optimizations, and issues categorized by priority and type. Updated during code reviews and paper-based testing.

## Module Guides

### Core Extractors
- [Base Extractor](base_extractor.md) — abstract interface and shared utilities
- [PDF Extractor](pdf_extractor.md) — text and image-based PDF handling
- [DOCX Extractor](docx_extractor.md) — DOCX text extraction with style detection
- [Image Preprocessor](image_preprocessor.md) — OpenCV pipeline for OCR accuracy
- [OCR Handler](ocr_handler.md) — multi-engine OCR support (Tesseract, GCV, Gemini Vision)
- [Text Analyzer](text_analyzer.md) — header detection and structure analysis

### Integration & Coordination
- [Strategy Factory](strategy_factory.md) — extraction strategy selection and routing
- [Gemini Vision Extractor](gemini_vision_extractor.md) — direct Gemini Vision API integration
- [Extraction Coordinator](extraction_coordinator.md) — full pipeline orchestration
- [Main CLI](main_cli.md) — command-line interface

### AI & Processing
- [Gemini Client](gemini_client.md) — Gemini API integration for text and vision
- [Schema Validator](schema_validator.md) — JSON schema validation and normalization

### Configuration & Setup
- [Configuration](configuration.md) — environment variables and strategy selection
- [PDF Preprocessing](pdf_preprocessing.md) — detection logic and processing flows

## Setup Guides

- [Windows OCR & Dependency Setup](windows_ocr_setup.md) — installing Tesseract, VC++ runtime, and optional Google Cloud Vision tooling

## System & Infrastructure

- [Logging and Error Handling](LOGGING_AND_ERROR_HANDLING.md) — centralized logging configuration, custom exceptions, and error handling patterns
- [Prompting Strategy Analysis](PROMPTING_STRATEGY_ANALYSIS.md) — analysis of current prompting approach and recommendations

Each guide includes module responsibilities, configuration toggles, and extension points to keep the codebase modular and easy to extend.
