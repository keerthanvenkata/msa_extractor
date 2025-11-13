"""
Extraction service for background task processing.

Handles the actual extraction work in background tasks.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import (
    UPLOADS_DIR,
    EXTRACTION_METHOD,
    LLM_PROCESSING_MODE,
    OCR_ENGINE,
    validate_config
)
from extractors.extraction_coordinator import ExtractionCoordinator
from storage.database import ExtractionDB
from utils.exceptions import FileError, ExtractionError
from utils.logger import get_logger

logger = get_logger(__name__)


def _cleanup_file_on_failure(file_path: Path, job_id: str) -> None:
    """
    Cleanup uploaded file when job fails.
    
    Args:
        file_path: Path to file to delete
        job_id: Job ID for logging
    """
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up file for failed job {job_id}: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file for job {job_id}: {e}")


def process_extraction(
    job_id: str,
    file_path: Path,
    extraction_method: Optional[str] = None,
    llm_processing_mode: Optional[str] = None,
    ocr_engine: Optional[str] = None,
    db: Optional[ExtractionDB] = None
) -> None:
    """
    Process extraction job in background task.
    
    This function:
    1. Updates job status to "processing"
    2. Runs extraction using ExtractionCoordinator
    3. Stores result JSON in database
    4. Updates job status to "completed" or "failed"
    
    Args:
        job_id: Job UUID
        file_path: Path to uploaded file
        extraction_method: Override default extraction method
        llm_processing_mode: Override default LLM processing mode
        ocr_engine: Override default OCR engine
        db: Database instance (will create if not provided)
    
    Note:
        - Always uses database storage (no legacy mode)
        - Logs errors to database
        - Handles all exceptions and updates job status
    """
    db_created = False
    if db is None:
        db = ExtractionDB()
        db_created = True
    
    try:
        # Validate configuration
        validate_config()
        
        # Update status to processing
        db.update_job_status(
            job_id,
            "processing",
            started_at=datetime.now()
        )
        db.add_log_entry(job_id, "INFO", "Starting extraction", module=__name__)
        
        # Initialize coordinator
        coordinator = ExtractionCoordinator()
        
        # Extract metadata with overrides (if provided)
        logger.info(f"Processing extraction for job {job_id}: {file_path}")
        if extraction_method or llm_processing_mode or ocr_engine:
            logger.info(
                f"Using overrides: extraction_method={extraction_method}, "
                f"llm_processing_mode={llm_processing_mode}, ocr_engine={ocr_engine}"
            )
        
        metadata = coordinator.extract_metadata(
            str(file_path),
            strategy=None,  # Deprecated parameter
            extraction_method=extraction_method,
            llm_processing_mode=llm_processing_mode,
            ocr_engine=ocr_engine
        )
        
        # Validate schema
        validator = coordinator.gemini_client.schema_validator
        is_valid, error = validator.validate(metadata)
        
        if not is_valid:
            logger.warning(f"Schema validation failed for job {job_id}: {error}")
            db.add_log_entry(
                job_id,
                "WARNING",
                f"Schema validation failed: {error}",
                module=__name__
            )
            # Normalize to ensure correct structure
            metadata = validator.normalize(metadata)
        
        # Store results in database (always, no legacy mode for API)
        db.complete_job(
            job_id=job_id,
            result_json_dict=metadata,
            pdf_storage_path=str(file_path),
            pdf_storage_type="local",
            result_json_path=None,  # Always None for API (database storage)
            log_path=None  # Always None for API (database storage)
        )
        
        db.add_log_entry(
            job_id,
            "INFO",
            "Extraction completed successfully",
            module=__name__
        )
        logger.info(f"Extraction completed for job {job_id}")
        
    except (FileError, ExtractionError) as e:
        # Update job status to failed
        error_msg = str(e)
        db.update_job_status(
            job_id,
            "failed",
            error_message=error_msg
        )
        db.add_log_entry(
            job_id,
            "ERROR",
            f"Extraction failed: {error_msg}",
            module=__name__
        )
        logger.error(f"Extraction failed for job {job_id}: {e}", exc_info=True)
        
        # Cleanup uploaded file on failure
        _cleanup_file_on_failure(file_path, job_id)
        
    except Exception as e:
        # Update job status to failed for unexpected errors
        error_msg = f"Unexpected error: {str(e)}"
        db.update_job_status(
            job_id,
            "failed",
            error_message=error_msg
        )
        db.add_log_entry(
            job_id,
            "ERROR",
            error_msg,
            module=__name__
        )
        logger.error(f"Unexpected error processing job {job_id}: {e}", exc_info=True)
        
        # Cleanup uploaded file on failure
        _cleanup_file_on_failure(file_path, job_id)
        
    finally:
        # Close database connection if we created it
        if db_created and db is not None:
            db.close()

