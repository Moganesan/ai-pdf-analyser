from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentChunk(BaseModel):
    content: str
    metadata: Dict[str, Any]
    chunk_index: int

class DocumentUpload(BaseModel):
    filename: str
    size: int
    content_type: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    size: int
    upload_date: datetime
    status: str
    chunks: List[DocumentChunk]
    num_pages: Optional[int] = None

class DocumentList(BaseModel):
    documents: List[DocumentResponse]
    total: int

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str
    document_ids: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    document_ids: List[str]
