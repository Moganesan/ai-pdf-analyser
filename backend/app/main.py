from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from app.api import documents, chat
from app.core.config import settings

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="AI PDF Analyzer Backend",
    description="Backend service for PDF document analysis with RAG",
    version="1.0.0"
)

# Configure CORS from environment
frontend_url = os.getenv("FRONTEND_URL")
frontend_host = os.getenv("FRONTEND_HOST")

allowed_origins = ["*"]
if frontend_url and frontend_url.strip():
    allowed_origins = [frontend_url.strip()]
elif frontend_host and frontend_host.strip():
    # Render web services are HTTPS by default
    allowed_origins = [f"https://{frontend_host.strip()}"]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "AI PDF Analyzer Backend is running!"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload
    )
