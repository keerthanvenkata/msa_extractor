# Documentation Index

**Last Updated:** November 12, 2025

The `docs/` directory contains comprehensive documentation for the MSA Metadata Extractor project, organized into logical sections for easy navigation.

---

## 🚀 Quick Start

- **[Project Status](PROJECT_STATUS.md)** — Current status, completed features, and roadmap
- **[Architecture Overview](architecture/ARCHITECTURE.md)** — High-level system architecture and component overview
- **[Configuration Guide](setup/configuration.md)** — All environment variables and configuration options
- **[Setup Guides](#-setup--installation)** — Platform-specific installation instructions

---

## 📋 Planning & Design Documents

**Status:** Planning phase - these documents outline future implementations.

Located in [`planning/`](planning/):

- **[Persistence & Storage Plan](planning/PERSISTENCE_PLAN.md)** — SQLite database schema, file storage strategy, cleanup policies, and FastAPI backend design (P1 - Phase 1 & 2 Complete)
  - Database schema and file storage structure
  - Cleanup strategies (time-based and count-based) - Deferred to next iteration
  - FastAPI backend architecture and endpoints - Phase 4 pending
  - Docker configuration for API deployment

- **[API Design Specification](planning/API_DESIGN.md)** — Complete REST API endpoint specifications (P1 - Design Complete)
  - Endpoint definitions with request/response examples
  - Authentication strategy (API key for v1)
  - Client usage flow and polling strategy
  - Background task architecture
  - Configuration options

- **[Data Masking Plan](planning/DATA_MASKING_PLAN.md)** — Data masking/encryption strategy for security and compliance (P0 - Critical)
  - Security goals and requirements
  - Masking methods and re-mapping strategy
  - Configuration options

---

## 📊 Project Management

- **[Project Status](PROJECT_STATUS.md)** — Current project status, completed features, what's missing, and recommended next steps
- **[Issues & TODOs](ISSUES_AND_TODOS.md)** — Tracked bugs, TODOs, optimizations, and issues categorized by priority and type

---

## 📐 Requirements & Schema

- **[Requirements](REQUIREMENTS.md)** — **Canonical source** for field definitions, examples, extraction rules, and update checklist. **Always reference this when modifying the schema.**

---

## 🏗️ Architecture & Design

Located in [`architecture/`](architecture/):

- **[System Architecture](architecture/ARCHITECTURE.md)** — High-level system architecture, component overview, and data flow
- **[Extraction Architecture](architecture/EXTRACTION_ARCHITECTURE.md)** — Detailed extraction system design with content extraction methods and LLM processing modes

### Legacy Documentation

Located in [`legacy/`](legacy/):

- **[Extraction Modes (Legacy)](legacy/EXTRACTION_MODES.md)** — ⚠️ **DEPRECATED** - Legacy extraction modes guide (kept for reference only)

---

## 🔧 Setup & Installation

Located in [`setup/`](setup/):

### Platform-Specific Guides
- **[Windows OCR Setup](setup/windows_ocr_setup.md)** — Installing Tesseract, VC++ runtime, and optional Google Cloud Vision tooling on Windows
- **[Linux & Docker Setup](setup/LINUX_AND_DOCKER_SETUP.md)** — Setting up on Linux and Docker, including Dockerfile and docker-compose examples

### Configuration
- **[Configuration Reference](setup/configuration.md)** — Complete reference for all environment variables and configuration options

---

## 📚 Module Documentation

Located in [`modules/`](modules/):

### Core Extractors
- **[Base Extractor](modules/base_extractor.md)** — Abstract interface and shared utilities
- **[PDF Extractor](modules/pdf_extractor.md)** — Text and image-based PDF handling with new extraction architecture
- **[DOCX Extractor](modules/docx_extractor.md)** — DOCX text extraction with style detection

### Processing Components
- **[Image Preprocessor](modules/image_preprocessor.md)** — OpenCV pipeline for OCR accuracy
- **[OCR Handler](modules/ocr_handler.md)** — Multi-engine OCR support (Tesseract, GCV, Gemini Vision)
- **[Text Analyzer](modules/text_analyzer.md)** — Header detection and structure analysis
- **[PDF Preprocessing](modules/pdf_preprocessing.md)** — Detection logic and processing flows

### Integration & Coordination
- **[Strategy Factory](modules/strategy_factory.md)** — Extraction strategy selection and routing
- **[Gemini Vision Extractor](modules/gemini_vision_extractor.md)** — Direct Gemini Vision API integration
- **[Extraction Coordinator](modules/extraction_coordinator.md)** — Full pipeline orchestration
- **[Main CLI](modules/main_cli.md)** — Command-line interface with database tracking

### AI & Processing
- **[Gemini Client](modules/gemini_client.md)** — Gemini API integration for text, vision, and multimodal processing
- **[Schema Validator](modules/schema_validator.md)** — JSON schema validation and normalization

### Persistence & Storage
- **[Storage Database](modules/storage_database.md)** — SQLite database for job tracking, result storage, and logging

---

## 🔍 Feature Guides

Located in [`features/`](features/):

### Extraction Modes & Methods
- **[Multimodal Extraction](features/MULTIMODAL_EXTRACTION.md)** — Guide to multimodal extraction mode for signature pages and mixed PDFs
- **[OCR and Signatures](features/OCR_AND_SIGNATURES.md)** — Guide to OCR capabilities for signature extraction and handling pure images

### System Features
- **[Logging and Error Handling](features/LOGGING_AND_ERROR_HANDLING.md)** — Centralized logging configuration, custom exceptions, and error handling patterns
- **[Prompting Strategy Analysis](features/PROMPTING_STRATEGY_ANALYSIS.md)** — Analysis of current prompting approach and recommendations

---

## 📖 Documentation Structure

```
docs/
├── README.md (this file)
│
├── planning/              # Planning & Design Documents
│   ├── PERSISTENCE_PLAN.md
│   └── DATA_MASKING_PLAN.md
│
├── architecture/          # Architecture & Design
│   ├── ARCHITECTURE.md
│   └── EXTRACTION_ARCHITECTURE.md
│
├── setup/                 # Setup & Installation
│   ├── windows_ocr_setup.md
│   ├── LINUX_AND_DOCKER_SETUP.md
│   └── configuration.md
│
├── modules/               # Module Documentation
│   ├── base_extractor.md
│   ├── pdf_extractor.md
│   ├── docx_extractor.md
│   ├── image_preprocessor.md
│   ├── ocr_handler.md
│   ├── text_analyzer.md
│   ├── pdf_preprocessing.md
│   ├── strategy_factory.md
│   ├── gemini_vision_extractor.md
│   ├── extraction_coordinator.md
│   ├── main_cli.md
│   ├── gemini_client.md
│   ├── schema_validator.md
│   └── storage_database.md
│
├── features/              # Feature Guides
│   ├── MULTIMODAL_EXTRACTION.md
│   ├── OCR_AND_SIGNATURES.md
│   ├── LOGGING_AND_ERROR_HANDLING.md
│   └── PROMPTING_STRATEGY_ANALYSIS.md
│
├── legacy/                # Deprecated Documentation
│   └── EXTRACTION_MODES.md
│
├── PROJECT_STATUS.md      # Project Management
├── ISSUES_AND_TODOS.md
└── REQUIREMENTS.md        # Requirements & Schema
```

---

## 🔗 Key References in Codebase

The following files reference documentation:

- `config.py` → `docs/REQUIREMENTS.md` (field definitions)
- `ai/gemini_client.py` → `docs/REQUIREMENTS.md` (prompt specifications)
- `extractors/ocr_handler.py` → `docs/setup/windows_ocr_setup.md`, `docs/setup/LINUX_AND_DOCKER_SETUP.md`

---

## 📝 Documentation Standards

- **Module Guides:** Each module has a dedicated guide explaining responsibilities, configuration, and extension points
- **Planning Documents:** Clearly marked with status and priority
- **Deprecated Docs:** Marked with ⚠️ and reference to current documentation
- **Code References:** Use relative paths from docs root (e.g., `../architecture/EXTRACTION_ARCHITECTURE.md`)

---

## 🎯 Quick Reference

### Most Frequently Used
1. **[Configuration](setup/configuration.md)** — Environment variables reference
2. **[Extraction Architecture](architecture/EXTRACTION_ARCHITECTURE.md)** — How extraction works
3. **[Requirements](REQUIREMENTS.md)** — Field definitions and schema
4. **[Project Status](PROJECT_STATUS.md)** — Current state and roadmap

### For Developers
1. **[Module Guides](modules/)** — Component-level documentation
2. **[Architecture](architecture/ARCHITECTURE.md)** — System design overview
3. **[Issues & TODOs](ISSUES_AND_TODOS.md)** — Known issues and planned work

### For Setup
1. **[Windows Setup](setup/windows_ocr_setup.md)** — Windows installation
2. **[Linux & Docker Setup](setup/LINUX_AND_DOCKER_SETUP.md)** — Linux/Docker installation
3. **[Configuration](setup/configuration.md)** — Configuration options

---

Each guide includes module responsibilities, configuration toggles, and extension points to keep the codebase modular and easy to extend.
