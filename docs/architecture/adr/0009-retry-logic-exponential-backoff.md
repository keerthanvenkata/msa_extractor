# ADR-0009: Retry Logic with Exponential Backoff

**Status:** Accepted  
**Date:** November 2025 (estimated)  
**Deciders:** Development Team  
**Tags:** reliability, error-handling, api

## Context

LLM API calls can fail due to:
- Rate limiting (429 errors)
- Temporary service unavailability (503, 502, 500)
- Network timeouts
- Transient errors

Need a retry strategy that:
- Handles transient failures gracefully
- Avoids overwhelming the API with retries
- Provides reasonable delays between retries

## Decision

Implemented **retry logic with exponential backoff** for all LLM API calls:
- Maximum retries: 3 attempts (configurable via `API_MAX_RETRIES`)
- Initial delay: 1 second (configurable via `API_RETRY_INITIAL_DELAY`)
- Maximum delay: 60 seconds (configurable via `API_RETRY_MAX_DELAY`)
- Exponential backoff: Delay doubles with each retry (1s, 2s, 4s, ...)
- Retryable exceptions: Rate limits, timeouts, 5xx errors

## Consequences

### Positive
- **Resilience**: Handles transient failures automatically
- **Rate limit friendly**: Exponential backoff reduces API load
- **Configurable**: All parameters can be adjusted
- **Selective retries**: Only retries on appropriate exceptions
- **Better UX**: Users don't see failures for transient issues

### Negative
- **Slower on failures**: Adds delay when retries occur
- **More complex**: Requires retry logic implementation

### Neutral
- **Cost impact**: Retries may increase API costs slightly
- **Timeout handling**: Long retries may exceed user expectations

## Alternatives Considered

1. **No retries**:
   - Pros: Simple, fast failures
   - Cons: Poor user experience, many false failures
   - **Rejected** - Too many transient failures

2. **Fixed delay retries**:
   - Pros: Predictable
   - Cons: May retry too quickly, doesn't back off
   - **Rejected** - Exponential backoff is better practice

3. **Linear backoff**:
   - Pros: Simpler than exponential
   - Cons: Slower to back off, may still overwhelm API
   - **Rejected** - Exponential is standard practice

## Implementation Notes

- Implemented in `ai/gemini_client.py` `_call_with_retry()` method
- Retries on: Rate limits (429), server errors (5xx), timeouts, retryable exceptions
- Does not retry on: Client errors (4xx except 429), validation errors
- Configurable via environment variables
- Logs retry attempts for debugging

