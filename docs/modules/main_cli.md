# Main CLI

**Module:** `main`  
**Last Updated:** November 11, 2025

## Purpose

The `main.py` module provides a command-line interface for:
- Single-file metadata extraction
- Batch processing of multiple contracts
- Configuration validation
- Strategy selection

## Usage

### Single File Extraction

```bash
# Extract and save to file
python main.py --file ./contracts/example.pdf --out ./results/example.json

# Extract and print to stdout
python main.py --file ./contracts/example.pdf

# Use specific strategy
python main.py --file ./contracts/example.pdf --strategy gemini_vision
```

### Batch Processing

```bash
# Process all PDFs/DOCX in directory
python main.py --dir ./contracts --out-dir ./results

# Use specific strategy for all files
python main.py --dir ./contracts --strategy tesseract
```

### Configuration Validation

```bash
# Validate configuration only
python main.py --validate-only
```

## Command-Line Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `--file` | Path to input file (PDF or DOCX) | For single file |
| `--dir` | Directory containing input files | For batch processing |
| `--out` | Output file path | Optional (single file) |
| `--out-dir` | Output directory | Optional (batch) |
| `--strategy` | Extraction strategy | Optional |
| `--parallel` | Number of parallel processes | Optional (not yet implemented) |
| `--validate-only` | Only validate configuration | Optional |

## Output

### Single File

- JSON file with extracted metadata (if `--out` specified)
- Prints to stdout if no output file specified

### Batch Processing

- Individual JSON files for each input file
- `batch_summary.json` with processing results

## Error Handling

- Returns exit code 0 on success
- Returns exit code 1 on error
- Logs errors to stderr
- Continues processing remaining files in batch mode

## Examples

```bash
# Extract from PDF
python main.py --file contract.pdf --out metadata.json

# Batch process with auto strategy
python main.py --dir ./contracts --out-dir ./results

# Use Tesseract OCR for scanned PDFs
python main.py --file scanned.pdf --strategy tesseract

# Validate setup
python main.py --validate-only
```

