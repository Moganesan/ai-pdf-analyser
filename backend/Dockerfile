# Ubuntu 24.04 LTS (Noble) with Python 3.12
FROM ubuntu:24.04

# Avoid interactive prompts and set UTF-8
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Set working directory
WORKDIR /app

# Install Python 3.12 and essential dependencies (including C++ build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    build-essential \
    g++ \
    gcc \
    libc6-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/bin/python3.12 /usr/bin/python3

# Copy requirements first (for Docker cache efficiency)
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip setuptools wheel && \
    /app/venv/bin/pip install --prefer-binary --no-cache-dir -r requirements.txt

# Update PATH to use venv
ENV PATH="/app/venv/bin:$PATH"

# Copy the rest of the app
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/uploads /app/chroma_db && \
    chmod 755 /app/uploads /app/chroma_db

# Expose port
ENV PORT=8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run as non-root user for security
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Start command using venv python
CMD ["/app/venv/bin/python", "run.py"]
