"""
Pydantic response models for API endpoints.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response model for file upload endpoint."""
    
    job_id: str = Field(..., description="Unique job identifier (UUID)")
    status: str = Field(..., description="Job status: pending")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    created_at: str = Field(..., description="ISO 8601 timestamp when job was created")
    status_url: str = Field(..., description="URL to check job status")
    result_url: str = Field(..., description="URL to get extraction result")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc-123-def-456",
                "status": "pending",
                "file_name": "contract.pdf",
                "file_size": 1024000,
                "created_at": "2025-11-12T10:30:00Z",
                "status_url": "/api/v1/extract/status/abc-123-def-456",
                "result_url": "/api/v1/extract/result/abc-123-def-456"
            }
        }


class StatusResponse(BaseModel):
    """Response model for job status endpoint."""
    
    job_id: str = Field(..., description="Unique job identifier (UUID)")
    status: str = Field(..., description="Job status: pending | processing | completed | failed")
    file_name: str = Field(..., description="Original filename")
    created_at: str = Field(..., description="ISO 8601 timestamp when job was created")
    started_at: Optional[str] = Field(None, description="ISO 8601 timestamp when processing started")
    completed_at: Optional[str] = Field(None, description="ISO 8601 timestamp when processing completed")
    error_message: Optional[str] = Field(None, description="Error message if status is failed")
    result_url: Optional[str] = Field(None, description="URL to get extraction result (only if completed)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc-123-def-456",
                "status": "processing",
                "file_name": "contract.pdf",
                "created_at": "2025-11-12T10:30:00Z",
                "started_at": "2025-11-12T10:30:05Z",
                "completed_at": None,
                "error_message": None,
                "result_url": None
            }
        }


class ResultResponse(BaseModel):
    """Response model for extraction result endpoint."""
    
    job_id: str = Field(..., description="Unique job identifier (UUID)")
    status: str = Field(..., description="Job status: completed | failed")
    file_name: str = Field(..., description="Original filename")
    created_at: str = Field(..., description="ISO 8601 timestamp when job was created")
    completed_at: Optional[str] = Field(None, description="ISO 8601 timestamp when processing completed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Extracted metadata (only if completed)")
    error_message: Optional[str] = Field(None, description="Error message if status is failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc-123-def-456",
                "status": "completed",
                "file_name": "contract.pdf",
                "created_at": "2025-11-12T10:30:00Z",
                "completed_at": "2025-11-12T10:32:15Z",
                "metadata": {
                    "Org Details": {
                        "Organization Name": "Adaequare Inc"
                    },
                    "Contract Lifecycle": {
                        "Party A": "Adaequare Inc.",
                        "Party B": "Orbit Inc.",
                        "Execution Date": "2025-03-14",
                        "Effective Date": "2025-04-01",
                        "Expiration / Termination Date": "2028-03-31",
                        "Authorized Signatory - Party A": "John Doe, VP of Operations",
                        "Authorized Signatory - Party B": "Jane Smith, CEO"
                    },
                    "Business Terms": {
                        "Document Type": "MSA",
                        "Termination Notice Period": "30 days"
                    },
                    "Commercial Operations": {
                        "Billing Frequency": "Monthly",
                        "Payment Terms": "Net 30 days from invoice date",
                        "Expense Reimbursement Rules": "Reimbursed as per client travel policy, pre-approval required"
                    },
                    "Finance Terms": {
                        "Pricing Model Type": "T&M",
                        "Currency": "USD",
                        "Contract Value": "50000.00"
                    },
                    "Risk & Compliance": {
                        "Indemnification Clause Reference": "Section 12 – Indemnification: Each party agrees to indemnify...",
                        "Limitation of Liability Cap": "Aggregate liability not to exceed fees paid in previous 12 months",
                        "Insurance Requirements": "CGL $2M per occurrence; Workers Comp as per law",
                        "Warranties / Disclaimers": "Services to be performed in a professional manner; no other warranties implied"
                    },
                    "Legal Terms": {
                        "Governing Law": "Texas, USA",
                        "Confidentiality Clause Reference": "Section 8 – Confidential Information: Each party agrees to maintain confidentiality...",
                        "Force Majeure Clause Reference": "Section 15 – Force Majeure: Neither party shall be liable..."
                    }
                },
                "error_message": None
            }
        }


class JobSummary(BaseModel):
    """Summary of a job for listing endpoints."""
    
    job_id: str = Field(..., description="Unique job identifier (UUID)")
    status: str = Field(..., description="Job status")
    file_name: str = Field(..., description="Original filename")
    created_at: str = Field(..., description="ISO 8601 timestamp when job was created")
    completed_at: Optional[str] = Field(None, description="ISO 8601 timestamp when processing completed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc-123-def-456",
                "status": "completed",
                "file_name": "contract.pdf",
                "created_at": "2025-11-12T10:30:00Z",
                "completed_at": "2025-11-12T10:32:15Z"
            }
        }


class JobListResponse(BaseModel):
    """Response model for job listing endpoint."""
    
    jobs: List[JobSummary] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs (before pagination)")
    limit: int = Field(..., description="Maximum number of jobs returned")
    offset: int = Field(..., description="Number of jobs skipped")
    
    class Config:
        json_schema_extra = {
            "example": {
                "jobs": [
                    {
                        "job_id": "abc-123-def-456",
                        "status": "completed",
                        "file_name": "contract.pdf",
                        "created_at": "2025-11-12T10:30:00Z",
                        "completed_at": "2025-11-12T10:32:15Z"
                    }
                ],
                "total": 10,
                "limit": 50,
                "offset": 0
            }
        }


class LogEntry(BaseModel):
    """Single log entry."""
    
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    level: str = Field(..., description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    message: str = Field(..., description="Log message")
    module: Optional[str] = Field(None, description="Module name")
    details: Optional[str] = Field(None, description="Additional details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-12T10:30:05Z",
                "level": "INFO",
                "message": "Starting extraction",
                "module": "extractors.pdf_extractor",
                "details": None
            }
        }


class JobLogsResponse(BaseModel):
    """Response model for job logs endpoint."""
    
    job_id: str = Field(..., description="Unique job identifier (UUID)")
    logs: List[LogEntry] = Field(..., description="List of log entries")
    total: int = Field(..., description="Total number of log entries")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc-123-def-456",
                "logs": [
                    {
                        "timestamp": "2025-11-12T10:30:05Z",
                        "level": "INFO",
                        "message": "Starting extraction",
                        "module": "extractors.pdf_extractor",
                        "details": None
                    }
                ],
                "total": 15
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str = Field(..., description="Service status: healthy | unhealthy")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status: connected | disconnected")
    storage_type: str = Field(..., description="Storage type: local | gcs")
    timestamp: str = Field(..., description="ISO 8601 timestamp of health check")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "database": "connected",
                "storage_type": "local",
                "timestamp": "2025-11-12T10:30:00Z",
                "error": None
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    status_url: Optional[str] = Field(None, description="URL to check job status (if applicable)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Job not completed yet",
                "message": "Job is still processing. Please check status endpoint.",
                "status_url": "/api/v1/extract/status/abc-123-def-456"
            }
        }

