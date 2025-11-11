"""
Run representative PDF tests and save results to results directory.

This script extracts metadata from the three representative PDFs and saves
the results as JSON files for manual review.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.extraction_coordinator import ExtractionCoordinator
from utils.exceptions import ExtractionError, FileError

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Representative PDFs
PDFS = [
    ("Orbit (Mixed)", TEST_DATA_DIR / "Adaequare Inc._Orbit Inc._MSA.pdf"),
    ("DGS (Image-only)", TEST_DATA_DIR / "DGS_Adaequare Agreement_CounterSigned.pdf"),
    ("Mindlance (Text-only)", TEST_DATA_DIR / "Executed Master Service Agreement_Adaequare,Inc_Mindlance_05192016.pdf"),
]


def extract_and_save(pdf_name: str, pdf_path: Path) -> dict:
    """Extract metadata from PDF and save to results directory."""
    print(f"\n{'='*80}")
    print(f"Extracting: {pdf_name}")
    print(f"File: {pdf_path.name}")
    print(f"{'='*80}")
    
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return {"success": False, "error": f"File not found: {pdf_path}"}
    
    try:
        coordinator = ExtractionCoordinator()
        metadata = coordinator.extract_metadata(str(pdf_path))
        
        # Create result filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = pdf_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        result_file = RESULTS_DIR / f"test_{safe_name}_{timestamp}.json"
        
        # Prepare result data
        result_data = {
            "test_name": pdf_name,
            "pdf_file": pdf_path.name,
            "extraction_timestamp": datetime.now().isoformat(),
            "success": True,
            "metadata": metadata
        }
        
        # Save to file
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        print(f"[SUCCESS] Result saved to: {result_file.name}")
        
        # Print key fields
        lifecycle = metadata.get("Contract Lifecycle", {})
        commercial = metadata.get("Commercial Operations", {})
        risk = metadata.get("Risk & Compliance", {})
        
        print(f"\nExtracted Metadata:")
        print(f"  Execution Date: {lifecycle.get('Execution Date', 'Not Found')}")
        print(f"  Effective Date: {lifecycle.get('Effective Date', 'Not Found')}")
        print(f"  Expiration Date: {lifecycle.get('Expiration / Termination Date', 'Not Found')}")
        print(f"  Authorized Signatory: {lifecycle.get('Authorized Signatory', 'Not Found')}")
        print(f"  Billing Frequency: {commercial.get('Billing Frequency', 'Not Found')}")
        print(f"  Payment Terms: {commercial.get('Payment Terms', 'Not Found')}")
        
        # Check field lengths
        max_length = 0
        long_fields = []
        for category_name, category_data in metadata.items():
            for field_name, field_value in category_data.items():
                if len(field_value) > max_length:
                    max_length = len(field_value)
                if len(field_value) > 1000:
                    long_fields.append(f"{category_name}.{field_name} ({len(field_value)} chars)")
        
        if long_fields:
            print(f"\n[WARNING] Fields exceeding 1000 chars:")
            for field in long_fields:
                print(f"  - {field}")
        else:
            print(f"\n[OK] All fields within 1000 character limit (max: {max_length} chars)")
        
        result_data["result_file"] = str(result_file)
        return result_data
        
    except ExtractionError as e:
        error_msg = f"Extraction failed: {e}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg, "pdf_file": pdf_path.name}
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg, "pdf_file": pdf_path.name}


def main():
    """Run all representative PDF tests."""
    print("="*80)
    print("Representative PDFs Extraction Test")
    print("="*80)
    print(f"Results will be saved to: {RESULTS_DIR}")
    print()
    
    results = []
    
    for pdf_name, pdf_path in PDFS:
        result = extract_and_save(pdf_name, pdf_path)
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]
    
    print(f"\nTotal: {len(results)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    
    if successful:
        print(f"\n[SUCCESS] Extracted metadata from:")
        for r in successful:
            print(f"  - {r.get('test_name', 'Unknown')}: {r.get('result_file', 'N/A')}")
    
    if failed:
        print(f"\n[FAILED] Extraction failed for:")
        for r in failed:
            print(f"  - {r.get('pdf_file', 'Unknown')}: {r.get('error', 'Unknown error')}")
    
    print(f"\nAll results saved to: {RESULTS_DIR}")
    print("="*80)


if __name__ == "__main__":
    main()

