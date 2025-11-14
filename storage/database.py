"""
Database module for MSA Metadata Extractor.

Handles SQLite database operations for job tracking, result storage, and logging.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from config import DB_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


class ExtractionDB:
    """
    Database interface for extraction job tracking and storage.
    
    Manages:
    - Job metadata and status tracking
    - JSON result storage (default mode)
    - Log storage in monthly tables
    - Legacy mode support (file paths in DB)
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection and create schema if needed.
        
        Args:
            db_path: Optional path to database file. Defaults to config.DB_PATH.
        """
        self.db_path = db_path or DB_PATH
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database connection and create schema."""
        try:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if database already exists
            db_exists = self.db_path.exists()
            
            # Connect to database
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
            
            # Create tables (idempotent - safe to call multiple times)
            self._create_extractions_table()
            self._create_indexes()
            
            # Create current month's log table
            self._ensure_log_table()
            
            # Only log at INFO level if database was just created, otherwise DEBUG
            if not db_exists:
                logger.info(f"Database initialized (new): {self.db_path}")
            else:
                logger.debug(f"Database connected: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_extractions_table(self):
        """Create the extractions table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extractions (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                result_json TEXT,
                pdf_storage_path TEXT,
                pdf_storage_type TEXT DEFAULT 'local',
                result_json_path TEXT,
                log_path TEXT,
                extraction_method TEXT,
                llm_processing_mode TEXT,
                ocr_engine TEXT,
                metadata TEXT
            )
        """)
        self.conn.commit()
        logger.debug("Extractions table created/verified")
    
    def _create_indexes(self):
        """Create indexes on extractions table."""
        cursor = self.conn.cursor()
        
        # Create indexes if they don't exist
        indexes = [
            ("idx_extractions_status", "extractions", "status"),
            ("idx_extractions_created_at", "extractions", "created_at"),
            ("idx_extractions_file_name", "extractions", "file_name"),
        ]
        
        for idx_name, table, column in indexes:
            try:
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})
                """)
            except sqlite3.OperationalError:
                # Index might already exist
                pass
        
        self.conn.commit()
        logger.debug("Indexes created/verified")
    
    def _get_log_table_name(self, timestamp: Optional[datetime] = None) -> str:
        """
        Get the log table name for a given timestamp.
        
        Args:
            timestamp: Timestamp to get table for. Defaults to current month.
        
        Returns:
            Table name like 'extraction_logs_2025_11'
        """
        if timestamp is None:
            timestamp = datetime.now()
        return f"extraction_logs_{timestamp.strftime('%Y_%m')}"
    
    def _ensure_log_table(self, timestamp: Optional[datetime] = None):
        """
        Ensure the log table for a given month exists.
        
        Args:
            timestamp: Timestamp to ensure table for. Defaults to current month.
        """
        table_name = self._get_log_table_name(timestamp)
        cursor = self.conn.cursor()
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extraction_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                module TEXT,
                details TEXT,
                FOREIGN KEY (extraction_id) REFERENCES extractions(id)
            )
        """)
        
        # Create index on extraction_id for faster queries
        try:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_extraction_id 
                ON {table_name}(extraction_id)
            """)
        except sqlite3.OperationalError:
            pass
        
        self.conn.commit()
        logger.debug(f"Log table created/verified: {table_name}")
    
    def create_job(
        self,
        file_name: str,
        pdf_storage_path: str,
        file_size: Optional[int] = None,
        extraction_method: Optional[str] = None,
        llm_processing_mode: Optional[str] = None,
        ocr_engine: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> str:
        """
        Create a new extraction job.
        
        Args:
            file_name: Original filename
            pdf_storage_path: Path to stored PDF file
            file_size: File size in bytes
            extraction_method: EXTRACTION_METHOD used
            llm_processing_mode: LLM_PROCESSING_MODE used
            ocr_engine: OCR_ENGINE used (if applicable)
            job_id: Optional job UUID (if not provided, generates a new one)
        
        Returns:
            Job UUID (str)
        """
        if job_id is None:
            job_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO extractions (
                id, file_name, pdf_storage_path, file_size, status,
                extraction_method, llm_processing_mode, ocr_engine
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, file_name, pdf_storage_path, file_size, "pending",
            extraction_method, llm_processing_mode, ocr_engine
        ))
        
        self.conn.commit()
        logger.info(f"Created job: {job_id} for file: {file_name}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a job by ID.
        
        Args:
            job_id: Job UUID
        
        Returns:
            Job dict with result_json parsed, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM extractions WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        # Convert Row to dict
        job = dict(row)
        
        # Parse result_json if present
        if job.get("result_json"):
            try:
                job["result_json"] = json.loads(job["result_json"])
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse result_json for job {job_id}")
                job["result_json"] = None
        
        # Parse metadata if present
        if job.get("metadata"):
            try:
                job["metadata"] = json.loads(job["metadata"])
            except (json.JSONDecodeError, TypeError):
                job["metadata"] = None
        
        return job
    
    def update_job_status(
        self,
        job_id: str,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ):
        """
        Update job status and timestamps.
        
        Args:
            job_id: Job UUID
            status: New status ('pending', 'processing', 'completed', 'failed')
            started_at: When processing started
            completed_at: When processing finished
            error_message: Error message if failed
        """
        cursor = self.conn.cursor()
        
        # Build update query dynamically
        updates = ["status = ?"]
        params = [status]
        
        if started_at:
            updates.append("started_at = ?")
            params.append(started_at.isoformat())
        
        if completed_at:
            updates.append("completed_at = ?")
            params.append(completed_at.isoformat())
        
        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)
        
        params.append(job_id)
        
        cursor.execute(
            f"UPDATE extractions SET {', '.join(updates)} WHERE id = ?",
            params
        )
        
        self.conn.commit()
        logger.debug(f"Updated job {job_id} status to {status}")
    
    def complete_job(
        self,
        job_id: str,
        result_json_dict: Dict[str, Any],
        pdf_storage_path: str,
        pdf_storage_type: str = "local",
        result_json_path: Optional[str] = None,
        log_path: Optional[str] = None,
    ):
        """
        Mark job as completed and store result JSON.
        
        Args:
            job_id: Job UUID
            result_json_dict: Extracted metadata as dict
            pdf_storage_path: Path to stored PDF
            pdf_storage_type: Storage type ('local' or 'gcs')
            result_json_path: Legacy mode only - path to JSON file
            log_path: Legacy mode only - path to log file
        """
        cursor = self.conn.cursor()
        
        # Serialize result_json
        result_json_str = json.dumps(result_json_dict, ensure_ascii=False)
        
        # Update job
        cursor.execute("""
            UPDATE extractions
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                result_json = ?,
                pdf_storage_path = ?,
                pdf_storage_type = ?,
                result_json_path = ?,
                log_path = ?
            WHERE id = ?
        """, (
            result_json_str,
            pdf_storage_path,
            pdf_storage_type,
            result_json_path,
            log_path,
            job_id
        ))
        
        self.conn.commit()
        logger.info(f"Completed job {job_id}")
    
    def add_log_entry(
        self,
        job_id: str,
        level: str,
        message: str,
        module: Optional[str] = None,
        details: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Add a log entry to the current month's log table.
        
        Args:
            job_id: Job UUID
            level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            message: Log message
            module: Module name (optional)
            details: Additional details (optional)
            timestamp: Log timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Ensure log table exists for this month
        self._ensure_log_table(timestamp)
        table_name = self._get_log_table_name(timestamp)
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO {table_name} (
                extraction_id, timestamp, level, message, module, details
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            timestamp.isoformat(),
            level,
            message,
            module,
            details
        ))
        
        self.conn.commit()
    
    def get_logs(
        self,
        job_id: str,
        limit: int = 1000,
        level: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get log entries for a job.
        
        Args:
            job_id: Job UUID
            limit: Maximum number of entries to return
            level: Filter by log level (optional)
        
        Returns:
            List of log entry dicts
        """
        # Get all log tables (we'll search across months)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'extraction_logs_%'
            ORDER BY name DESC
        """)
        table_names = [row[0] for row in cursor.fetchall()]
        
        all_logs = []
        
        for table_name in table_names:
            query = f"SELECT * FROM {table_name} WHERE extraction_id = ?"
            params = [job_id]
            
            if level:
                query += " AND level = ?"
                params.append(level)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            logs = [dict(row) for row in cursor.fetchall()]
            all_logs.extend(logs)
        
        # Sort by timestamp descending and limit
        all_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_logs[:limit]
    
    def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "created_at DESC",
    ) -> List[Dict[str, Any]]:
        """
        List jobs with optional filtering.
        
        Args:
            status: Filter by status (optional)
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            sort: Sort order (SQL ORDER BY clause)
        
        Returns:
            List of job dicts
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM extractions"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += f" ORDER BY {sort} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        jobs = [dict(row) for row in cursor.fetchall()]
        
        # Parse JSON fields
        for job in jobs:
            if job.get("result_json"):
                try:
                    job["result_json"] = json.loads(job["result_json"])
                except (json.JSONDecodeError, TypeError):
                    job["result_json"] = None
            
            if job.get("metadata"):
                try:
                    job["metadata"] = json.loads(job["metadata"])
                except (json.JSONDecodeError, TypeError):
                    job["metadata"] = None
        
        return jobs
    
    def delete_job(self, job_id: str, hard_delete: bool = False):
        """
        Delete a job (soft delete by default, hard delete if specified).
        
        Args:
            job_id: Job UUID
            hard_delete: If True, permanently delete. If False, mark as deleted.
        """
        if hard_delete:
            cursor = self.conn.cursor()
            
            # Delete log entries (across all months)
            table_names = self._get_all_log_tables()
            for table_name in table_names:
                cursor.execute(f"DELETE FROM {table_name} WHERE extraction_id = ?", (job_id,))
            
            # Delete job
            cursor.execute("DELETE FROM extractions WHERE id = ?", (job_id,))
            self.conn.commit()
            logger.info(f"Hard deleted job {job_id}")
        else:
            # Soft delete: update status to 'deleted' (if we add that status)
            # For now, just hard delete
            self.delete_job(job_id, hard_delete=True)
    
    def _get_all_log_tables(self) -> List[str]:
        """Get all log table names."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'extraction_logs_%'
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def get_jobs_for_cleanup(
        self,
        days_old: int,
        max_count: Optional[int] = None,
    ) -> List[str]:
        """
        Get job IDs eligible for cleanup.
        
        Args:
            days_old: Delete PDFs older than N days
            max_count: Maximum number of PDFs to keep (optional)
        
        Returns:
            List of job IDs
        """
        cursor = self.conn.cursor()
        
        if max_count is not None:
            if max_count == 0:
                # Keep 0 jobs = all jobs eligible for cleanup
                query = """
                    SELECT id FROM extractions
                    WHERE status = 'completed'
                    ORDER BY created_at ASC
                """
                params = []
            else:
                # Count-based cleanup: keep only the most recent N jobs
                query = """
                    SELECT id FROM extractions
                    WHERE status = 'completed'
                    AND id NOT IN (
                        SELECT id FROM extractions
                        WHERE status = 'completed'
                        ORDER BY created_at DESC
                        LIMIT ?
                    )
                    ORDER BY created_at ASC
                """
                params = [max_count]
        else:
            # Time-based cleanup: jobs older than N days
            query = """
                SELECT id FROM extractions
                WHERE status = 'completed'
                AND created_at < datetime('now', '-' || ? || ' days')
                ORDER BY created_at ASC
            """
            params = [days_old]
        
        cursor.execute(query, params)
        return [row[0] for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

