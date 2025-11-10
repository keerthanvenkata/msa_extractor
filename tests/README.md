# Test Suite

Basic smoke tests and unit tests for MSA Metadata Extractor.

## Running Tests

### Run all tests:
```bash
pytest
```

### Run only fast tests (skip slow tests):
```bash
pytest -m "not slow"
```

### Run with verbose output:
```bash
pytest -v
```

### Run specific test file:
```bash
pytest tests/test_schema.py
```

### Run specific test:
```bash
pytest tests/test_schema.py::TestSchemaValidator::test_validate_complete_metadata
```

## Test Structure

- `conftest.py` - Pytest configuration and fixtures
- `test_schema.py` - Schema validation and normalization tests
- `test_extraction_coordinator.py` - Smoke tests for extraction pipeline
- `test_retry_logic.py` - Retry logic tests

## Test Markers

- `@pytest.mark.slow` - Tests that take longer (e.g., actual API calls)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests

## Fixtures

- `sample_pdf_path` - Path to a sample PDF file from `scratch/` directory
- `mock_gemini_client` - Mock Gemini client for testing
- `temp_output_dir` - Temporary output directory for tests

## Notes

- Some tests require API keys (marked with `@pytest.mark.slow`)
- Tests will skip if sample PDFs are not found
- Mock tests don't require API keys

