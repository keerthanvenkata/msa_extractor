"""
Extraction endpoints for MSA Metadata Extractor API.

Handles file upload, job status, and result retrieval.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    status,
    UploadFile
)

from config import (
    MAX_UPLOAD_SIZE_BYTES,
    UPLOADS_DIR,
    EXTRACTION_METHOD,
    LLM_PROCESSING_MODE,
    OCR_ENGINE
)
from api.dependencies import get_db, verify_api_key
from api.models.responses import (
    UploadResponse,
    StatusResponse,
    ResultResponse,
    ErrorResponse
)
from api.services.extraction_service import process_extraction
from storage.database import ExtractionDB
from utils.exceptions import FileError
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/extract", tags=["extraction"])

# Whitelist of allowed values for override parameters
ALLOWED_EXTRACTION_METHODS = {"text_direct", "ocr_all", "ocr_images_only", "vision_all", "hybrid"}
ALLOWED_LLM_PROCESSING_MODES = {"text_llm", "vision_llm", "multimodal", "dual_llm"}
ALLOWED_OCR_ENGINES = {"tesseract", "gcv"}


def validate_file_type(filename: str) -> None:
    """
    Validate that file is PDF or DOCX.
    
    Args:
        filename: Original filename
    
    Raises:
        HTTPException: If file type is invalid
    """
    ext = Path(filename).suffix.lower()
    if ext not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {ext}. Only PDF and DOCX files are supported."
        )


def validate_file_size(size: int) -> None:
    """
    Validate file size is within limits.
    
    Args:
        size: File size in bytes
    
    Raises:
        HTTPException: If file size exceeds maximum
    """
    if size > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size ({size / (1024 * 1024):.2f} MB) exceeds maximum allowed size ({max_mb} MB)"
        )


def validate_extraction_method(method: Optional[str]) -> None:
    """
    Validate extraction method parameter.
    
    Args:
        method: Extraction method to validate
    
    Raises:
        HTTPException: If method is invalid
    """
    if method is not None and method not in ALLOWED_EXTRACTION_METHODS:
        allowed = ", ".join(sorted(ALLOWED_EXTRACTION_METHODS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid extraction_method: {method}. Allowed values: {allowed}"
        )


def validate_llm_processing_mode(mode: Optional[str]) -> None:
    """
    Validate LLM processing mode parameter.
    
    Args:
        mode: LLM processing mode to validate
    
    Raises:
        HTTPException: If mode is invalid
    """
    if mode is not None and mode not in ALLOWED_LLM_PROCESSING_MODES:
        allowed = ", ".join(sorted(ALLOWED_LLM_PROCESSING_MODES))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid llm_processing_mode: {mode}. Allowed values: {allowed}"
        )


def validate_ocr_engine(engine: Optional[str]) -> None:
    """
    Validate OCR engine parameter.
    
    Args:
        engine: OCR engine to validate
    
    Raises:
        HTTPException: If engine is invalid
    """
    if engine is not None and engine not in ALLOWED_OCR_ENGINES:
        allowed = ", ".join(sorted(ALLOWED_OCR_ENGINES))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ocr_engine: {engine}. Allowed values: {allowed}"
        )


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document and start extraction"
)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF or DOCX file to extract metadata from"),
    extraction_method: Optional[str] = Form(
        None,
        description="Override extraction method (text_direct, ocr_all, ocr_images_only, vision_all, hybrid)"
    ),
    llm_processing_mode: Optional[str] = Form(
        None,
        description="Override LLM processing mode (text_llm, vision_llm, multimodal, dual_llm)"
    ),
    ocr_engine: Optional[str] = Form(
        None,
        description="Override OCR engine (tesseract, gcv). Only used if extraction_method requires OCR."
    ),
    db: ExtractionDB = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Upload a PDF or DOCX file and start extraction job.
    
    The file is validated, saved to uploads directory, and a background
    extraction task is started. Returns immediately with job ID.
    
    **Request:**
    - `file`: PDF or DOCX file (required)
    - `extraction_method`: Optional override (defaults to config)
    - `llm_processing_mode`: Optional override (defaults to config)
    - `ocr_engine`: Optional override (defaults to config, only used if extraction_method requires OCR)
    
    **Response:**
    - Job ID and status URLs for polling
    
    **Error Responses:**
    - `400 Bad Request`: Invalid file type or size
    - `401 Unauthorized`: Invalid or missing API key (if auth enabled)
    - `500 Internal Server Error`: Server error during upload
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        validate_file_type(file.filename)
        
        # Validate parameter overrides
        validate_extraction_method(extraction_method)
        validate_llm_processing_mode(llm_processing_mode)
        validate_ocr_engine(ocr_engine)
        
        # Read file content to get size
        content = await file.read()
        file_size = len(content)
        validate_file_size(file_size)
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save file to uploads directory (preserve extension)
        file_extension = Path(file.filename).suffix.lower()
        file_path = UPLOADS_DIR / f"{job_id}{file_extension}"
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Write file content
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File uploaded: {file.filename} -> {file_path} (Job ID: {job_id})")
        
        # Create job in database
        # Use provided extraction method or default from config
        extraction_method_used = extraction_method or EXTRACTION_METHOD
        llm_mode_used = llm_processing_mode or LLM_PROCESSING_MODE
        # Use provided OCR engine or determine from extraction method
        if ocr_engine:
            ocr_engine_used = ocr_engine
        elif extraction_method_used in ["ocr_all", "ocr_images_only"]:
            ocr_engine_used = OCR_ENGINE
        else:
            ocr_engine_used = None
        
        # Pass job_id to ensure file path and database record use the same ID
        db.create_job(
            file_name=file.filename,
            pdf_storage_path=str(file_path),
            file_size=file_size,
            extraction_method=extraction_method_used,
            llm_processing_mode=llm_mode_used,
            ocr_engine=ocr_engine_used,
            job_id=job_id  # Use the generated job_id to match file path
        )
        
        # Start background extraction task
        background_tasks.add_task(
            process_extraction,
            job_id=job_id,
            file_path=file_path,
            extraction_method=extraction_method_used,
            llm_processing_mode=llm_mode_used,
            ocr_engine=ocr_engine_used  # Pass OCR engine override if provided
        )
        
        # Use current timestamp (job was just created)
        created_at = datetime.now().isoformat()
        
        # Return response
        return UploadResponse(
            job_id=job_id,
            status="pending",
            file_name=file.filename,
            file_size=file_size,
            created_at=created_at,
            status_url=f"/api/v1/extract/status/{job_id}",
            result_url=f"/api/v1/extract/result/{job_id}"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.get(
    "/status/{job_id}",
    response_model=StatusResponse,
    summary="Get extraction job status"
)
async def get_job_status(
    job_id: str,
    db: ExtractionDB = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get the status of an extraction job.
    
    This is a lightweight endpoint for polling job status.
    Poll every 2-3 seconds until status is "completed" or "failed".
    
    **Path Parameters:**
    - `job_id`: Job UUID
    
    **Response:**
    - Job status, timestamps, and result URL (if completed)
    
    **Error Responses:**
    - `404 Not Found`: Job ID not found
    - `401 Unauthorized`: Invalid or missing API key (if auth enabled)
    """
    # Validate UUID format (basic check)
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job ID format: {job_id}"
        )
    
    # Get job from database
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    # Build response
    response = StatusResponse(
        job_id=job_id,
        status=job["status"],
        file_name=job["file_name"],
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        error_message=job.get("error_message"),
        result_url=f"/api/v1/extract/result/{job_id}" if job["status"] == "completed" else None
    )
    
    return response


@router.get(
    "/result/{job_id}",
    response_model=ResultResponse,
    summary="Get extraction result"
)
async def get_job_result(
    job_id: str,
    db: ExtractionDB = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get the extraction result for a completed job.
    
    Returns the extracted metadata if job is completed.
    If job is still processing, returns 202 with status URL.
    If job failed, returns error message.
    
    **Path Parameters:**
    - `job_id`: Job UUID
    
    **Response:**
    - Extracted metadata (if completed)
    - Error message (if failed)
    - 202 Accepted (if still processing)
    
    **Error Responses:**
    - `202 Accepted`: Job not completed yet
    - `404 Not Found`: Job ID not found
    - `401 Unauthorized`: Invalid or missing API key (if auth enabled)
    """
    # Validate UUID format
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job ID format: {job_id}"
        )
    
    # Get job from database
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    job_status = job["status"]
    
    # If job is still processing or pending, return 202
    if job_status in ["pending", "processing"]:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "error": "Job not completed yet",
                "status": job_status,
                "status_url": f"/api/v1/extract/status/{job_id}"
            }
        )
    
    # If job failed, return error
    if job_status == "failed":
        return ResultResponse(
            job_id=job_id,
            status="failed",
            file_name=job["file_name"],
            created_at=job["created_at"],
            completed_at=job.get("completed_at"),
            metadata=None,
            error_message=job.get("error_message")
        )
    
    # Job is completed, return metadata
    if job_status == "completed":
        result_json = job.get("result_json")
        if not result_json:
            logger.warning(f"Job {job_id} marked as completed but no result_json found")
            result_json = {}
        
        return ResultResponse(
            job_id=job_id,
            status="completed",
            file_name=job["file_name"],
            created_at=job["created_at"],
            completed_at=job.get("completed_at"),
            metadata=result_json,
            error_message=None
        )
    
    # Unknown status
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unknown job status: {job_status}"
    )

