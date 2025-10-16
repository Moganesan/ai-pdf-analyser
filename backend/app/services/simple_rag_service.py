import os
import uuid
import requests
from typing import List, Dict, Any
from datetime import datetime

from app.core.config import settings

class SimpleRAGService:
    def __init__(self):
        self.ollama_base_url = settings.ollama_base_url
        self.ollama_model = settings.ollama_model
        self.embedding_model = settings.ollama_embedding_model
        self.documents = []  # Simple in-memory storage
        self.embeddings = []  # Simple in-memory embeddings

    async def process_document(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """Process a PDF document and extract text"""
        try:
            # For now, we'll use a simple text extraction
            # In a real implementation, you'd use PyPDF or similar
            with open(file_path, 'rb') as file:
                # Simple text extraction - in production, use proper PDF library
                text = f"Document content from {file_path}"
            
            # Split into chunks
            chunks = self._split_text(text, settings.chunk_size, settings.chunk_overlap)
            
            # Create embeddings for each chunk
            chunk_embeddings = []
            for chunk in chunks:
                embedding = await self._get_embedding(chunk)
                chunk_embeddings.append(embedding)
            
            # Store document
            doc_data = {
                "id": document_id,
                "file_path": file_path,
                "chunks": chunks,
                "embeddings": chunk_embeddings,
                "processed_at": datetime.now()
            }
            
            self.documents.append(doc_data)
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks": len(chunks),
                "text": text
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def query_documents(self, question: str, document_ids: List[str] = None) -> Dict[str, Any]:
        """Query documents using simple similarity search"""
        try:
            # Get embedding for the question
            question_embedding = await self._get_embedding(question)
            
            # Find most similar chunks
            similarities = []
            for doc in self.documents:
                if document_ids and doc["id"] not in document_ids:
                    continue
                    
                for i, chunk_embedding in enumerate(doc["embeddings"]):
                    similarity = self._cosine_similarity(question_embedding, chunk_embedding)
                    similarities.append({
                        "doc_id": doc["id"],
                        "chunk_index": i,
                        "content": doc["chunks"][i],
                        "similarity": similarity
                    })
            
            # Sort by similarity and get top results
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            top_results = similarities[:settings.retrieval_k]
            
            # Create context from top results
            context = "\n\n".join([result["content"] for result in top_results])
            
            # Generate response using Ollama
            response = await self._generate_response(question, context)
            
            return {
                "success": True,
                "response": response,
                "sources": [{"content": result["content"][:200] + "...", "similarity": result["similarity"]} for result in top_results]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a document"""
        try:
            self.documents = [doc for doc in self.documents if doc["id"] != document_id]
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_document_count(self) -> int:
        """Get the number of documents"""
        return len(self.documents)

    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            
            # Try to break at sentence boundaries
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size * 0.5:
                    chunk = chunk[:break_point + 1]
                    start = start + break_point + 1 - overlap
                else:
                    start = end - overlap
            else:
                start = end
            
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["embedding"]
            else:
                # Fallback to simple hash-based embedding
                return self._simple_embedding(text)
                
        except Exception:
            # Fallback to simple hash-based embedding
            return self._simple_embedding(text)

    def _simple_embedding(self, text: str) -> List[float]:
        """Simple hash-based embedding fallback"""
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert hash to 384-dimensional vector
        embedding = []
        for i in range(0, len(hash_hex), 2):
            val = int(hash_hex[i:i+2], 16) / 255.0
            embedding.append(val)
        
        # Pad or truncate to 384 dimensions
        while len(embedding) < 384:
            embedding.append(0.0)
        
        return embedding[:384]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)

    async def _generate_response(self, question: str, context: str) -> str:
        """Generate response using Ollama"""
        try:
            prompt = f"""You are a helpful AI assistant. Answer the question based on the provided context.

Context:
{context}

Question: {question}

Please provide a comprehensive answer based on the context. If the context doesn't contain enough information to answer the question, please say so and suggest what additional information might be helpful.

Answer:"""

            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "Sorry, I couldn't generate a response.")
            else:
                return "Sorry, I couldn't connect to the AI model."
                
        except Exception as e:
            return f"Error generating response: {str(e)}"

# Global RAG service instance
rag_service = SimpleRAGService()
