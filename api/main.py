"""
FastAPI application entry point for MSA Metadata Extractor API.

Main application that registers all routers and configures middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import extract, health, jobs
from api import __version__
from utils.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MSA Metadata Extractor API",
    description="REST API for extracting structured metadata from Master Service Agreements",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS (allow all origins for now - configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure allowed origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(extract.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(f"MSA Metadata Extractor API v{__version__} starting up")
    logger.info("API documentation available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("MSA Metadata Extractor API shutting down")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MSA Metadata Extractor API",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    from config import API_HOST, API_PORT, API_RELOAD
    
    uvicorn.run(
        "api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_RELOAD
    )

