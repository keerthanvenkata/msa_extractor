# System Architecture

**Last Updated:** January 7, 2025

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

### 4. Utilities
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
2. **Detection**: File type and PDF characteristics (text/image/mixed)
3. **Extraction**: Content extraction based on `EXTRACTION_METHOD`
4. **Processing**: LLM processing based on `LLM_PROCESSING_MODE`
5. **Validation**: Schema validation and normalization
6. **Output**: Structured JSON metadata

## Configuration

All configuration is environment-based:
- Environment variables (`.env` file)
- No hardcoded paths
- Cross-platform compatible

See [configuration.md](../setup/configuration.md) for all configuration options.

## Future Architecture

### Planned Components
- **Storage Layer**: SQLite database for job tracking
- **API Layer**: FastAPI backend for web service
- **Cleanup Service**: Automated file cleanup

See [PERSISTENCE_PLAN.md](../planning/PERSISTENCE_PLAN.md) for details.

## Related Documentation

- [Extraction Architecture](EXTRACTION_ARCHITECTURE.md) - Detailed extraction system design
- [Configuration](../setup/configuration.md) - All configuration options
- [Module Guides](README.md#module-guides) - Individual component documentation

