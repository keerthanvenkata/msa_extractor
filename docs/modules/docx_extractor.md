# DOCX Extractor

## Purpose

The `DOCXExtractor` class extracts text from Microsoft Word documents with style-based header detection.

## Features

- **Style-Based Header Detection**: Uses native DOCX styles (Heading 1, Heading 2, etc.)
- **Font Property Extraction**: Extracts font size, bold, italic
- **Structured Text Blocks**: Preserves paragraph structure
- **High Accuracy**: Better structure preservation than PDF extraction

## Header Detection

DOCX files have native style information:
- `Heading 1` → Level 1 header
- `Heading 2` → Level 2 header
- `Title` → Title/header
- `Normal` → Body text

This provides **95%+ accuracy** for header detection.

## Usage

```python
from extractors.docx_extractor import DOCXExtractor

extractor = DOCXExtractor(gemini_client=gemini_client)
result = extractor.extract("/path/to/contract.docx")

# Access extracted text
text = result.raw_text

# Access structured blocks
blocks = result.structured_text

# Access detected headers
headers = result.headers
```

## Output Structure

- **raw_text**: Full document text
- **structured_text**: List of text blocks with metadata
- **headers**: List of detected headers
- **metadata**: Extraction metadata (file_type, paragraph_count, etc.)

## Advantages Over PDF

- Better structure preservation
- Native style information
- No font size heuristics needed
- Exact header levels from styles

## Dependencies

- `python-docx`
- `ai.gemini_client` (optional, for LLM processing)

