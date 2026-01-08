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
                        "Organization Name": {
                            "extracted_value": "Adaequare Inc",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        }
                    },
                    "Contract Lifecycle": {
                        "Party A": {
                            "extracted_value": "Adaequare Inc.",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Party B": {
                            "extracted_value": "Orbit Inc.",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Execution Date": {
                            "extracted_value": "2025-03-14",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Effective Date": {
                            "extracted_value": "2025-04-01",
                            "match_flag": "similar_not_exact",
                            "validation": {
                                "score": 90,
                                "status": "valid",
                                "notes": "Date format correct, differs from template by 18 days"
                            }
                        },
                        "Expiration / Termination Date": {
                            "extracted_value": "2028-03-31",
                            "match_flag": "different_from_template",
                            "validation": {
                                "score": 85,
                                "status": "warning",
                                "notes": "Valid date but different term length than template"
                            }
                        },
                        "Authorized Signatory - Party A": {
                            "extracted_value": "John Doe, VP of Operations",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Authorized Signatory - Party B": {
                            "extracted_value": "Jane Smith, CEO",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        }
                    },
                    "Business Terms": {
                        "Document Type": {
                            "extracted_value": "MSA",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Termination Notice Period": {
                            "extracted_value": "30 days",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        }
                    },
                    "Commercial Operations": {
                        "Billing Frequency": {
                            "extracted_value": "Monthly",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Payment Terms": {
                            "extracted_value": "Net 30 days from invoice date",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Expense Reimbursement Rules": {
                            "extracted_value": "Reimbursed as per client travel policy, pre-approval required",
                            "match_flag": "similar_not_exact",
                            "validation": {
                                "score": 95,
                                "status": "valid",
                                "notes": "Minor wording differences from template"
                            }
                        }
                    },
                    "Finance Terms": {
                        "Pricing Model Type": {
                            "extracted_value": "T&M",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Currency": {
                            "extracted_value": "USD",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Contract Value": {
                            "extracted_value": "50000.00",
                            "match_flag": "different_from_template",
                            "validation": {
                                "score": 80,
                                "status": "warning",
                                "notes": "Value differs from template example"
                            }
                        }
                    },
                    "Risk & Compliance": {
                        "Indemnification Clause Reference": {
                            "extracted_value": "Section 12 – Indemnification: Each party agrees to indemnify...",
                            "match_flag": "similar_not_exact",
                            "validation": {
                                "score": 90,
                                "status": "valid",
                                "notes": "Clause found, minor wording variations"
                            }
                        },
                        "Limitation of Liability Cap": {
                            "extracted_value": "Aggregate liability not to exceed fees paid in previous 12 months",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Insurance Requirements": {
                            "extracted_value": "CGL $2M per occurrence; Workers Comp as per law",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Warranties / Disclaimers": {
                            "extracted_value": "Services to be performed in a professional manner; no other warranties implied",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        }
                    },
                    "Legal Terms": {
                        "Governing Law": {
                            "extracted_value": "Texas, USA",
                            "match_flag": "different_from_template",
                            "validation": {
                                "score": 75,
                                "status": "warning",
                                "notes": "Jurisdiction differs from template"
                            }
                        },
                        "Confidentiality Clause Reference": {
                            "extracted_value": "Section 8 – Confidential Information: Each party agrees to maintain confidentiality...",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        },
                        "Force Majeure Clause Reference": {
                            "extracted_value": "Section 15 – Force Majeure: Neither party shall be liable...",
                            "match_flag": "same_as_template",
                            "validation": {
                                "score": 100,
                                "status": "valid",
                                "notes": ""
                            }
                        }
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
                "version": "1.1.0",
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

