from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Body
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
import logging
import traceback
import json
from datetime import datetime
from typing import List, Dict, Any

from app.models.document import DocumentResponse, DocumentList, DocumentChunk
from app.services.rag_service import rag_service
from app.core.config import settings
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Persistent storage for document metadata
DOCUMENTS_DB_FILE = "./documents_db.json"

@router.post("/notify-dev")
async def notify_dev(message: str = Body(default="Please start the AI server (Ollama) on backend host", embed=True)):
    """Send a Telegram notification to the developer"""
    try:
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            return JSONResponse({
                "success": False,
                "error": "Telegram is not configured on the server"
            }, status_code=500)

        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": settings.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        resp = requests.post(url, json=payload, timeout=10)
        ok = resp.status_code == 200 and resp.json().get("ok")
        return JSONResponse({"success": ok, "status": resp.status_code, "response": resp.json()}, status_code=200 if ok else 500)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

def load_documents_db() -> Dict[str, Any]:
    """Load documents database from file"""
    try:
        with open(DOCUMENTS_DB_FILE, 'r') as f:
            data = json.load(f)
            # Convert datetime strings back to datetime objects
            for doc_id, doc_data in data.items():
                if 'upload_date' in doc_data:
                    doc_data['upload_date'] = datetime.fromisoformat(doc_data['upload_date'])
            return data
    except Exception as e:
        logger.error(f"Error loading documents DB: {e}")
        return {}

def save_documents_db(documents_db: Dict[str, Any]) -> None:
    """Save documents database to file"""
    try:
        # Convert datetime objects to strings for JSON serialization
        data_to_save = {}
        for doc_id, doc_data in documents_db.items():
            data_to_save[doc_id] = doc_data.copy()
            if 'upload_date' in data_to_save[doc_id]:
                data_to_save[doc_id]['upload_date'] = data_to_save[doc_id]['upload_date'].isoformat()
        
        with open(DOCUMENTS_DB_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        logger.info(f"Saved {len(documents_db)} documents to database")
    except Exception as e:
        logger.error(f"Error saving documents DB: {e}")

# Always ensure documents_db.json exists as a file
if not os.path.isfile(DOCUMENTS_DB_FILE):
    logger.error(f"CRITICAL: {DOCUMENTS_DB_FILE} is not a file (likely a directory from Docker mount)")
    logger.error(f"Please delete the directory on host and create an empty file before starting container:")
    logger.error(f"  rm -rf documents_db.json && echo '{{}}' > documents_db.json")
    # Initialize with empty dict instead of crashing
    documents_db = {}
else:
    # Load existing documents on startup
    documents_db = load_documents_db()

logger.info(f"Loaded {len(documents_db)} documents from database")

@router.get("/ollama-status")
async def ollama_status():
    """Check whether Ollama server is reachable"""
    try:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
        resp = requests.get(url, timeout=settings.ollama_health_timeout_seconds)
        ok = resp.status_code == 200
        return JSONResponse({
            "success": ok,
            "status": resp.status_code,
            "reachable": ok
        }, status_code=200 if ok else 503)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "reachable": False,
            "error": str(e)
        }, status_code=503)

@router.post("/upload")
async def upload_document(file: UploadFile = File(..., description="PDF file to upload")):
    """Upload and process a PDF document"""
    document_id = None
    file_path = None
    
    try:
        logger.info(f"Starting document upload for file: {file.filename}")
        logger.info(f"File content type: {file.content_type}")
        logger.info(f"File size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Validate file type
        if not file.filename or not file.filename.endswith('.pdf'):
            logger.error(f"Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        logger.info(f"File size: {file_size} bytes")
        
        # Log file content (first 1000 bytes for debugging)
        content_preview = content[:1000] if len(content) > 1000 else content
        logger.info(f"File content preview (first {len(content_preview)} bytes): {content_preview}")
        
        if file_size > settings.max_file_size:
            logger.error(f"File too large: {file_size} > {settings.max_file_size}")
            raise HTTPException(status_code=400, detail="File too large")
        
        # Check for duplicate documents (same filename and size)
        for existing_id, existing_doc in documents_db.items():
            if (existing_doc.get('filename') == file.filename and 
                existing_doc.get('size') == file_size):
                logger.warning(f"Duplicate document detected: {file.filename} (size: {file_size})")
                return JSONResponse({
                    "success": True,
                    "document_id": existing_id,
                    "filename": file.filename,
                    "size": file_size,
                    "chunks": existing_doc.get('chunks', 0),
                    "message": "Document already exists"
                })
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        logger.info(f"Generated document ID: {document_id}")
        
        # Save file
        try:
            # Resolve upload directory to an absolute path rooted at backend dir
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_dir = settings.upload_directory
            if not os.path.isabs(upload_dir):
                upload_dir = os.path.join(base_dir, upload_dir)

            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"{document_id}.pdf")
            logger.info(f"Saving file to: {file_path}")
            
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            logger.info("File saved successfully")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
        # Process document with RAG
        logger.info("Starting RAG document processing...")
        logger.info(f"File path: {file_path}")
        logger.info(f"File exists: {os.path.exists(file_path)}")
        logger.info(f"File size: {os.path.getsize(file_path) if os.path.exists(file_path) else 'N/A'}")
        
        try:
            result = await rag_service.process_document(file_path, document_id)
            logger.info(f"RAG processing result: {result}")
        except Exception as e:
            logger.error(f"RAG processing failed: {e}")
            logger.error(f"RAG processing traceback: {traceback.format_exc()}")
            # Clean up file if processing failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"RAG processing failed: {str(e)}")
        
        if not result.get("success", False):
            logger.error(f"RAG processing returned failure: {result}")
            # Clean up file if processing failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown RAG processing error"))
        
        # Store document metadata
        try:
            documents_db[document_id] = {
                "id": document_id,
                "filename": file.filename,
                "size": file_size,
                "upload_date": datetime.now(),
                "status": "processed",
                "file_path": file_path,
                "chunks": result.get("chunks", 0)
            }
            # Save to persistent storage
            save_documents_db(documents_db)
            logger.info(f"Document metadata stored for ID: {document_id}")
        except Exception as e:
            logger.error(f"Failed to store document metadata: {e}")
            # Don't fail the upload for metadata storage issues
        
        return JSONResponse({
            "success": True,
            "document_id": document_id,
            "filename": file.filename,
            "size": file_size,
            "chunks": result.get("chunks", 0)
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_document: {e}")
        logger.error(f"Upload error traceback: {traceback.format_exc()}")
        
        # Clean up file if it was created
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup file: {cleanup_error}")
        
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/list")
async def list_documents():
    """List all uploaded documents"""
    try:
        logger.info("Listing documents...")
        documents = []
        
        for doc_id, doc_data in documents_db.items():
            try:
                documents.append(DocumentResponse(
                    id=doc_data["id"],
                    filename=doc_data["filename"],
                    size=doc_data["size"],
                    upload_date=doc_data["upload_date"],
                    status=doc_data["status"],
                    chunks=[],  # Would need to fetch from vector store
                    num_pages=None
                ))
            except Exception as e:
                logger.error(f"Error processing document {doc_id}: {e}")
                # Continue with other documents
                continue
        
        logger.info(f"Found {len(documents)} documents")
        return DocumentList(
            documents=documents,
            total=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Error in list_documents: {e}")
        logger.error(f"List documents traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")
    
@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get a specific document"""
    try:
        logger.info(f"Getting document: {document_id}")
        
        if document_id not in documents_db:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_data = documents_db[document_id]
        logger.info(f"Found document: {doc_data['filename']}")
        
        return DocumentResponse(
            id=doc_data["id"],
            filename=doc_data["filename"],
            size=doc_data["size"],
            upload_date=doc_data["upload_date"],
            status=doc_data["status"],
            chunks=[],
            num_pages=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_document: {e}")
        logger.error(f"Get document traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    try:
        logger.info(f"Deleting document: {document_id}")
        
        if document_id not in documents_db:
            logger.warning(f"Document not found for deletion: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_data = documents_db[document_id]
        logger.info(f"Deleting document: {doc_data['filename']}")
        
        # Delete from RAG service
        try:
            logger.info("Deleting from RAG service...")
            await rag_service.delete_document(document_id)
            logger.info("RAG service deletion completed")
        except Exception as e:
            logger.error(f"Failed to delete from RAG service: {e}")
            # Continue with file deletion even if RAG deletion fails
        
        # Delete file
        try:
            if os.path.exists(doc_data["file_path"]):
                os.remove(doc_data["file_path"])
                logger.info(f"File deleted: {doc_data['file_path']}")
            else:
                logger.warning(f"File not found for deletion: {doc_data['file_path']}")
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            # Continue with database cleanup
        
        # Remove from database
        try:
            del documents_db[document_id]
            # Save to persistent storage
            save_documents_db(documents_db)
            logger.info(f"Document removed from database: {document_id}")
        except Exception as e:
            logger.error(f"Failed to remove from database: {e}")
            raise
        
        return JSONResponse({
            "success": True,
            "message": f"Document {document_id} deleted successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_document: {e}")
        logger.error(f"Delete document traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.get("/")
async def get_document_count():
    """Get the total number of documents"""
    try:
        logger.info("Getting document count...")
        
        try:
            count = await rag_service.get_document_count()
            logger.info(f"RAG service document count: {count}")
        except Exception as e:
            logger.error(f"Failed to get RAG service count: {e}")
            count = 0
        
        total_documents = len(documents_db)
        logger.info(f"Database document count: {total_documents}")
        
        return JSONResponse({
            "count": count,
            "total_documents": total_documents
        })
    except Exception as e:
        logger.error(f"Error in get_document_count: {e}")
        logger.error(f"Get document count traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get document count: {str(e)}")
