"""
Unit tests for storage.database module.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import json

from storage.database import ExtractionDB


class TestExtractionDB:
    """Test ExtractionDB class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        
        db = ExtractionDB(db_path=db_path)
        yield db
        
        # Cleanup
        db.close()
        if db_path.exists():
            db_path.unlink()
    
    def test_create_job(self, temp_db):
        """Test creating a job."""
        job_id = temp_db.create_job(
            file_name="test.pdf",
            pdf_storage_path="uploads/test.pdf",
            file_size=1024,
            extraction_method="hybrid",
            llm_processing_mode="multimodal",
            ocr_engine="tesseract"
        )
        
        assert job_id is not None
        assert len(job_id) == 36  # UUID length
    
    def test_get_job(self, temp_db):
        """Test getting a job."""
        job_id = temp_db.create_job(
            file_name="test.pdf",
            pdf_storage_path="uploads/test.pdf",
            file_size=1024
        )
        
        job = temp_db.get_job(job_id)
        
        assert job is not None
        assert job["id"] == job_id
        assert job["file_name"] == "test.pdf"
        assert job["status"] == "pending"
        assert job["pdf_storage_path"] == "uploads/test.pdf"
    
    def test_update_job_status(self, temp_db):
        """Test updating job status."""
        job_id = temp_db.create_job(
            file_name="test.pdf",
            pdf_storage_path="uploads/test.pdf"
        )
        
        started = datetime.now()
        temp_db.update_job_status(job_id, "processing", started_at=started)
        
        job = temp_db.get_job(job_id)
        assert job["status"] == "processing"
        assert job["started_at"] is not None
    
    def test_complete_job(self, temp_db):
        """Test completing a job with result JSON."""
        job_id = temp_db.create_job(
            file_name="test.pdf",
            pdf_storage_path="uploads/test.pdf"
        )
        
        result_json = {
            "Contract Lifecycle": {
                "Effective Date": "2025-01-01"
            }
        }
        
        temp_db.complete_job(
            job_id=job_id,
            result_json_dict=result_json,
            pdf_storage_path="uploads/test.pdf",
            pdf_storage_type="local"
        )
        
        job = temp_db.get_job(job_id)
        assert job["status"] == "completed"
        assert job["result_json"] == result_json
        assert job["completed_at"] is not None
    
    def test_complete_job_legacy_mode(self, temp_db):
        """Test completing a job in legacy mode (with file paths)."""
        job_id = temp_db.create_job(
            file_name="test.pdf",
            pdf_storage_path="uploads/test.pdf"
        )
        
        result_json = {"test": "data"}
        
        temp_db.complete_job(
            job_id=job_id,
            result_json_dict=result_json,
            pdf_storage_path="uploads/test.pdf",
            pdf_storage_type="local",
            result_json_path="results/test.json",
            log_path="logs/test.log"
        )
        
        job = temp_db.get_job(job_id)
        assert job["result_json_path"] == "results/test.json"
        assert job["log_path"] == "logs/test.log"
    
    def test_add_log_entry(self, temp_db):
        """Test adding log entries."""
        job_id = temp_db.create_job(
            file_name="test.pdf",
            pdf_storage_path="uploads/test.pdf"
        )
        
        temp_db.add_log_entry(
            job_id=job_id,
            level="INFO",
            message="Test log message",
            module="test_module"
        )
        
        logs = temp_db.get_logs(job_id)
        assert len(logs) == 1
        assert logs[0]["level"] == "INFO"
        assert logs[0]["message"] == "Test log message"
        assert logs[0]["module"] == "test_module"
    
    def test_get_logs_filtered(self, temp_db):
        """Test getting logs filtered by level."""
        job_id = temp_db.create_job(
            file_name="test.pdf",
            pdf_storage_path="uploads/test.pdf"
        )
        
        temp_db.add_log_entry(job_id, "INFO", "Info message")
        temp_db.add_log_entry(job_id, "ERROR", "Error message")
        temp_db.add_log_entry(job_id, "WARNING", "Warning message")
        
        error_logs = temp_db.get_logs(job_id, level="ERROR")
        assert len(error_logs) == 1
        assert error_logs[0]["level"] == "ERROR"
    
    def test_list_jobs(self, temp_db):
        """Test listing jobs."""
        # Create multiple jobs
        for i in range(5):
            temp_db.create_job(
                file_name=f"test_{i}.pdf",
                pdf_storage_path=f"uploads/test_{i}.pdf"
            )
        
        jobs = temp_db.list_jobs(limit=10)
        assert len(jobs) == 5
    
    def test_list_jobs_filtered_by_status(self, temp_db):
        """Test listing jobs filtered by status."""
        job_id1 = temp_db.create_job(
            file_name="test1.pdf",
            pdf_storage_path="uploads/test1.pdf"
        )
        job_id2 = temp_db.create_job(
            file_name="test2.pdf",
            pdf_storage_path="uploads/test2.pdf"
        )
        
        temp_db.update_job_status(job_id1, "completed")
        
        completed_jobs = temp_db.list_jobs(status="completed")
        assert len(completed_jobs) == 1
        assert completed_jobs[0]["id"] == job_id1
    
    def test_get_jobs_for_cleanup(self, temp_db):
        """Test getting jobs for cleanup."""
        # Create a completed job
        job_id = temp_db.create_job(
            file_name="test.pdf",
            pdf_storage_path="uploads/test.pdf"
        )
        temp_db.complete_job(
            job_id=job_id,
            result_json_dict={"test": "data"},
            pdf_storage_path="uploads/test.pdf"
        )
        
        # Get jobs for cleanup by count (keep only 0 most recent = all eligible)
        cleanup_jobs = temp_db.get_jobs_for_cleanup(days_old=365, max_count=0)
        assert len(cleanup_jobs) >= 1
        assert job_id in cleanup_jobs
    
    def test_monthly_log_tables(self, temp_db):
        """Test that log tables are created monthly."""
        job_id = temp_db.create_job(
            file_name="test.pdf",
            pdf_storage_path="uploads/test.pdf"
        )
        
        # Add log entry (creates current month's table)
        temp_db.add_log_entry(job_id, "INFO", "Test message")
        
        # Verify table exists
        cursor = temp_db.conn.cursor()
        table_name = temp_db._get_log_table_name()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        assert count == 1

