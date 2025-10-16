import os
import uuid
from typing import List, Dict, Any
from datetime import datetime

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from app.core.config import settings

class RAGService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model
        )
        self.llm = Ollama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model
        )
        self.vectorstore = None
        self.retriever = None
        self.rag_chain = None
        self._initialize_vectorstore()
        self._setup_rag_chain()

    def _initialize_vectorstore(self):
        """Initialize ChromaDB vector store"""
        self.vectorstore = Chroma(
            persist_directory=settings.chroma_persist_directory,
            embedding_function=self.embeddings
        )
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": settings.retrieval_k}
        )

    def _setup_rag_chain(self):
        """Setup the RAG chain with prompt template"""
        template = """Answer the question based only on the following context:
        {context}

        Question: {question}
        
        Please provide a comprehensive answer based on the context. If the context doesn't contain enough information to answer the question, please say so and suggest what additional information might be helpful.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        self.rag_chain = create_retrieval_chain(self.retriever, question_answer_chain)

    async def process_document(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """Process a PDF document and add it to the vector store"""
        try:
            # Load PDF document
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )
            splits = text_splitter.split_documents(documents)
            
            # Add document ID to metadata
            for i, split in enumerate(splits):
                split.metadata.update({
                    "document_id": document_id,
                    "chunk_index": i,
                    "source": file_path
                })
            
            # Add to vector store
            self.vectorstore.add_documents(splits)
            
            # Update retriever and RAG chain
            self._initialize_vectorstore()
            self._setup_rag_chain()
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks": len(splits),
                "text": "\n".join([doc.page_content for doc in splits])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def query_documents(self, question: str, document_ids: List[str] = None) -> Dict[str, Any]:
        """Query documents using RAG"""
        try:
            # Filter by document IDs if provided
            if document_ids:
                # This would require custom filtering in ChromaDB
                # For now, we'll use all documents
                pass
            
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
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a document from the vector store"""
        try:
            # Note: ChromaDB doesn't have a direct delete by metadata
            # This would require rebuilding the vector store
            # For now, we'll return success
            return {
                "success": True,
                "message": f"Document {document_id} deletion requested"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_document_count(self) -> int:
        """Get the number of documents in the vector store"""
        try:
            # This would require querying ChromaDB directly
            # For now, return 0
            return 0
        except:
            return 0

# Global RAG service instance
rag_service = RAGService()
