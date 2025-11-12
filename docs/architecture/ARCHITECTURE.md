# System Architecture

**Last Updated:** November 12, 2025

## Overview

The MSA Metadata Extractor is a modular system designed to extract structured metadata from Master Service Agreements (MSAs) using a combination of text extraction, OCR, and Large Language Models (LLMs).

## High-Level Architecture

```
┌─────────────────┐
│   Input Files   │
│  (PDF, DOCX)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     Strategy Factory                │
│  (Routes to appropriate extractor)   │
└────────┬────────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│  PDF   │ │   DOCX   │
│Extractor│ │Extractor│
└────┬───┘ └────┬─────┘
     │          │
     └────┬─────┘
          │
          ▼
┌─────────────────────┐
│ Extraction          │
│ Coordinator         │
│ (Orchestrates flow)  │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌──────────┐
│   OCR   │  │   Text   │
│ Handler │  │ Analyzer │
└────┬────┘  └────┬─────┘
     │            │
     └─────┬──────┘
           │
           ▼
┌─────────────────────┐
│   Gemini Client     │
│  (LLM Processing)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Schema Validator   │
│ (Validation & Norm) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Output JSON       │
│  (Structured Data)  │
└─────────────────────┘
```

## Core Components

### 1. Extractors
- **PDFExtractor**: Handles PDF files (text, image, mixed)
- **DOCXExtractor**: Handles DOCX files
- **GeminiVisionExtractor**: Direct vision-based extraction

### 2. Processing Pipeline
- **StrategyFactory**: Routes files to appropriate extractor
- **ExtractionCoordinator**: Orchestrates the full extraction pipeline
- **OCRHandler**: Multi-engine OCR support (Tesseract, GCV)
- **ImagePreprocessor**: OpenCV-based image enhancement

### 3. AI Integration
- **GeminiClient**: Handles both text and vision LLM calls
- **SchemaValidator**: Validates and normalizes extracted metadata

### 4. Persistence & Storage
- **ExtractionDB**: SQLite database for job tracking, result storage, and logging
- **File Storage**: Temporary PDF storage in `uploads/{uuid}.{ext}` directory
- **Database Storage**: JSON results and logs stored in database (default mode)
- **Legacy Mode**: File-based storage support for backward compatibility

### 5. Utilities
- **Logger**: Centralized logging system
- **Exceptions**: Custom exception hierarchy

## Extraction Architecture

The system uses a two-tier architecture:

1. **Content Extraction Methods** (`EXTRACTION_METHOD`):
   - How to extract content from PDF pages
   - Options: `text_direct`, `ocr_all`, `ocr_images_only`, `vision_all`, `hybrid`

2. **LLM Processing Modes** (`LLM_PROCESSING_MODE`):
   - How to process extracted content with LLMs
   - Options: `text_llm`, `vision_llm`, `multimodal`, `dual_llm`

See [EXTRACTION_ARCHITECTURE.md](EXTRACTION_ARCHITECTURE.md) for detailed information.

## Data Flow

1. **Input**: PDF or DOCX file
2. **Job Creation**: Create database job with UUID, copy file to `uploads/{uuid}.{ext}`
3. **Detection**: File type and PDF characteristics (text/image/mixed)
4. **Extraction**: Content extraction based on `EXTRACTION_METHOD`
5. **Processing**: LLM processing based on `LLM_PROCESSING_MODE`
6. **Validation**: Schema validation and normalization
7. **Storage**: Store results in database (`extractions.result_json`) or files (legacy mode)
8. **Output**: Structured JSON metadata with job ID

## Configuration

All configuration is environment-based:
- Environment variables (`.env` file)
- No hardcoded paths
- Cross-platform compatible

See [configuration.md](../setup/configuration.md) for all configuration options.

## Persistence Architecture

### Current Implementation (Phase 1 & 2 Complete)
- **Database Layer**: SQLite database (`storage/msa_extractor.db`)
  - `extractions` table: Job tracking with UUID primary keys
  - `extraction_logs_YYYY_MM` tables: Monthly log tables
  - JSON results stored in `result_json` column (default mode)
- **File Storage**: PDFs stored in `uploads/{uuid}.{ext}` directory
- **CLI Integration**: Database tracking in all extraction commands
- **Legacy Mode**: File-based storage support (`--legacy` flag)

### Future Components (Phase 3 & 4 Pending)
- **Cleanup Service**: Automated PDF cleanup after N days
- **API Layer**: FastAPI backend for web service
- **GCS Integration**: Migrate PDF storage to Google Cloud Storage
- **Cloud SQL**: Migrate from SQLite to Cloud SQL PostgreSQL

See [PERSISTENCE_PLAN.md](../planning/PERSISTENCE_PLAN.md) and [IMPLEMENTATION_ROADMAP.md](../planning/IMPLEMENTATION_ROADMAP.md) for details.

## Related Documentation

- [Extraction Architecture](EXTRACTION_ARCHITECTURE.md) - Detailed extraction system design
- [Configuration](../setup/configuration.md) - All configuration options
- [Module Guides](README.md#module-guides) - Individual component documentation

