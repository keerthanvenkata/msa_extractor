"""
Health check endpoint for MSA Metadata Extractor API.

Used by load balancers and monitoring systems.
"""

from datetime import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from api.dependencies import get_db
from api.models.responses import HealthResponse
from config import DB_PATH
from storage.database import ExtractionDB
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint"
)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Checks database connectivity and returns service status.
    No authentication required.
    
    **Response:**
    - Service status (healthy/unhealthy)
    - Database connection status
    - API version
    - Storage type
    
    **Status Codes:**
    - `200 OK`: Service is healthy
    - `503 Service Unavailable`: Service is unhealthy
    """
    try:
        # Try to connect to database
        db = ExtractionDB(db_path=DB_PATH)
        try:
            # Test database connection with a simple query
            db.conn.execute("SELECT 1").fetchone()
            db_status = "connected"
            health_status = "healthy"
            error = None
        except Exception as e:
            db_status = "disconnected"
            health_status = "unhealthy"
            error = f"Database connection failed: {str(e)}"
            logger.error(f"Health check failed: {error}")
        finally:
            db.close()
        
        # Determine storage type (local for now, GCS in future)
        storage_type = "local"
        
        # Build response
        response = HealthResponse(
            status=health_status,
            version="1.0.0",
            database=db_status,
            storage_type=storage_type,
            timestamp=datetime.now().isoformat(),
            error=error
        )
        
        # Return appropriate status code
        if health_status == "healthy":
            return response
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response.model_dump()
            )
            
    except Exception as e:
        # Unexpected error during health check
        logger.error(f"Health check error: {e}", exc_info=True)
        error_response = HealthResponse(
            status="unhealthy",
            version="1.0.0",
            database="unknown",
            storage_type="local",
            timestamp=datetime.now().isoformat(),
            error=f"Health check failed: {str(e)}"
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response.model_dump()
        )

