# Text Analyzer

**Module:** `extractors.text_analyzer`  
**Last Updated:** November 11, 2025

## Purpose

The `TextAnalyzer` class provides heuristics-based header detection and text structure analysis for extracted text blocks.

## Features

- **Header Detection**: Identifies headers using multiple heuristics
- **Level Assignment**: Assigns hierarchical levels (1-6) to headers
- **Text Structuring**: Organizes text into hierarchical sections

## Header Detection Heuristics

1. **Font Size Analysis**:
   - Headers typically 1.2x - 2.5x larger than body text
   - Top 10-15% of font sizes likely headers

2. **Style Indicators**:
   - Bold text more likely to be headers
   - Italic less likely (often emphasis)

3. **Position Analysis**:
   - Text at top of page/section
   - Centered text
   - More whitespace around

4. **Pattern Matching**:
   - Section numbers ("Section 12", "Article 3.1")
   - All caps text
   - Short lines (1-3 words)

5. **Confidence Scoring**: Combines multiple indicators for confidence score

## Usage

```python
from extractors.text_analyzer import TextAnalyzer

analyzer = TextAnalyzer()

# Detect headers from text blocks
headers = analyzer.detect_headers(text_blocks)

# Assign hierarchical levels
headers = analyzer.assign_header_levels(headers)

# Structure text into sections
structure = analyzer.structure_text(text_blocks)
```

## Output

- **Headers**: List of detected headers with confidence scores
- **Levels**: Hierarchical levels (1-6) assigned to headers
- **Structure**: Organized text with sections and body text

## Dependencies

- Standard library only (statistics, re, logging)

