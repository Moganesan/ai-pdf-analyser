# Use a base image that has prebuilt wheels for most libraries
FROM python:3.11-bookworm

# Avoid writing .pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install required system dependencies (Rust not needed if we prefer binary wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker cache efficiency)
COPY requirements.txt .

# Upgrade pip and ensure wheel + setuptools are ready
RUN pip install --upgrade pip setuptools wheel

# Force pip to prefer binary wheels instead of building from source
RUN pip install --prefer-binary --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose port for Render
ENV PORT=8000
EXPOSE 8000

# Default start command (Render expects CMD)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
