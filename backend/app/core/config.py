from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    api_title: str = "AI PDF Analyzer Backend"
    api_version: str = "1.0.0"
    
    # Ollama Settings
    ollama_base_url: str = "http://192.168.31.101:11434"
    ollama_model: str = "gemma3:4b"
    ollama_embedding_model: str = "nomic-embed-text:latest"
    ollama_health_timeout_seconds: int = 3
    
    # Vector Store Settings
    chroma_persist_directory: str = "./chroma_db"
    
    # File Upload Settings
    upload_directory: str = "./uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 4

    # Notifications
    telegram_bot_token: Optional[str] = "8329594028:AAEpT2LJMnnHMVwvF-qABvGkll5EJNF7Erk"
    telegram_chat_id: Optional[str] = "1005787823"
    
    class Config:
        env_file = ".env"

settings = Settings()
