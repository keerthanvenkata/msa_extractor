# ADR-0006: SQLite Database Choice for v1

**Status:** Accepted  
**Date:** November 2025 (estimated)  
**Deciders:** Development Team  
**Tags:** database, persistence, architecture

## Context

Needed a database solution for job tracking, result storage, and logging. Requirements:
- Simple setup (no separate database server)
- Suitable for MVP/production v1
- Easy migration path to cloud database later
- File-based for Cloud Run compatibility
- Support for JSON storage

## Decision

Chose **SQLite** for v1 with a clear migration path to Cloud SQL PostgreSQL for future iterations.

## Consequences

### Positive
- **Zero configuration**: No separate database server needed
- **File-based**: Works with Cloud Run ephemeral storage
- **Simple deployment**: Database file included in container
- **Fast for MVP**: Sufficient performance for initial scale
- **JSON support**: Native JSON columns for storing results
- **Migration path**: Schema designed for easy Cloud SQL migration

### Negative
- **Concurrency limits**: SQLite has write concurrency limitations
- **Not distributed**: Single file, can't scale horizontally
- **File size limits**: Large databases can be slow
- **No advanced features**: Missing some PostgreSQL features

### Neutral
- **Cloud Run compatible**: Works with ephemeral storage
- **Future migration**: Schema designed for PostgreSQL compatibility

## Alternatives Considered

1. **PostgreSQL from start**:
   - Pros: More features, better concurrency, production-ready
   - Cons: Requires managed database service, more complex setup
   - **Rejected** - Overkill for MVP, adds complexity

2. **NoSQL (MongoDB/Firestore)**:
   - Pros: Flexible schema, good for JSON
   - Cons: Different query model, migration complexity
   - **Rejected** - SQL queries needed, relational structure preferred

3. **File-based JSON only**:
   - Pros: Simplest
   - Cons: No querying, no job tracking, hard to scale
   - **Rejected** - Need database features

## Implementation Notes

- SQLite database at `storage/msa_extractor.db`
- Monthly log tables (`extraction_logs_YYYY_MM`) for efficient management
- JSON results stored in `result_json` column
- Schema designed for PostgreSQL migration (no SQLite-specific features)
- Legacy mode supports file-based storage for backward compatibility

