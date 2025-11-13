"""
Job management endpoints for MSA Metadata Extractor API.

Handles job listing and log retrieval.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_db, verify_api_key
from api.models.responses import JobListResponse, JobSummary, JobLogsResponse, LogEntry
from storage.database import ExtractionDB
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/extract", tags=["jobs"])

# Whitelist of allowed columns for sorting (based on extractions table schema)
ALLOWED_SORT_COLUMNS = {
    "id",
    "file_name",
    "file_size",
    "status",
    "created_at",
    "started_at",
    "completed_at",
    "error_message",
    "extraction_method",
    "llm_processing_mode",
    "ocr_engine"
}

# Allowed sort directions
ALLOWED_SORT_DIRECTIONS = {"ASC", "DESC"}


def validate_and_sanitize_sort(sort: str) -> str:
    """
    Validate and sanitize sort parameter to prevent SQL injection.
    
    Args:
        sort: Sort string in format "column [ASC|DESC]" (e.g., "created_at DESC")
    
    Returns:
        Sanitized sort string
    
    Raises:
        HTTPException: If sort parameter is invalid
    """
    # Remove leading/trailing whitespace
    sort = sort.strip()
    
    # Split by whitespace to get column and direction
    parts = sort.split()
    
    if not parts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sort parameter cannot be empty"
        )
    
    # Get column name (first part)
    column = parts[0].lower()
    
    # Validate column name against whitelist
    if column not in ALLOWED_SORT_COLUMNS:
        allowed = ", ".join(sorted(ALLOWED_SORT_COLUMNS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort column: {parts[0]}. Allowed columns: {allowed}"
        )
    
    # Get direction (second part, if present)
    direction = "DESC"  # Default direction
    if len(parts) > 1:
        direction = parts[1].upper()
        if direction not in ALLOWED_SORT_DIRECTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort direction: {parts[1]}. Must be ASC or DESC"
            )
    
    # Return sanitized sort string (use original column name from whitelist for consistency)
    # Map lowercase to actual column name
    column_map = {col.lower(): col for col in ALLOWED_SORT_COLUMNS}
    sanitized_column = column_map[column]
    
    return f"{sanitized_column} {direction}"


@router.get(
    "/jobs",
    response_model=JobListResponse,
    summary="List extraction jobs"
)
async def list_jobs(
    status: Optional[str] = Query(
        None,
        description="Filter by status: pending | processing | completed | failed"
    ),
    limit: int = Query(
        50,
        ge=1,
        le=1000,
        description="Maximum number of jobs to return"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of jobs to skip (pagination)"
    ),
    sort: str = Query(
        "created_at DESC",
        description="Sort order (SQL ORDER BY clause)"
    ),
    db: ExtractionDB = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    List extraction jobs with optional filtering and pagination.
    
    Useful for monitoring and administration.
    
    **Query Parameters:**
    - `status`: Filter by status (optional)
    - `limit`: Maximum number of jobs (default: 50, max: 1000)
    - `offset`: Pagination offset (default: 0)
    - `sort`: Sort order (default: created_at DESC)
    
    **Response:**
    - List of job summaries with pagination info
    """
    # Validate status if provided
    if status and status not in ["pending", "processing", "completed", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status}. Must be one of: pending, processing, completed, failed"
        )
    
    # Validate and sanitize sort parameter to prevent SQL injection
    try:
        sanitized_sort = validate_and_sanitize_sort(sort)
    except HTTPException:
        raise  # Re-raise HTTP exceptions from validation
    
    # Get jobs from database
    jobs = db.list_jobs(status=status, limit=limit, offset=offset, sort=sanitized_sort)
    
    # Get total count (for pagination)
    # Note: This is a simplified count - for production, consider a separate count query
    all_jobs = db.list_jobs(status=status, limit=10000, offset=0, sort=sanitized_sort)
    total = len(all_jobs)
    
    # Convert to response models
    job_summaries = [
        JobSummary(
            job_id=job["id"],
            status=job["status"],
            file_name=job["file_name"],
            created_at=job["created_at"],
            completed_at=job.get("completed_at")
        )
        for job in jobs
    ]
    
    return JobListResponse(
        jobs=job_summaries,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{job_id}/logs",
    response_model=JobLogsResponse,
    summary="Get log entries for a job"
)
async def get_job_logs(
    job_id: str,
    limit: int = Query(
        1000,
        ge=1,
        le=10000,
        description="Maximum number of log entries to return"
    ),
    level: Optional[str] = Query(
        None,
        description="Filter by log level: DEBUG | INFO | WARNING | ERROR | CRITICAL"
    ),
    db: ExtractionDB = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get log entries for a specific job.
    
    Useful for debugging and monitoring extraction progress.
    
    **Path Parameters:**
    - `job_id`: Job UUID
    
    **Query Parameters:**
    - `limit`: Maximum number of entries (default: 1000, max: 10000)
    - `level`: Filter by log level (optional)
    
    **Response:**
    - List of log entries with timestamps and details
    """
    # Validate UUID format
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job ID format: {job_id}"
        )
    
    # Validate job exists
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    # Validate level if provided
    if level and level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid log level: {level}. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
        )
    
    # Get logs from database
    logs = db.get_logs(job_id, limit=limit, level=level)
    
    # Convert to response models
    log_entries = [
        LogEntry(
            timestamp=log["timestamp"],
            level=log["level"],
            message=log["message"],
            module=log.get("module"),
            details=log.get("details")
        )
        for log in logs
    ]
    
    return JobLogsResponse(
        job_id=job_id,
        logs=log_entries,
        total=len(log_entries)
    )

