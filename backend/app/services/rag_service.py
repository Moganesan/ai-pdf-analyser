import os
import uuid
import traceback
import json
from typing import List, Dict, Any
from datetime import datetime

from app.core.config import settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from pypdf import PdfReader
import requests

class FixedRAGService:
    def __init__(self):
        # Initialize common attributes
        self.embeddings = None
        self.llm = None
        self.vectorstore = None
        self.retriever = None
        self.rag_chain = None
        self.initialization_error = None
        
        try:
            print(f"Initializing RAG service with Ollama URL: {settings.ollama_base_url}")
            print(f"Using embedding model: {settings.ollama_embedding_model}")
            print(f"Using LLM model: {settings.ollama_model}")
            
            # Check Ollama availability before initializing
            try:
                health_url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
                resp = requests.get(health_url, timeout=settings.ollama_health_timeout_seconds)
                if resp.status_code != 200:
                    raise RuntimeError(f"Ollama health check failed with status {resp.status_code}")
            except Exception as health_err:
                raise RuntimeError(f"Ollama is not reachable at {settings.ollama_base_url}: {health_err}")

            # Initialize embeddings with your specific model
            self.embeddings = OllamaEmbeddings(
                base_url=settings.ollama_base_url,
                model=settings.ollama_embedding_model  # nomic-embed-text:latest
            )
            print("Embeddings initialized successfully")
            
            # Initialize LLM with your specific model
            self.llm = Ollama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model  # gemma3:4b
            )
            print("LLM initialized successfully")
            
            self._initialize_vectorstore()
            self._setup_rag_chain()
            print("RAG service initialized successfully")
            
        except Exception as e:
            print(f"Error initializing RAG service: {e}")
            self.initialization_error = f"Failed to initialize RAG service: {e}"

    def _ensure_ready(self):
        if self.initialization_error:
            raise RuntimeError(self.initialization_error)
        if not self.embeddings or not self.llm:
            raise RuntimeError("LLM or embeddings are not initialized.")
        if not self.vectorstore or not self.retriever:
            raise RuntimeError("Vector store or retriever is not initialized.")
        if not self.rag_chain:
            raise RuntimeError("RAG chain is not initialized.")

    

    def _initialize_vectorstore(self):
        """Initialize ChromaDB vector store"""
        try:
            self.vectorstore = Chroma(
                persist_directory=settings.chroma_persist_directory,
                embedding_function=self.embeddings
            )
            self.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": settings.retrieval_k}
            )
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            self.vectorstore = None
            self.retriever = None

    def _setup_rag_chain(self):
        """Setup the RAG chain with prompt template"""
        try:
            template = """Answer the question based only on the following context:
            {context}

            Question: {input}
            
            Please provide a comprehensive answer based on the context. If the context doesn't contain enough information to answer the question, please say so and suggest what additional information might be helpful.
            """
            
            prompt = ChatPromptTemplate.from_template(template)
            question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
            self.rag_chain = create_retrieval_chain(self.retriever, question_answer_chain)
        except Exception as e:
            print(f"Error setting up RAG chain: {e}")
            self.rag_chain = None

    async def process_document(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """Process a PDF document and add it to the vector store"""
        try:
            print(f"Processing document: {file_path} with ID: {document_id}")
            self._ensure_ready()
            
            # Load PDF and extract text using pypdf (to avoid loader import issues on Windows)
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                full_text = "".join([(page.extract_text() or "") for page in reader.pages])

            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )
            chunks = text_splitter.split_text(full_text)
            
            # Prepare metadata and add to vector store
            metadatas = [
                {"document_id": document_id, "chunk_index": i, "source": file_path}
                for i in range(len(chunks))
            ]
            self.vectorstore.add_texts(chunks, metadatas=metadatas)
            
            # Update retriever and RAG chain
            self._initialize_vectorstore()
            self._setup_rag_chain()
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks": len(chunks),
                "text": "\n".join(chunks)
            }
            
        except Exception as e:
            print(f"Error processing document: {e}")
            raise

    

    async def query_documents(self, question: str, document_ids: List[str] = None) -> Dict[str, Any]:
        """Query documents using RAG"""
        try:
            self._ensure_ready()
            
            # Get response from RAG chain
            response = self.rag_chain.invoke({"input": question})
            
            # Extract sources
            sources = []
            if "context" in response:
                for doc in response["context"]:
                    sources.append({
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    })
            
            return {
                "success": True,
                "response": response["answer"],
                "sources": sources
            }
            
        except Exception as e:
            print(f"Error querying documents: {e}")
            raise

    async def query_documents_stream(self, question: str, document_ids: List[str] = None) -> Dict[str, Any]:
        """Query documents using RAG with streaming response"""
        try:
            self._ensure_ready()
            
            # Get streaming response from RAG chain
            response_stream = self.rag_chain.astream({"input": question})
            
            # Extract sources from the first chunk
            sources = []
            full_response = ""
            
            async def stream_generator():
                nonlocal sources, full_response
                async for chunk in response_stream:
                    if "answer" in chunk:
                        content = chunk["answer"]
                        full_response += content
                        yield content
                    
                    # Extract sources from context
                    if "context" in chunk and not sources:
                        for doc in chunk["context"]:
                            sources.append({
                                "content": doc.page_content[:200] + "...",
                                "metadata": doc.metadata
                            })
            
            return {
                "success": True,
                "stream": stream_generator(),
                "sources": sources
            }
            
        except Exception as e:
            print(f"Error querying documents with stream: {e}")
            raise
    

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a document from the vector store"""
        try:
            self._ensure_ready()
            # Chroma delete by metadata is non-trivial; not implemented here
            return {
                "success": True,
                "message": f"Document {document_id} deletion requested (not implemented)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_document_count(self) -> int:
        """Get the number of documents in the vector store"""
        try:
            # Not directly supported via Chroma wrapper here; return 0
            return 0
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0

# Global RAG service instance
rag_service = FixedRAGService()
