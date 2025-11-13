"""
Pydantic request models for API endpoints.

Note: File uploads use FastAPI's UploadFile directly,
so we don't need request models for those endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field


class JobListQuery(BaseModel):
    """Query parameters for job listing endpoint."""
    
    status: Optional[str] = Field(
        None,
        description="Filter by status: pending | processing | completed | failed"
    )
    limit: int = Field(
        50,
        ge=1,
        le=1000,
        description="Maximum number of jobs to return"
    )
    offset: int = Field(
        0,
        ge=0,
        description="Number of jobs to skip (pagination)"
    )
    sort: str = Field(
        "created_at DESC",
        description="Sort order (SQL ORDER BY clause)"
    )


class JobLogsQuery(BaseModel):
    """Query parameters for job logs endpoint."""
    
    limit: int = Field(
        1000,
        ge=1,
        le=10000,
        description="Maximum number of log entries to return"
    )
    level: Optional[str] = Field(
        None,
        description="Filter by log level: DEBUG | INFO | WARNING | ERROR | CRITICAL"
    )

