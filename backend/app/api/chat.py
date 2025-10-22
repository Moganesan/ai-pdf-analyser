from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional, AsyncGenerator
from datetime import datetime
import json
import requests

from app.models.document import ChatRequest, ChatResponse, ChatMessage
from app.services.rag_service import rag_service
from app.core.config import settings

router = APIRouter()

# In-memory chat history storage
chat_history = {}

@router.post("/message")
async def send_message(request: ChatRequest):
    """Send a message to the RAG system"""
    try:
        # Get response from RAG service
        result = await rag_service.query_documents(
            question=request.message,
            document_ids=request.document_ids
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Create chat response
        response = ChatResponse(
            response=result["response"],
            sources=result["sources"],
            document_ids=request.document_ids or []
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message/stream")
async def send_message_stream(request: ChatRequest):
    """Send a message to the RAG system with streaming response"""
    try:
        # Get streaming response from RAG service
        async def generate_response():
            try:
                # Get response from RAG service
                result = await rag_service.query_documents_stream(
                    question=request.message,
                    document_ids=request.document_ids
                )
                
                if not result["success"]:
                    yield f"data: {json.dumps({'error': result['error']})}\n\n"
                    return
                
                # Stream the response
                async for chunk in result["stream"]:
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                # Send sources and metadata at the end
                yield f"data: {json.dumps({'sources': result.get('sources', []), 'document_ids': request.document_ids or [], 'done': True})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ollama-status")
async def ollama_status():
    """Check whether Ollama server is reachable"""
    try:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
        resp = requests.get(url, timeout=settings.ollama_health_timeout_seconds)
        ok = resp.status_code == 200
        return {"success": ok, "status": resp.status_code, "reachable": ok}
    except Exception as e:
        return {"success": False, "reachable": False, "error": str(e)}

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        if session_id not in chat_history:
            return {"messages": []}
        
        return {"messages": chat_history[session_id]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/history/{session_id}")
async def save_message(session_id: str, message: ChatMessage):
    """Save a message to chat history"""
    try:
        if session_id not in chat_history:
            chat_history[session_id] = []
        
        chat_history[session_id].append(message.dict())
        
        return {"success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    try:
        if session_id in chat_history:
            del chat_history[session_id]
        
        return {"success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def list_sessions():
    """List all chat sessions"""
    try:
        sessions = list(chat_history.keys())
        return {"sessions": sessions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
