# Main CLI

**Module:** `main`  
**Last Updated:** November 12, 2025

## Purpose

The `main.py` module provides a command-line interface for:
- Single-file metadata extraction with database tracking
- Batch processing of multiple contracts
- Job management (list, get, re-run)
- Configuration validation
- Legacy mode support (file-based storage)

## Usage

### Single File Extraction (Database Mode - Default)

```bash
# Extract with database tracking (default)
python main.py extract --file ./contracts/example.pdf

# Output: Job ID and metadata JSON
# Job ID: abc-123-def-456
# { "Contract Lifecycle": { ... } }

# Extract in legacy mode (file-based storage)
python main.py extract --file ./contracts/example.pdf --legacy --out ./results/example.json

# Re-run a failed job
python main.py extract --file ./contracts/example.pdf --job-id abc-123-def-456
```

### Batch Processing

```bash
# Batch extract with database tracking
python main.py extract --dir ./contracts/

# Batch extract in legacy mode
python main.py extract --dir ./contracts/ --legacy --out-dir ./results/
```

### Job Management

```bash
# List all jobs
python main.py list-jobs

# List jobs by status
python main.py list-jobs --status completed

# Get job details
python main.py get-job abc-123-def-456

# Validate configuration
python main.py validate
```

## Database Integration

The CLI now integrates with the persistence system:

- **Default Mode:** All jobs tracked in SQLite database
  - JSON results stored in `extractions.result_json` column
  - Logs stored in `extraction_logs` monthly tables
  - PDFs stored in `uploads/{uuid}.{ext}` directory
  - Job UUID returned for tracking

- **Legacy Mode:** File-based storage (`--legacy` flag)
  - JSON results saved to `results/{uuid}.json` files
  - Database still tracks job metadata
  - Backward compatible with existing workflows

See [Storage Database Module](storage_database.md) for details.

## Command-Line Arguments

### Extract Command

| Argument | Description | Required |
|----------|-------------|----------|
| `--file` | Path to input file (PDF or DOCX) | For single file |
| `--dir` | Directory containing input files | For batch processing |
| `--out` | Output file path (legacy mode only) | Optional |
| `--out-dir` | Output directory (legacy mode only) | Optional |
| `--strategy` | Extraction strategy (deprecated) | Optional |
| `--parallel` | Number of parallel processes | Optional (not yet implemented) |
| `--legacy` | Use file-based storage | Optional |
| `--job-id` | Re-run existing job by ID | Optional |

### List Jobs Command

| Argument | Description | Required |
|----------|-------------|----------|
| `--status` | Filter by status (`pending`, `processing`, `completed`, `failed`) | Optional |
| `--limit` | Maximum number of jobs to return | Optional (default: 50) |

### Get Job Command

| Argument | Description | Required |
|----------|-------------|----------|
| `job_id` | Job UUID | Required |

## Output

### Single File (Database Mode)

- Job ID printed to stdout
- Metadata JSON printed to stdout
- Results stored in database

### Single File (Legacy Mode)

- JSON file saved to `results/{uuid}.json` or `--out` path
- Job ID printed to stdout

### Batch Processing (Database Mode)

- Job IDs printed to stdout
- Results stored in database
- No individual JSON files

### Batch Processing (Legacy Mode)

- Individual JSON files for each input file
- `batch_summary.json` with processing results
- Job IDs printed to stdout

## Error Handling

- Returns exit code 0 on success
- Returns exit code 1 on error
- Failed jobs tracked in database with error messages
- Logs errors to database and stderr
- Continues processing remaining files in batch mode

## Examples

```bash
# Extract with database tracking (default)
python main.py extract --file contract.pdf

# Extract in legacy mode
python main.py extract --file contract.pdf --legacy --out metadata.json

# Batch extract
python main.py extract --dir ./contracts/

# List completed jobs
python main.py list-jobs --status completed

# Get job details
python main.py get-job abc-123-def-456

# Re-run failed job
python main.py extract --file contract.pdf --job-id abc-123-def-456

# Validate configuration
python main.py validate
```

