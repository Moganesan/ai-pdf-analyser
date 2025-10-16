# AI PDF Analyzer Backend

FastAPI backend service for PDF document analysis with RAG (Retrieval Augmented Generation) using LangChain and Ollama.

## Features

- **PDF Document Processing**: Upload and process PDF documents
- **RAG System**: Retrieval Augmented Generation with LangChain and Ollama
- **Vector Storage**: ChromaDB for document embeddings
- **Chat API**: Query documents with natural language
- **Document Management**: List, view, and delete documents

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **LangChain**: Framework for developing applications with LLMs
- **Ollama**: Local LLM server
- **ChromaDB**: Vector database for embeddings
- **PyPDF**: PDF text extraction

## Prerequisites

1. **Python 3.8+**
2. **Ollama installed and running**
3. **LLM model downloaded** (e.g., `ollama pull llama2`)

## Setup Instructions

### 1. Create and Activate Virtual Environment

```bash
cd backend
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (Git Bash)
source .venv/Scripts/activate
# macOS/Linux
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Setup Ollama

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.ai/

# Pull a model
ollama pull llama2

# Start Ollama server
ollama serve
```

### 4. Configure Environment

Create a `.env` file:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_EMBEDDING_MODEL=llama2
CHROMA_PERSIST_DIRECTORY=./chroma_db
UPLOAD_DIRECTORY=./uploads
MAX_FILE_SIZE=10485760
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_K=4
```

### 5. Run the Backend

```bash
python run.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Documents

- `POST /api/documents/upload` - Upload a PDF document
- `GET /api/documents/list` - List all documents
- `GET /api/documents/{document_id}` - Get specific document
- `DELETE /api/documents/{document_id}` - Delete document

### Chat

- `POST /api/chat/message` - Send a message to the RAG system
- `GET /api/chat/history/{session_id}` - Get chat history
- `POST /api/chat/history/{session_id}` - Save message to history
- `DELETE /api/chat/history/{session_id}` - Clear chat history

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │───▶│  LangChain       │───▶│  Ollama LLM     │
│   Backend       │    │  RAG System      │    │  (Local)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │  ChromaDB      │
         │              │  Vector Store  │
         │              └─────────────────┘
         │
         ▼
┌─────────────────┐
│  PDF Processing │
│  & File Storage │
└─────────────────┘
```

## Development

### Running in Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Deployment

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run.py"]
```

### Production Deployment

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```
