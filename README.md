# AI PDF Analyzer

A comprehensive SaaS application for analyzing PDF documents using AI. Built with a modern microservices architecture featuring a Next.js frontend and FastAPI backend with RAG (Retrieval Augmented Generation) using LangChain and Ollama.

## Features

- **PDF Upload & Processing**: Drag-and-drop interface for uploading PDF documents
- **AI-Powered Analysis**: Chat with AI about your documents using local LLM
- **RAG System**: Retrieval-Augmented Generation for accurate document-based responses
- **Document Management**: View, manage, and delete uploaded documents
- **Modern UI**: Beautiful interface built with shadcn/ui components
- **Microservices Architecture**: Separate frontend and backend services
- **Robust Error Handling**: Graceful fallback when dependencies fail
- **Local LLM Integration**: Uses Ollama with configurable models

## Prerequisites

1. **Node.js** (v18 or higher)
2. **Python 3.8+**
3. **Ollama** installed and running locally
4. **Required Models**:
   - `nomic-embed-text:latest` for embeddings
   - `gemma3:4b` for text generation

## Architecture Overview

### The RAG System:

1. **Document Processing**:
   - PDF text extraction using PyPDFLoader
   - Text chunking with RecursiveCharacterTextSplitter
   - Embedding generation using nomic-embed-text:latest

2. **Vector Storage**:
   - ChromaDB for persistent vector storage
   - Similarity search for document retrieval
   - Metadata tracking for document sources

3. **Response Generation**:
   - Context retrieval from relevant document chunks
   - LLM generation using gemma3:4b
   - Source attribution for responses

## Setup Instructions

### 1. Install Frontend Dependencies

```bash
npm install
```

### 2. Setup Ollama

1. Install Ollama following the [official instructions](https://ollama.ai/)
2. Download the required models:
```bash
# For embeddings
ollama pull nomic-embed-text:latest

# For text generation
ollama pull gemma3:4b
```
3. Start Ollama server:
```bash
ollama serve
```

### 3. Start the Backend

```bash
# Option 1: Use the startup script
./start-backend.sh

# Option 2: Manual setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

The backend will be available at `http://localhost:8000`

**Note**: The backend uses a fixed RAG service that handles dependency conflicts gracefully. If LangChain fails to load, it will automatically fall back to direct Ollama API calls.

### 4. Start the Frontend

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

## Usage

1. **Upload Documents**: Go to the "Upload" tab and drag & drop PDF files
2. **View Documents**: Check the "Documents" tab to see all uploaded files
3. **Chat with AI**: Use the "Chat" tab to ask questions about your documents

## API Endpoints

### Backend (FastAPI)
- `POST /api/documents/upload` - Upload PDF files
- `GET /api/documents/list` - List all documents
- `GET /api/documents/{id}` - Get specific document
- `DELETE /api/documents/{id}` - Delete document
- `POST /api/chat/message` - Send message to RAG system
- `GET /api/chat/history/{session_id}` - Get chat history

### Frontend (Next.js)
- `POST /api/upload` - Upload PDF files (legacy)
- `POST /api/process-pdf` - Extract text from PDFs (legacy)
- `POST /api/add-to-store` - Add documents to vector store (legacy)
- `POST /api/chat` - Chat with AI about documents (legacy)

## Project Structure

```
src/                          # Next.js Frontend
├── app/
│   ├── api/                  # Next.js API routes (legacy)
│   ├── globals.css           # Global styles
│   ├── layout.tsx            # Root layout
│   └── page.tsx              # Main page
├── components/
│   ├── ui/                   # shadcn/ui components
│   ├── chat-interface.tsx    # Chat UI component
│   ├── document-list.tsx     # Document management
│   └── pdf-upload.tsx        # File upload component
└── lib/
    ├── llm.ts                # Local LLM integration
    ├── vector-store.ts       # In-memory vector store
    ├── local-embeddings.ts   # Hash-based embeddings
    └── utils.ts              # Utility functions

backend/                      # FastAPI Backend
├── app/
│   ├── api/
│   │   ├── documents.py      # PDF upload & management
│   │   └── chat.py           # RAG chat endpoints
│   ├── core/
│   │   └── config.py         # Configuration settings
│   ├── models/
│   │   └── document.py       # Pydantic models
│   ├── services/
│   │   ├── rag_service.py    # LangChain RAG implementation
│   │   └── fixed_rag_service.py # Fixed RAG with fallback
│   └── main.py               # FastAPI app
├── requirements.txt          # Python dependencies
├── run.py                    # Startup script
└── README.md                 # Backend documentation
```

## Development

### Backend Development

The backend uses a **dual-mode RAG system**:

1. **Full LangChain Mode** (Primary):
   - Uses `nomic-embed-text:latest` for embeddings
   - Uses `gemma3:4b` for text generation
   - ChromaDB for vector storage
   - Complete RAG pipeline with retrieval and generation

2. **Fallback Mode** (When LangChain fails):
   - Direct Ollama API calls
   - Simple in-memory document storage
   - Maintains same API interface

### Frontend Development

1. **Components**: Add new UI components in `src/components/`
2. **API Integration**: Update API calls in components to use FastAPI backend
3. **Styling**: Use shadcn/ui components for consistent design

### Configuration

#### Backend Configuration (`backend/app/core/config.py`):
```python
# Ollama Settings
ollama_base_url: str = "http://192.168.31.101:11434"
ollama_model: str = "gemma3:4b"
ollama_embedding_model: str = "nomic-embed-text:latest"

# RAG Settings
chunk_size: int = 1000
chunk_overlap: int = 200
vector_store_path: str = "chroma_db"
```

#### Frontend Configuration:
- Update API endpoints in components to point to FastAPI backend
- Modify LLM settings in `src/lib/llm.ts` if using legacy endpoints

## Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy!

### Docker

```bash
# Build the image
docker build -t ai-pdf-analyzer .

# Run the container
docker run -p 3000:3000 ai-pdf-analyzer
```

## Troubleshooting

### Common Issues

1. **Backend Dependency Conflicts**: 
   - The fixed RAG service handles LangChain conflicts automatically
   - If you see import errors, the system will fall back to direct Ollama calls
   - Check that all required models are downloaded: `ollama list`

2. **Ollama Connection Issues**:
   - Ensure Ollama is running: `ollama serve`
   - Verify the base URL in `backend/app/core/config.py`
   - Check that required models are available: `ollama list`

3. **PDF Processing Errors**:
   - Check file size limits and PDF format
   - Ensure sufficient disk space for ChromaDB storage
   - Verify PDF files are not corrupted

4. **Frontend-Backend Communication**:
   - Ensure backend is running on `http://localhost:8000`
   - Check CORS settings if running on different ports
   - Verify API endpoints in frontend components

### Performance Optimization

- **Model Selection**: Use smaller models for faster responses
- **Chunking Strategy**: Adjust `chunk_size` and `chunk_overlap` in config
- **Caching**: Implement document caching for frequently accessed files
- **Vector Store**: Monitor ChromaDB storage size and performance

### Debug Mode

To enable debug logging, set environment variables:
```bash
export PYTHONPATH=$PYTHONPATH:./backend
export DEBUG=true
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.
