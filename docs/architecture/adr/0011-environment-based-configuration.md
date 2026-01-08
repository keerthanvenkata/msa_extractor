# ADR-0011: Environment-Based Configuration

**Status:** Accepted  
**Date:** November 2025 (estimated)  
**Deciders:** Development Team  
**Tags:** configuration, deployment, architecture

## Context

Need a configuration management approach that:
- Works across different environments (dev, staging, production)
- Supports cloud deployment (Cloud Run, Docker)
- Avoids hardcoded values
- Is secure (API keys, secrets)
- Is easy to override

## Decision

Chose **environment variable-based configuration** with:
- `.env` file for local development
- Environment variables for cloud deployment
- Sensible defaults in `config.py`
- Google Secret Manager for production secrets

## Consequences

### Positive
- **Environment-specific**: Different configs for dev/staging/prod
- **Cloud-native**: Works with Cloud Run, Docker, Kubernetes
- **Secure**: Secrets not in code or version control
- **Flexible**: Easy to override for testing
- **Standard practice**: Common pattern in cloud deployments
- **No hardcoded paths**: Cross-platform compatible

### Negative
- **Runtime errors**: Missing env vars only discovered at runtime
- **No type checking**: Env vars are strings, need conversion
- **Documentation needed**: Must document all env vars

### Neutral
- **Default values**: Sensible defaults provided
- **Validation**: Config validation at startup (can be added)

## Alternatives Considered

1. **Config files (YAML/JSON)**:
   - Pros: Structured, versioned
   - Cons: Harder to override per environment, security concerns
   - **Rejected** - Less flexible for cloud deployment

2. **Database-stored config**:
   - Pros: Dynamic, can change without redeploy
   - Cons: Overkill, adds complexity, requires database
   - **Rejected** - Too complex for current needs

3. **Hardcoded with overrides**:
   - Pros: Simple, type-safe
   - Cons: Not flexible, hardcoded values
   - **Rejected** - Not suitable for cloud deployment

## Implementation Notes

- All config in `config.py` with `os.getenv()` calls
- Default values provided for all settings
- `.env.example` file documents all variables
- Google Secret Manager integration for production
- No hardcoded paths or values
- Cross-platform compatible (Windows, Linux, macOS)

