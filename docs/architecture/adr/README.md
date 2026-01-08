# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) documenting major architectural decisions made during the development of the MSA Metadata Extractor.

## What are ADRs?

ADRs are documents that capture important architectural decisions along with their context and consequences. They help:
- Document why decisions were made
- Provide context for future developers
- Track the evolution of the system
- Avoid revisiting already-decided questions

## ADR Index

### v2.0.0 Decisions (January 2026)

- **[ADR-0001: Enhanced Schema Structure](0001-enhanced-schema-structure.md)** - Validation and match flags
- **[ADR-0002: Config Refactoring](0002-config-refactoring-separation-of-concerns.md)** - Separation of concerns
- **[ADR-0003: Integrated Validation](0003-integrated-validation-vs-separate-service.md)** - Validation architecture

### Historical Decisions (November 2025)

- **[ADR-0004: Two-Tier Extraction Architecture](0004-two-tier-extraction-architecture.md)** - Content extraction vs LLM processing separation
- **[ADR-0005: FastAPI Framework Choice](0005-fastapi-framework-choice.md)** - Web framework selection
- **[ADR-0006: SQLite Database Choice](0006-sqlite-database-choice.md)** - Database selection for v1
- **[ADR-0007: Multimodal as Default](0007-multimodal-as-default.md)** - Default LLM processing mode
- **[ADR-0008: Hybrid Extraction as Default](0008-hybrid-extraction-as-default.md)** - Default extraction method
- **[ADR-0009: Retry Logic with Exponential Backoff](0009-retry-logic-exponential-backoff.md)** - Error handling strategy
- **[ADR-0010: JSON Schema Validation](0010-json-schema-validation.md)** - Validation approach
- **[ADR-0011: Environment-Based Configuration](0011-environment-based-configuration.md)** - Configuration management

## ADR Format

Each ADR follows this structure:
- **Status**: Accepted, Proposed, Deprecated, Superseded
- **Date**: When the decision was made
- **Deciders**: Who made the decision
- **Tags**: Keywords for categorization
- **Context**: What situation led to this decision
- **Decision**: What was decided
- **Consequences**: Positive, negative, and neutral consequences
- **Alternatives Considered**: Other options that were evaluated
- **Implementation Notes**: How it was implemented

## Adding New ADRs

When making a significant architectural decision:
1. Create a new ADR file: `00XX-decision-title.md`
2. Use the template from existing ADRs
3. Update this README with the new ADR
4. Link to the ADR from relevant documentation

## References

- [ADR Template](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

