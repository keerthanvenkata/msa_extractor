"""
Main CLI entry point for MSA Metadata Extractor.

Provides command-line interface for single-file and batch processing.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config import (
    validate_config, OUTPUT_DIR, UPLOADS_DIR, RESULTS_DIR, LOGS_DIR,
    EXTRACTION_METHOD, LLM_PROCESSING_MODE, OCR_ENGINE
)
from extractors.extraction_coordinator import ExtractionCoordinator
from ai.schema import SchemaValidator
from storage.database import ExtractionDB
from utils.logger import get_logger
from utils.exceptions import ConfigurationError, FileError, ExtractionError

# Set up centralized logging
logger = get_logger(__name__)


def extract_single_file(
    file_path: str,
    output_path: str = None,
    strategy: str = None,
    legacy: bool = False,
    job_id: Optional[str] = None,
    db: Optional[ExtractionDB] = None
) -> dict:
    """
    Extract metadata from a single file with database tracking.
    
    Args:
        file_path: Path to input file (PDF or DOCX)
        output_path: Path to output JSON file (legacy mode only, optional)
        strategy: Extraction strategy (optional, deprecated - use config)
        legacy: If True, use file-based storage (results/, logs/). If False, use database.
        job_id: Optional existing job ID (for re-running failed jobs)
        db: Optional ExtractionDB instance (will create if not provided)
    
    Returns:
        Dictionary with extracted metadata and job_id
    """
    # Initialize database if not provided
    if db is None:
        db = ExtractionDB()
    
    input_file = Path(file_path)
    if not input_file.exists():
        raise FileError(f"File not found: {file_path}")
    
    file_name = input_file.name
    file_size = input_file.stat().st_size
    
    try:
        # Validate configuration
        validate_config()
        
        # Create or get job
        if job_id:
            # Re-running existing job
            job = db.get_job(job_id)
            if not job:
                raise ValueError(f"Job not found: {job_id}")
            pdf_storage_path = job.get("pdf_storage_path")
            if not pdf_storage_path or not Path(pdf_storage_path).exists():
                raise FileError(f"File not found for job {job_id}: {pdf_storage_path}")
        else:
            # Create new job
            # Copy file to uploads directory with UUID (preserve original extension)
            job_id = db.create_job(
                file_name=file_name,
                pdf_storage_path="",  # Will be set after copy
                file_size=file_size,
                extraction_method=EXTRACTION_METHOD,
                llm_processing_mode=LLM_PROCESSING_MODE,
                ocr_engine=OCR_ENGINE if EXTRACTION_METHOD in ["ocr_all", "ocr_images_only"] else None
            )
            
            # Copy file to uploads directory with UUID and preserve original extension
            file_extension = input_file.suffix.lower()  # .pdf or .docx
            pdf_storage_path = UPLOADS_DIR / f"{job_id}{file_extension}"
            shutil.copy2(input_file, pdf_storage_path)
            
            # Update job with storage path
            db.update_job_status(job_id, "pending")
            cursor = db.conn.cursor()
            cursor.execute(
                "UPDATE extractions SET pdf_storage_path = ? WHERE id = ?",
                (str(pdf_storage_path), job_id)
            )
            db.conn.commit()
        
        # Update status to processing
        db.update_job_status(job_id, "processing", started_at=datetime.now())
        
        # Initialize coordinator
        coordinator = ExtractionCoordinator()
        
        # Extract metadata (use copied PDF path for consistency)
        extraction_file_path = str(pdf_storage_path) if job_id else file_path
        logger.info(f"Extracting metadata from: {extraction_file_path} (Job ID: {job_id})")
        metadata = coordinator.extract_metadata(extraction_file_path, strategy)
        
        # Validate schema
        validator = coordinator.gemini_client.schema_validator
        is_valid, error = validator.validate(metadata)
        
        if not is_valid:
            logger.warning(f"Schema validation failed: {error}")
            # Normalize to ensure correct structure
            metadata = validator.normalize(metadata)
        
        # Store results based on mode
        result_json_path = None
        log_path = None
        
        if legacy:
            # Legacy mode: Save to files
            if output_path:
                result_json_path = Path(output_path)
            else:
                result_json_path = RESULTS_DIR / f"{job_id}.json"
            
            result_json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(result_json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Metadata saved to: {result_json_path}")
            
            # Note: Logs are still written to database in legacy mode
            # If you want file-based logs, we'd need a custom log handler
        
        # Complete job
        db.complete_job(
            job_id=job_id,
            result_json_dict=metadata if not legacy else None,  # Store in DB only if not legacy
            pdf_storage_path=str(pdf_storage_path),
            pdf_storage_type="local",
            result_json_path=str(result_json_path) if legacy else None,
            log_path=log_path
        )
        
        # Add job_id to return value
        result = metadata.copy()
        result["_job_id"] = job_id
        
        return result
        
    except (FileError, ExtractionError) as e:
        # Update job status to failed
        if job_id:
            db.update_job_status(
                job_id,
                "failed",
                error_message=str(e)
            )
            db.add_log_entry(job_id, "ERROR", str(e), module=__name__)
        logger.error(f"Extraction failed: {e}", exc_info=True)
        raise
    except Exception as e:
        # Update job status to failed
        if job_id:
            db.update_job_status(
                job_id,
                "failed",
                error_message=str(e)
            )
            db.add_log_entry(job_id, "ERROR", f"Unexpected error: {e}", module=__name__)
        logger.error(f"Unexpected error extracting metadata: {e}", exc_info=True)
        raise ExtractionError(f"Unexpected error: {e}") from e


def extract_batch(
    input_dir: str,
    output_dir: str = None,
    strategy: str = None,
    parallel: int = 1,
    legacy: bool = False
) -> List[dict]:
    """
    Extract metadata from multiple files with database tracking.
    
    Args:
        input_dir: Directory containing input files
        output_dir: Directory for output JSON files (legacy mode only)
        strategy: Extraction strategy (optional, deprecated)
        parallel: Number of parallel processes (not yet implemented)
        legacy: If True, use file-based storage. If False, use database.
    
    Returns:
        List of dictionaries with job_id and status
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    
    # Find all PDF and DOCX files
    files = list(input_path.glob("*.pdf")) + list(input_path.glob("*.docx"))
    
    if not files:
        logger.warning(f"No PDF or DOCX files found in: {input_dir}")
        return []
    
    logger.info(f"Found {len(files)} files to process")
    
    # Set output directory (legacy mode only)
    if legacy and output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    elif legacy:
        output_path = RESULTS_DIR
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = None
    
    # Initialize database
    db = ExtractionDB()
    
    # Process files
    results = []
    job_ids = []
    
    for i, file_path in enumerate(files, 1):
        logger.info(f"Processing file {i}/{len(files)}: {file_path.name}")
        
        try:
            # Generate output filename (legacy mode only)
            output_file = None
            if legacy and output_path:
                output_file = output_path / f"{file_path.stem}.json"
            
            # Extract metadata
            metadata = extract_single_file(
                str(file_path),
                str(output_file) if output_file else None,
                strategy,
                legacy=legacy,
                db=db
            )
            
            job_id = metadata.pop("_job_id", None)
            job_ids.append(job_id)
            
            results.append({
                "file": str(file_path),
                "job_id": job_id,
                "status": "success",
                "metadata": metadata if legacy else None  # Only include in legacy mode
            })
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            results.append({
                "file": str(file_path),
                "job_id": None,
                "status": "error",
                "error": str(e)
            })
    
    # Save batch summary (legacy mode only)
    if legacy and output_path:
        summary_file = output_path / "batch_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Batch summary saved to: {summary_file}")
    
    logger.info(f"Batch processing complete. Processed {len(results)} files. Job IDs: {job_ids}")
    
    return results


def list_jobs(status: Optional[str] = None, limit: int = 50) -> List[dict]:
    """List extraction jobs."""
    db = ExtractionDB()
    try:
        jobs = db.list_jobs(status=status, limit=limit)
        return jobs
    finally:
        db.close()


def get_job(job_id: str) -> Optional[dict]:
    """Get a job by ID."""
    db = ExtractionDB()
    try:
        return db.get_job(job_id)
    finally:
        db.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MSA Metadata Extractor - Extract structured metadata from contracts"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract metadata from file(s)")
    extract_parser.add_argument(
        "--file",
        type=str,
        help="Path to input file (PDF or DOCX)"
    )
    extract_parser.add_argument(
        "--dir",
        type=str,
        help="Directory containing input files for batch processing"
    )
    extract_parser.add_argument(
        "--out",
        type=str,
        help="Output file path (legacy mode only, for single file processing)"
    )
    extract_parser.add_argument(
        "--out-dir",
        type=str,
        help="Output directory (legacy mode only, for batch processing)"
    )
    extract_parser.add_argument(
        "--strategy",
        type=str,
        choices=["auto", "text_extraction", "gemini_vision", "tesseract", "gcv"],
        help="Extraction strategy (deprecated - use config EXTRACTION_METHOD)"
    )
    extract_parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of parallel processes for batch processing (not yet implemented)"
    )
    extract_parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use file-based storage (results/, logs/) instead of database"
    )
    extract_parser.add_argument(
        "--job-id",
        type=str,
        help="Re-run an existing job by job ID"
    )
    
    # List jobs command
    list_parser = subparsers.add_parser("list-jobs", help="List extraction jobs")
    list_parser.add_argument(
        "--status",
        type=str,
        choices=["pending", "processing", "completed", "failed"],
        help="Filter by status"
    )
    list_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of jobs to return"
    )
    
    # Get job command
    get_parser = subparsers.add_parser("get-job", help="Get job details by ID")
    get_parser.add_argument("job_id", type=str, help="Job UUID")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    
    args = parser.parse_args()
    
    # Validate configuration
    try:
        validate_config()
        if args.command == "validate" or (hasattr(args, "validate_only") and args.validate_only):
            logger.info("Configuration validation successful")
            return 0
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    # Process based on command
    try:
        if args.command == "extract":
            if args.file:
                # Single file processing
                metadata = extract_single_file(
                    args.file,
                    args.out,
                    args.strategy,
                    legacy=args.legacy,
                    job_id=args.job_id
                )
                
                # Print job ID and metadata
                job_id = metadata.pop("_job_id", None)
                if job_id:
                    print(f"Job ID: {job_id}")
                
                # Print to stdout if no output file specified (or in database mode)
                if not args.out or not args.legacy:
                    print(json.dumps(metadata, indent=2, ensure_ascii=False))
                
                return 0
                
            elif args.dir:
                # Batch processing
                results = extract_batch(
                    args.dir,
                    args.out_dir,
                    args.strategy,
                    args.parallel,
                    legacy=args.legacy
                )
                
                logger.info(f"Processed {len(results)} files")
                success_count = sum(1 for r in results if r.get("status") == "success")
                logger.info(f"Successfully processed: {success_count}/{len(results)}")
                
                # Print job IDs
                job_ids = [r.get("job_id") for r in results if r.get("job_id")]
                if job_ids:
                    print(f"Job IDs: {', '.join(job_ids)}")
                
                return 0 if success_count == len(results) else 1
            else:
                extract_parser.print_help()
                return 1
        
        elif args.command == "list-jobs":
            jobs = list_jobs(status=args.status, limit=args.limit)
            print(json.dumps(jobs, indent=2, ensure_ascii=False, default=str))
            return 0
        
        elif args.command == "get-job":
            job = get_job(args.job_id)
            if job:
                print(json.dumps(job, indent=2, ensure_ascii=False, default=str))
                return 0
            else:
                logger.error(f"Job not found: {args.job_id}")
                return 1
        
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

