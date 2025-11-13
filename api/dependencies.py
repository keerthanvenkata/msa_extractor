"""
Shared dependencies for FastAPI endpoints.

Provides database connection, authentication, and other shared resources.
"""

from functools import lru_cache
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, APIKeyQuery

from config import API_ENABLE_AUTH, API_KEYS, DB_PATH
from storage.database import ExtractionDB
from utils.logger import get_logger

logger = get_logger(__name__)

# API Key authentication schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


def get_db() -> Generator[ExtractionDB, None, None]:
    """
    Dependency to get database connection.
    
    Uses context manager to ensure proper cleanup.
    """
    db = ExtractionDB(db_path=DB_PATH)
    try:
        yield db
    finally:
        db.close()


@lru_cache()
def get_db_singleton() -> ExtractionDB:
    """
    Get a singleton database instance.
    
    Note: This is for cases where we need a persistent connection
    (e.g., background tasks). Use get_db() for request handlers.
    """
    return ExtractionDB(db_path=DB_PATH)


def verify_api_key(
    api_key_header: str = Depends(api_key_header),
    api_key_query: str = Depends(api_key_query),
) -> str:
    """
    Verify API key from header or query parameter.
    
    Args:
        api_key_header: API key from X-API-Key header
        api_key_query: API key from api_key query parameter
    
    Returns:
        The verified API key
    
    Raises:
        HTTPException: If authentication is enabled and key is invalid/missing
    """
    # If auth is disabled, allow all requests
    if not API_ENABLE_AUTH:
        return "anonymous"
    
    # Get API key from header or query parameter
    api_key = api_key_header or api_key_query
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header or api_key query parameter."
        )
    
    # Check if key is in allowed keys
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


# Optional dependency for endpoints that may or may not require auth
def get_api_key_optional(
    api_key_header: str = Depends(api_key_header),
    api_key_query: str = Depends(api_key_query),
) -> Optional[str]:
    """
    Get API key if provided, but don't require it.
    
    Returns None if auth is disabled or no key provided.
    """
    if not API_ENABLE_AUTH:
        return None
    
    api_key = api_key_header or api_key_query
    if api_key and api_key in API_KEYS:
        return api_key
    
    return None

