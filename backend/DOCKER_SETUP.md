# Docker Setup for AI PDF Analyzer Backend

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Ubuntu 24.04 LTS

## Quick Start

### 1. Build and Run with Docker Compose

```bash
cd backend

# Create environment file
cp .env.example .env
# Edit .env with your Ollama URL

# Initialize empty database
echo '{}' > documents_db.json

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### 2. Build and Run with Docker Only

```bash
cd backend

# Build image
docker build -t ai-pdf-analyzer-backend .

# Run container
docker run -d \
  --name ai-pdf-backend \
  -p 8000:8000 \
  -e OLLAMA_BASE_URL=http://192.168.31.101:11434 \
  -e UVICORN_RELOAD=false \
  -v $(pwd)/chroma_db:/app/chroma_db \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/documents_db.json:/app/documents_db.json \
  ai-pdf-analyzer-backend

# View logs
docker logs -f ai-pdf-backend

# Stop and remove
docker stop ai-pdf-backend
docker rm ai-pdf-backend
```

## Environment Variables

| Variable               | Default                     | Description                   |
| ---------------------- | --------------------------- | ----------------------------- |
| OLLAMA_BASE_URL        | http://192.168.31.101:11434 | Ollama server URL             |
| OLLAMA_MODEL           | gemma3:4b                   | LLM model name                |
| OLLAMA_EMBEDDING_MODEL | nomic-embed-text:latest     | Embedding model               |
| UVICORN_RELOAD         | false                       | Enable auto-reload (dev only) |
| TELEGRAM_BOT_TOKEN     | -                           | Optional Telegram bot token   |
| TELEGRAM_CHAT_ID       | -                           | Optional Telegram chat ID     |

## Troubleshooting

### Permissions Issues

```bash
# Fix volume permissions
sudo chown -R 1000:1000 chroma_db uploads
chmod 755 chroma_db uploads
```

### View Container Logs

```bash
docker-compose logs -f backend
```

### Rebuild After Code Changes

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Access Container Shell

```bash
docker-compose exec backend bash
```

## Production Deployment on EC2

```bash
# SSH to EC2
ssh ubuntu@your-ec2-ip

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
newgrp docker

# Clone/copy your code
cd /var/www/ai-pdf-analyser/backend

# Setup environment
cp .env.example .env
vim .env  # Configure your Ollama URL

# Initialize database
echo '{}' > documents_db.json

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

## Health Check

The container includes a health check endpoint:

```bash
curl http://localhost:8000/api/health
```

## Stopping and Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Clean up images
docker system prune -a
```
