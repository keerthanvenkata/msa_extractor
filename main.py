"""
Main CLI entry point for MSA Metadata Extractor.

Provides command-line interface for single-file and batch processing.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

from config import validate_config, OUTPUT_DIR
from extractors.extraction_coordinator import ExtractionCoordinator
from ai.schema import SchemaValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_single_file(file_path: str, output_path: str = None, 
                       strategy: str = None) -> dict:
    """
    Extract metadata from a single file.
    
    Args:
        file_path: Path to input file (PDF or DOCX)
        output_path: Path to output JSON file (optional)
        strategy: Extraction strategy (optional)
    
    Returns:
        Dictionary with extracted metadata
    """
    try:
        # Validate configuration
        validate_config()
        
        # Initialize coordinator
        coordinator = ExtractionCoordinator()
        
        # Extract metadata
        logger.info(f"Extracting metadata from: {file_path}")
        metadata = coordinator.extract_metadata(file_path, strategy)
        
        # Validate schema
        validator = SchemaValidator()
        is_valid, error = validator.validate(metadata)
        
        if not is_valid:
            logger.warning(f"Schema validation failed: {error}")
            # Normalize to ensure correct structure
            metadata = validator.normalize(metadata)
        
        # Save to file if output path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Metadata saved to: {output_path}")
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}", exc_info=True)
        raise


def extract_batch(input_dir: str, output_dir: str = None, 
                 strategy: str = None, parallel: int = 1) -> List[dict]:
    """
    Extract metadata from multiple files.
    
    Args:
        input_dir: Directory containing input files
        output_dir: Directory for output JSON files (defaults to input_dir/results)
        strategy: Extraction strategy (optional)
        parallel: Number of parallel processes (not yet implemented)
    
    Returns:
        List of metadata dictionaries
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
    
    # Set output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = input_path / "results"
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Process files
    results = []
    for i, file_path in enumerate(files, 1):
        logger.info(f"Processing file {i}/{len(files)}: {file_path.name}")
        
        try:
            # Generate output filename
            output_file = output_path / f"{file_path.stem}.json"
            
            # Extract metadata
            metadata = extract_single_file(
                str(file_path),
                str(output_file),
                strategy
            )
            
            results.append({
                "file": str(file_path),
                "status": "success",
                "metadata": metadata
            })
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            results.append({
                "file": str(file_path),
                "status": "error",
                "error": str(e)
            })
    
    # Save batch summary
    summary_file = output_path / "batch_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Batch processing complete. Summary saved to: {summary_file}")
    
    return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MSA Metadata Extractor - Extract structured metadata from contracts"
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="Path to input file (PDF or DOCX)"
    )
    
    parser.add_argument(
        "--dir",
        type=str,
        help="Directory containing input files for batch processing"
    )
    
    parser.add_argument(
        "--out",
        type=str,
        help="Output file path (for single file processing)"
    )
    
    parser.add_argument(
        "--out-dir",
        type=str,
        help="Output directory (for batch processing)"
    )
    
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["auto", "text_extraction", "gemini_vision", "tesseract", "gcv"],
        help="Extraction strategy (defaults to config value)"
    )
    
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of parallel processes for batch processing (not yet implemented)"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration, don't extract"
    )
    
    args = parser.parse_args()
    
    # Validate configuration
    try:
        validate_config()
        if args.validate_only:
            logger.info("Configuration validation successful")
            return 0
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    # Process based on arguments
    try:
        if args.file:
            # Single file processing
            metadata = extract_single_file(args.file, args.out, args.strategy)
            
            # Print to stdout if no output file specified
            if not args.out:
                print(json.dumps(metadata, indent=2, ensure_ascii=False))
            
            return 0
            
        elif args.dir:
            # Batch processing
            results = extract_batch(args.dir, args.out_dir, args.strategy, args.parallel)
            
            logger.info(f"Processed {len(results)} files")
            success_count = sum(1 for r in results if r.get("status") == "success")
            logger.info(f"Successfully processed: {success_count}/{len(results)}")
            
            return 0 if success_count == len(results) else 1
            
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

