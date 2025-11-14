"""
Live mode testing script for MSA Extractor API.

Tests different extraction method and LLM processing mode combinations
against real PDFs to diagnose issues with extraction modes, GCP, or Docker.

This is NOT a pytest test - run directly: python tests/test_live_modes.py
"""

import requests
import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Service URL
SERVICE_URL = "https://msa-extractor-api-592845797104.us-central1.run.app"

# PDF files to test (relative to project root)
PDF_FILES = [
    "scratch/Executed Master Service Agreement_Adaequare,Inc_Mindlance_05192016.pdf",
    "scratch/Adaequare Inc._Orbit Inc._MSA.pdf",
    "scratch/Executed Subcontracting Agreement_Adaequare Inc_DISYS_07222020.pdf"
]

# Test combinations: (extraction_method, llm_processing_mode, description)
TEST_COMBINATIONS = [
    ("hybrid", "multimodal", "Hybrid + Multimodal (default)"),
    ("hybrid", "text_llm", "Hybrid + Text LLM"),
    ("hybrid", "vision_llm", "Hybrid + Vision LLM"),
    ("hybrid", "dual_llm", "Hybrid + Dual LLM"),
    ("text_direct", "text_llm", "Text Direct + Text LLM"),
    ("vision_all", "vision_llm", "Vision All + Vision LLM"),
    ("ocr_all", "text_llm", "OCR All + Text LLM"),
]


def upload_file(file_path: str, extraction_method: Optional[str] = None, 
                llm_processing_mode: Optional[str] = None) -> Dict:
    """Upload a file and return the response."""
    url = f"{SERVICE_URL}/api/v1/extract/upload"
    
    # Resolve path relative to project root
    project_root = Path(__file__).parent.parent
    full_path = project_root / file_path
    
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {full_path}")
    
    with open(full_path, 'rb') as f:
        files = {'file': f}
        data = {}
        if extraction_method:
            data['extraction_method'] = extraction_method
        if llm_processing_mode:
            data['llm_processing_mode'] = llm_processing_mode
        
        response = requests.post(url, files=files, data=data)
        
        # Get full error details
        if not response.ok:
            error_detail = ""
            try:
                error_json = response.json()
                error_detail = error_json.get('detail', str(error_json))
            except:
                error_detail = response.text[:500]
            
            raise requests.HTTPError(
                f"{response.status_code} {response.reason}: {error_detail} "
                f"for url: {url}"
            )
        
        return response.json()


def check_status(job_id: str) -> Dict:
    """Check job status."""
    url = f"{SERVICE_URL}/api/v1/extract/status/{job_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def check_result(job_id: str) -> Tuple[int, Dict]:
    """Check job result. Returns (status_code, data)."""
    url = f"{SERVICE_URL}/api/v1/extract/result/{job_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.status_code, response.json()
    else:
        return response.status_code, response.text


def wait_for_completion(job_id: str, max_wait: int = 600, poll_interval: int = 5) -> Dict:
    """Wait for job to complete and return final status."""
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status = check_status(job_id)
        current_status = status.get('status')
        
        elapsed = int(time.time() - start_time)
        print(f"  Status: {current_status} (elapsed: {elapsed}s)", end='\r')
        
        if current_status in ['completed', 'failed']:
            print()  # New line after status updates
            return status
        
        time.sleep(poll_interval)
    
    # Timeout
    print()  # New line
    return check_status(job_id)


def test_combination(file_path: str, extraction_method: str, llm_processing_mode: str, 
                     description: str) -> Dict:
    """Test a specific extraction mode combination."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"File: {file_path.split('/')[-1]}")
    print(f"Extraction Method: {extraction_method}")
    print(f"LLM Mode: {llm_processing_mode}")
    print(f"{'='*60}")
    
    try:
        # Upload
        print("Uploading file...")
        upload_response = upload_file(file_path, extraction_method, llm_processing_mode)
        job_id = upload_response.get('job_id')
        print(f"✅ Upload successful - Job ID: {job_id}")
        
        # Wait for completion
        print("Waiting for extraction...")
        final_status = wait_for_completion(job_id, max_wait=600)  # 10 min max
        
        # Get result
        status_code, result = check_result(job_id)
        
        return {
            'job_id': job_id,
            'status': final_status.get('status'),
            'error': final_status.get('error_message'),
            'result_status_code': status_code,
            'has_result': status_code == 200,
            'description': description,
            'extraction_method': extraction_method,
            'llm_processing_mode': llm_processing_mode
        }
        
    except requests.HTTPError as e:
        # HTTP errors - show full details
        error_msg = str(e)
        return {
            'job_id': None,
            'status': 'error',
            'error': error_msg,
            'result_status_code': None,
            'has_result': False,
            'description': description,
            'extraction_method': extraction_method,
            'llm_processing_mode': llm_processing_mode
        }
    except Exception as e:
        # Other errors
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        return {
            'job_id': None,
            'status': 'error',
            'error': error_msg,
            'result_status_code': None,
            'has_result': False,
            'description': description,
            'extraction_method': extraction_method,
            'llm_processing_mode': llm_processing_mode
        }


def main():
    """Run all tests and generate summary."""
    print("="*60)
    print("MSA Extractor - Live Mode Testing")
    print("="*60)
    print(f"Service URL: {SERVICE_URL}")
    print(f"Testing {len(PDF_FILES)} PDFs with {len(TEST_COMBINATIONS)} mode combinations")
    print("="*60)
    
    results = []
    
    for pdf_file in PDF_FILES:
        print(f"\n\n{'#'*60}")
        print(f"Testing PDF: {pdf_file.split('/')[-1]}")
        print(f"{'#'*60}")
        
        for extraction_method, llm_mode, description in TEST_COMBINATIONS:
            result = test_combination(pdf_file, extraction_method, llm_mode, description)
            result['file'] = pdf_file.split('/')[-1]
            results.append(result)
            
            # Brief summary
            job_id = result.get('job_id', 'N/A')
            if result['status'] == 'completed':
                print(f"  ✅ SUCCESS: {description} (Job ID: {job_id})")
            elif result['status'] == 'failed':
                print(f"  ❌ FAILED: {description} (Job ID: {job_id})")
                error = result.get('error', 'Unknown')
                error_preview = error[:100] + '...' if len(error) > 100 else error
                print(f"     Error: {error_preview}")
            elif result['status'] == 'error':
                print(f"  ❌ ERROR: {description} (Job ID: {job_id})")
                error = result.get('error', 'Unknown')
                error_preview = error[:200] + '...' if len(error) > 200 else error
                print(f"     Error: {error_preview}")
            else:
                print(f"  ⏳ {result['status'].upper()}: {description} (Job ID: {job_id})")
    
    # Print summary
    print("\n\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    # Group by mode
    mode_results = {}
    for result in results:
        key = result.get('description', 'Unknown')
        if key not in mode_results:
            mode_results[key] = {'success': 0, 'failed': 0, 'errors': []}
        
        if result['status'] == 'completed':
            mode_results[key]['success'] += 1
        elif result['status'] == 'failed':
            mode_results[key]['failed'] += 1
            if result.get('error'):
                mode_results[key]['errors'].append(result['error'][:150])
    
    print("\nResults by Mode:")
    for mode, stats in mode_results.items():
        total = stats['success'] + stats['failed']
        success_rate = (stats['success'] / total * 100) if total > 0 else 0
        print(f"\n{mode}:")
        print(f"  Success: {stats['success']}/{total} ({success_rate:.1f}%)")
        print(f"  Failed: {stats['failed']}/{total}")
        if stats['errors']:
            print(f"  Sample Errors:")
            for error in stats['errors'][:2]:  # Show first 2 errors
                print(f"    - {error}")
    
    # Group by file
    print("\n\nResults by File:")
    file_results = {}
    for result in results:
        file = result.get('file', 'Unknown')
        if file not in file_results:
            file_results[file] = {'success': 0, 'failed': 0}
        
        if result['status'] == 'completed':
            file_results[file]['success'] += 1
        elif result['status'] == 'failed':
            file_results[file]['failed'] += 1
    
    for file, stats in file_results.items():
        total = stats['success'] + stats['failed']
        success_rate = (stats['success'] / total * 100) if total > 0 else 0
        print(f"\n{file}:")
        print(f"  Success: {stats['success']}/{total} ({success_rate:.1f}%)")
        print(f"  Failed: {stats['failed']}/{total}")
    
    # Detailed results table
    print("\n\n" + "="*60)
    print("DETAILED RESULTS")
    print("="*60)
    print(f"{'File':<35} {'Mode':<25} {'Job ID':<38} {'Status':<12}")
    print("-" * 110)
    for result in results:
        file = result.get('file', 'Unknown')[:33]
        mode = result.get('description', 'Unknown')[:23]
        job_id = result.get('job_id', 'N/A')[:36]
        status = result.get('status', 'Unknown')[:10]
        print(f"{file:<35} {mode:<25} {job_id:<38} {status:<12}")
    
    # Error details table
    error_results = [r for r in results if r.get('status') in ['failed', 'error']]
    if error_results:
        print("\n\n" + "="*60)
        print("ERROR DETAILS")
        print("="*60)
        print(f"{'Job ID':<38} {'Mode':<25} {'Error':<50}")
        print("-" * 113)
        for result in error_results:
            job_id = result.get('job_id', 'N/A')[:36]
            mode = result.get('description', 'Unknown')[:23]
            error = (result.get('error', '') or '')[:48]
            print(f"{job_id:<38} {mode:<25} {error:<50}")
    
    # Analysis
    print("\n\n" + "="*60)
    print("ANALYSIS")
    print("="*60)
    
    # Check if all text_llm modes fail
    text_llm_results = [r for r in results if r.get('llm_processing_mode') == 'text_llm']
    text_llm_failed = [r for r in text_llm_results if r['status'] == 'failed']
    if text_llm_failed and len(text_llm_failed) == len(text_llm_results):
        print("\n⚠️  ALL text_llm modes failed - suggests API key or text LLM issue")
    
    # Check if all modes fail
    all_failed = all(r['status'] == 'failed' for r in results)
    if all_failed:
        print("\n⚠️  ALL modes failed - suggests GCP/Docker/API key issue")
    
    # Check if specific extraction methods fail
    extraction_methods = {}
    for result in results:
        method = result.get('extraction_method', 'Unknown')
        if method not in extraction_methods:
            extraction_methods[method] = {'success': 0, 'failed': 0}
        if result['status'] == 'completed':
            extraction_methods[method]['success'] += 1
        elif result['status'] == 'failed':
            extraction_methods[method]['failed'] += 1
    
    print("\nResults by Extraction Method:")
    for method, stats in extraction_methods.items():
        total = stats['success'] + stats['failed']
        success_rate = (stats['success'] / total * 100) if total > 0 else 0
        print(f"  {method}: {stats['success']}/{total} success ({success_rate:.1f}%)")
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)


if __name__ == "__main__":
    main()

