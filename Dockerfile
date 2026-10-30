# IMAIRA FairScore — Production Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (build-essential, git, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Run pre-flight checks
RUN python check_setup.py

# Expose server port
EXPOSE 8002

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8002
ENV PYTHONUNBUFFERED=1

# Command to start the platform
CMD ["python", "-m", "api.main"]
