FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libopencv-dev \
    python3-opencv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
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

# Expose API port
EXPOSE 8000

# Default command (can be overridden)
# For CLI: CMD ["python", "main.py", "--help"]
# For API: CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["python", "main.py", "--help"]

