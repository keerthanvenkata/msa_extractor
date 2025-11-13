# Linux & Docker Setup Guide

This guide covers setting up the MSA Metadata Extractor on Linux and in Docker containers.

## Linux Setup

### 1. Python Environment

```bash
# Install Python 3.10+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# Or use pyenv for version management
pyenv install 3.10.12
pyenv local 3.10.12

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
```

### 2. Install System Dependencies

#### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Tesseract OCR
sudo apt install -y tesseract-ocr tesseract-ocr-eng

# Install additional languages (optional)
sudo apt install -y tesseract-ocr-fra tesseract-ocr-spa tesseract-ocr-deu

# Install OpenCV dependencies
sudo apt install -y libopencv-dev python3-opencv

# Install other system dependencies
sudo apt install -y libgl1-mesa-glx libglib2.0-0
```

#### CentOS/RHEL/Fedora

```bash
# Install Tesseract OCR
sudo dnf install -y tesseract tesseract-langpack-eng

# Install OpenCV dependencies
sudo dnf install -y opencv opencv-devel
```

#### Arch Linux

```bash
# Install Tesseract OCR
sudo pacman -S tesseract tesseract-data-eng

# Install OpenCV
sudo pacman -S opencv
```

### 3. Install Python Packages

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env` file:

```env
# Required
GEMINI_API_KEY=your_api_key_here

# Optional Tesseract configuration (usually not needed on Linux)
# TESSERACT_CMD=/usr/bin/tesseract  # Usually in PATH
# TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata  # Usually default

# Optional: Other settings
GEMINI_TEXT_MODEL=gemini-2.5-pro
GEMINI_VISION_MODEL=gemini-2.5-pro
EXTRACTION_METHOD=hybrid
LLM_PROCESSING_MODE=multimodal
```

### 5. Verify Installation

```bash
# Check Tesseract
tesseract --version

# Test Python imports
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

## Docker Setup

### Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
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

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
# Note: We install packages directly (not in venv) because Docker containers
# already provide isolation. The pip warning about root user is expected and
# acceptable in containers. For local development, use venv outside Docker.
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/results /app/logs /app/contracts

# Set environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1
ENV TESSERACT_LANG=eng

# Default command
CMD ["python", "main.py", "--help"]
```

### Docker Compose

The `docker-compose.yml` provides two services:

1. **CLI Service** (`msa-extractor-cli`): For batch processing via command line
2. **API Service** (`msa-extractor-api`): FastAPI backend server (port 8000)

**Example `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  # CLI Service (for batch processing)
  msa-extractor-cli:
    build: .
    volumes:
      - ./contracts:/app/contracts:ro
      - ./results:/app/results
      - ./logs:/app/logs
      - ./uploads:/app/uploads
      - ./storage:/app/storage
      - ./.env:/app/.env:ro
    command: python main.py --dir /app/contracts --out-dir /app/results

  # API Service (FastAPI backend)
  msa-extractor-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./results:/app/results
      - ./logs:/app/logs
      - ./uploads:/app/uploads
      - ./storage:/app/storage
      - ./.env:/app/.env:ro
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Usage:**
- Run CLI: `docker-compose run --rm msa-extractor-cli`
- Run API: `docker-compose up msa-extractor-api`
- Access API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### .dockerignore

Create `.dockerignore`:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
results/
logs/
uploads/
storage/
*.db
scratch/
.env.local

# Git
.git/
.gitignore

# Documentation (optional - include if you want docs in image)
# docs/

# Tests
tests/
.pytest_cache/
```

### Building and Running

```bash
# Build Docker image
docker build -t msa-extractor .

# Run single file extraction
docker run --rm \
  -v $(pwd)/contracts:/app/contracts:ro \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/.env:/app/.env:ro \
  msa-extractor \
  python main.py --file /app/contracts/example.pdf --out /app/results/example.json

# Or use docker-compose
docker-compose up
```

### Docker with Environment Variables

```bash
# Run with environment variables (no .env file needed)
docker run --rm \
  -e GEMINI_API_KEY=your_key_here \
  -e GEMINI_TEXT_MODEL=gemini-2.5-pro \
  -e GEMINI_VISION_MODEL=gemini-2.5-pro \
  -v $(pwd)/contracts:/app/contracts:ro \
  -v $(pwd)/results:/app/results \
  msa-extractor \
  python main.py --file /app/contracts/example.pdf
```

## Cross-Platform Configuration

### Path Handling

The system uses `pathlib.Path` for all file paths, which automatically handles:
- Windows: `C:\Users\...`
- Linux: `/home/user/...`
- Docker: `/app/...`

### Tesseract Configuration

Tesseract paths are configured via environment variables, making them cross-platform:

**Windows:**
```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata
```

**Linux:**
```env
TESSERACT_CMD=/usr/bin/tesseract  # Usually in PATH, can omit
TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata  # Usually default, can omit
```

**Docker:**
```env
# Usually in PATH, no configuration needed
# TESSERACT_CMD=/usr/bin/tesseract
# TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
```

### Environment Variables

All configuration is done via environment variables (or `.env` file), making it:
- ✅ Cross-platform compatible
- ✅ Docker-friendly
- ✅ CI/CD ready
- ✅ No hardcoded paths

## Platform-Specific Notes

### Linux

- Tesseract is usually installed via package manager
- Default paths are standard (`/usr/bin/tesseract`, `/usr/share/tesseract-ocr/`)
- Usually no need to set `TESSERACT_CMD` or `TESSDATA_PREFIX`
- OpenCV dependencies may require additional system packages

### Docker

- Use official Python base images (e.g., `python:3.10-slim`)
- Install Tesseract via `apt-get` in Dockerfile
- Mount volumes for input/output directories
- Use environment variables or `.env` file for configuration
- Consider multi-stage builds for smaller images

### Windows

- See [Windows OCR Setup](windows_ocr_setup.md) for detailed instructions
- May need to set `TESSERACT_CMD` if not in PATH
- Visual C++ Redistributable required for some dependencies

## Troubleshooting

### Issue: Tesseract not found on Linux

**Solution:**
```bash
# Check if installed
which tesseract

# Install if missing
sudo apt install tesseract-ocr  # Ubuntu/Debian
sudo dnf install tesseract      # Fedora/CentOS
```

### Issue: Tesseract not found in Docker

**Solution:**
- Ensure Tesseract is installed in Dockerfile
- Check if `TESSERACT_CMD` is set correctly
- Verify PATH includes Tesseract location

### Issue: OpenCV errors on Linux

**Solution:**
```bash
# Install OpenCV system dependencies
sudo apt install libopencv-dev python3-opencv  # Ubuntu/Debian
```

### Issue: Permission errors in Docker

**Solution:**
- Ensure volumes are mounted with correct permissions
- Use `--user` flag if running as non-root
- Check file ownership in mounted directories

## Best Practices

1. **Use `.env` files** for local development
2. **Use environment variables** in Docker/CI/CD
3. **Don't hardcode paths** - use environment variables
4. **Test on target platform** before deploying
5. **Use Docker** for consistent environments
6. **Document platform-specific requirements** in setup guides

## Migration from Windows to Linux

1. **Install system dependencies** (Tesseract, OpenCV)
2. **Update `.env` file** - remove Windows-specific paths
3. **Test Tesseract** - verify it's in PATH
4. **Update paths** - use forward slashes or pathlib
5. **Test extraction** - verify everything works

## Next Steps

- See [Windows OCR Setup](windows_ocr_setup.md) for Windows-specific instructions
- See [Configuration Reference](configuration.md) for all environment variables
- See [README.md](../README.md) for general usage instructions

