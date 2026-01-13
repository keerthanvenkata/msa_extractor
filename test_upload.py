"""
Temporary script to test file upload and polling for results.
"""
import time
import sys
from pathlib import Path
import requests

# Configuration
API_URL = "http://localhost:8080/api/v1"
FILE_PATH = "templates/template.pdf"
POLL_INTERVAL = 2  # seconds
MAX_WAIT_TIME = 300  # 5 minutes max

def upload_file(file_path: str, extraction_method: str = "hybrid", 
                llm_processing_mode: str = "multimodal") -> dict:
    """Upload a file and return the response."""
    url = f"{API_URL}/extract/upload"
    
    # Resolve path relative to script location
    script_dir = Path(__file__).parent
    full_path = script_dir / file_path
    
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {full_path}")
    
    print(f"Uploading file: {full_path}")
    
    with open(full_path, 'rb') as f:
        files = {'file': (full_path.name, f, 'application/pdf')}
        data = {
            'extraction_method': extraction_method,
            'llm_processing_mode': llm_processing_mode
        }
        
        response = requests.post(url, files=files, data=data)
        
        if not response.ok:
            error_detail = ""
            try:
                error_json = response.json()
                error_detail = error_json.get('detail', str(error_json))
            except:
                error_detail = response.text[:500]
            
            raise requests.HTTPError(
                f"{response.status_code} {response.reason}: {error_detail}"
            )
        
        return response.json()


def check_status(job_id: str) -> dict:
    """Check job status."""
    url = f"{API_URL}/extract/status/{job_id}"
    response = requests.get(url)
    
    if not response.ok:
        error_detail = ""
        try:
            error_json = response.json()
            error_detail = error_json.get('detail', str(error_json))
        except:
            error_detail = response.text[:500]
        
        raise requests.HTTPError(
            f"{response.status_code} {response.reason}: {error_detail}"
        )
    
    return response.json()


def get_result(job_id: str) -> dict:
    """Get extraction result."""
    url = f"{API_URL}/extract/result/{job_id}"
    response = requests.get(url)
    
    if not response.ok:
        error_detail = ""
        try:
            error_json = response.json()
            error_detail = error_json.get('detail', str(error_json))
        except:
            error_detail = response.text[:500]
        
        raise requests.HTTPError(
            f"{response.status_code} {response.reason}: {error_detail}"
        )
    
    return response.json()


def poll_until_complete(job_id: str) -> dict:
    """Poll job status until completed or failed."""
    start_time = time.time()
    
    print(f"\nPolling for job: {job_id}")
    print("Status updates:")
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > MAX_WAIT_TIME:
            raise TimeoutError(f"Job {job_id} did not complete within {MAX_WAIT_TIME} seconds")
        
        try:
            status_response = check_status(job_id)
            status = status_response.get('status')
            
            print(f"  [{elapsed:.1f}s] Status: {status}", end='')
            
            if status == 'completed':
                print(" ✓")
                return get_result(job_id)
            elif status == 'failed':
                print(" ✗")
                error_msg = status_response.get('error_message', 'Unknown error')
                raise RuntimeError(f"Job failed: {error_msg}")
            else:
                print(" (waiting...)")
                time.sleep(POLL_INTERVAL)
                
        except requests.HTTPError as e:
            if "Job not found" in str(e):
                raise RuntimeError(f"Job {job_id} not found. Container may have restarted.")
            raise


def main():
    """Main function."""
    print("=" * 60)
    print("MSA Metadata Extractor - Test Upload Script")
    print("=" * 60)
    
    try:
        # Step 1: Upload file
        print("\n[1/3] Uploading file...")
        upload_response = upload_file(FILE_PATH)
        job_id = upload_response['job_id']
        print(f"✓ Upload successful!")
        print(f"  Job ID: {job_id}")
        print(f"  File: {upload_response.get('file_name')}")
        print(f"  Size: {upload_response.get('file_size')} bytes")
        print(f"  Status: {upload_response.get('status')}")
        
        # Step 2: Poll for completion
        print("\n[2/3] Waiting for extraction to complete...")
        result = poll_until_complete(job_id)
        
        # Step 3: Print results
        print("\n[3/3] Extraction completed!")
        print("\n" + "=" * 60)
        print("EXTRACTION RESULT:")
        print("=" * 60)
        
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 60)
        print("✓ Test completed successfully!")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Error: Could not connect to API at {API_URL}", file=sys.stderr)
        print("  Make sure the API server is running:", file=sys.stderr)
        print("    uvicorn api.main:app --host 0.0.0.0 --port 8080", file=sys.stderr)
        sys.exit(1)
    except requests.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}", file=sys.stderr)
        sys.exit(1)
    except (TimeoutError, RuntimeError) as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

