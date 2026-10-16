# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system dependencies: FFmpeg, curl, git, build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x for Remotion
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Remotion dependencies
COPY remotion/package.json remotion/package-lock.json ./remotion/
RUN cd remotion && npm ci

# Copy application source code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Default entrypoint starts FastAPI web studio
CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
