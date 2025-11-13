FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libopencv-dev \
    python3-opencv \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
# Note: We install packages directly (not in venv) because Docker containers
# already provide isolation. The pip warning about root user is expected and
# acceptable in containers. For local development, use venv outside Docker.
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/results /app/logs /app/contracts /app/uploads /app/storage

# Set environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1
ENV TESSERACT_LANG=eng
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV PYTHONPATH=/app

# Expose API port
EXPOSE 8000

# Default command for Cloud Run / API deployment
# Cloud Run sets PORT environment variable automatically (usually 8080)
# PYTHONPATH is set to /app so Python can find root-level modules (storage, config, utils, etc.)
# Using 'python -m uvicorn' ensures PYTHONPATH is respected
# For CLI usage, override with: docker run ... python main.py --help
CMD ["/bin/sh", "-c", "python -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

