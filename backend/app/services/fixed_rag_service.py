import os
import uuid
import traceback
import json
from typing import List, Dict, Any
from datetime import datetime

# Import with error handling to avoid dependency conflicts
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain_community.llms import Ollama
    from langchain_core.prompts import ChatPromptTemplate
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"Warning: LangChain import failed: {e}")
    LANGCHAIN_AVAILABLE = False

from app.core.config import settings

class FixedRAGService:
    def __init__(self):
        # Initialize common attributes first
        self.documents = []  # Simple in-memory storage (always available)
        self.documents_db_file = "./rag_documents_db.json"
        self.embeddings = None
        self.llm = None
        self.vectorstore = None
        self.retriever = None
        self.rag_chain = None
        
        # Load existing documents from persistent storage
        self._load_documents_from_storage()
        
        if not LANGCHAIN_AVAILABLE:
            print("LangChain not available, using fallback mode")
            self._setup_fallback()
            return
            
        try:
            print(f"Initializing RAG service with Ollama URL: {settings.ollama_base_url}")
            print(f"Using embedding model: {settings.ollama_embedding_model}")
            print(f"Using LLM model: {settings.ollama_model}")
            
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
            print(f"Falling back to simple mode")
            self._setup_fallback()

    def _load_documents_from_storage(self):
        """Load documents from persistent storage"""
        try:
            if os.path.exists(self.documents_db_file):
                with open(self.documents_db_file, 'r') as f:
                    data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    for doc in data:
                        if 'processed_at' in doc:
                            doc['processed_at'] = datetime.fromisoformat(doc['processed_at'])
                    self.documents = data
                    print(f"Loaded {len(self.documents)} documents from persistent storage")
            else:
                print("No existing documents found in persistent storage")
        except Exception as e:
            print(f"Error loading documents from storage: {e}")
            self.documents = []

    def _save_documents_to_storage(self):
        """Save documents to persistent storage"""
        try:
            # Convert datetime objects to strings for JSON serialization
            data_to_save = []
            for doc in self.documents:
                doc_copy = doc.copy()
                if 'processed_at' in doc_copy:
                    doc_copy['processed_at'] = doc_copy['processed_at'].isoformat()
                data_to_save.append(doc_copy)
            
            with open(self.documents_db_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            print(f"Saved {len(self.documents)} documents to persistent storage")
        except Exception as e:
            print(f"Error saving documents to storage: {e}")

    def _setup_fallback(self):
        """Fallback mode when LangChain is not available"""
        self.embeddings = None
        self.llm = None
        self.vectorstore = None
        self.retriever = None
        self.rag_chain = None
        self.documents = []  # Simple in-memory storage

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

            Question: {question}
            
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
            print(f"LangChain available: {LANGCHAIN_AVAILABLE}")
            print(f"Vectorstore available: {self.vectorstore is not None}")
            print(f"Documents list available: {hasattr(self, 'documents')}")
            
            # Check if document already exists
            for existing_doc in self.documents:
                if existing_doc.get('id') == document_id:
                    print(f"Document {document_id} already processed, returning existing data")
                    return {
                        "success": True,
                        "document_id": document_id,
                        "chunks": 1,
                        "text": existing_doc.get('content', '')
                    }
            
            if not LANGCHAIN_AVAILABLE or not self.vectorstore:
                print("Using fallback processing")
                return await self._fallback_process_document(file_path, document_id)
            
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
            print(f"Error processing document: {e}")
            return await self._fallback_process_document(file_path, document_id)

    async def _fallback_process_document(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """Fallback document processing"""
        try:
            print(f"Fallback processing document: {file_path}")
            print(f"Documents list exists: {hasattr(self, 'documents')}")
            print(f"Documents list type: {type(self.documents) if hasattr(self, 'documents') else 'None'}")
            
            # Check if document already exists in fallback storage
            for existing_doc in self.documents:
                if existing_doc.get('id') == document_id:
                    # Check if the existing content is a placeholder
                    content = existing_doc.get('content', '')
                    if 'PDF text extraction not available' in content:
                        print(f"Document {document_id} exists but has placeholder content, reprocessing...")
                        break  # Continue to reprocess
                    else:
                        print(f"Document {document_id} already exists in fallback storage with valid content")
                        return {
                            "success": True,
                            "document_id": document_id,
                            "chunks": 1,
                            "text": content
                        }
            
            # ACTUAL PDF text extraction - only store valid content
            text = ""
            extraction_successful = False
            
            try:
                # Try to use PyMuPDF for text extraction (better quality)
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                for page in doc:
                    text += page.get_text()
                doc.close()
                print(f"Successfully extracted text using PyMuPDF")
                extraction_successful = True
            except ImportError:
                print(f"PyMuPDF not available, trying PyPDF2...")
                try:
                    # Fallback to PyPDF2
                    import PyPDF2
                    with open(file_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        for page in reader.pages:
                            text += page.extract_text()
                    print(f"Successfully extracted text using PyPDF2")
                    extraction_successful = True
                except ImportError:
                    print(f"PyPDF2 not available either")
                    print(f"PDF extraction libraries not available")
            except Exception as e:
                print(f"Error extracting PDF text with PyMuPDF: {e}")
                # Try PyPDF2 as fallback
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        for page in reader.pages:
                            text += page.extract_text()
                    print(f"Successfully extracted text using PyPDF2 (fallback)")
                    extraction_successful = True
                except Exception as e2:
                    print(f"Error extracting PDF text with PyPDF2: {e2}")
                    print(f"All PDF extraction methods failed")
            
            # Only proceed if we successfully extracted text
            if not extraction_successful or not text.strip():
                print(f"Failed to extract text from PDF: {file_path}")
                print(f"Extraction successful: {extraction_successful}")
                print(f"Text length: {len(text)}")
                print(f"Text preview: {text[:200]}")
                return {
                    "success": False,
                    "error": f"Failed to extract text from PDF. Extraction successful: {extraction_successful}, Text length: {len(text)}. Please ensure the PDF contains readable text and is not an image-based PDF."
                }
            
            print(f"Extracted text length: {len(text)}")
            
            # Check if document already exists and update it, otherwise add new
            doc_data = {
                "id": document_id,
                "file_path": file_path,
                "content": text,
                "processed_at": datetime.now()
            }
            
            # Find existing document with same ID
            existing_index = None
            for i, existing_doc in enumerate(self.documents):
                if existing_doc.get('id') == document_id:
                    existing_index = i
                    break
            
            if existing_index is not None:
                print(f"Updating existing document at index {existing_index}")
                self.documents[existing_index] = doc_data
            else:
                print(f"Adding new document to list. Current count: {len(self.documents)}")
                self.documents.append(doc_data)
                print(f"Document added. New count: {len(self.documents)}")
            
            # Save to persistent storage
            self._save_documents_to_storage()
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks": 1,
                "text": text
            }
        except Exception as e:
            print(f"Error in fallback processing: {e}")
            print(f"Fallback error traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e)
            }

    async def query_documents(self, question: str, document_ids: List[str] = None) -> Dict[str, Any]:
        """Query documents using RAG"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.rag_chain:
                return await self._fallback_query(question, document_ids)
            
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
            return await self._fallback_query(question, document_ids)

    async def query_documents_stream(self, question: str, document_ids: List[str] = None) -> Dict[str, Any]:
        """Query documents using RAG with streaming response"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.rag_chain:
                return await self._fallback_query_stream(question, document_ids)
            
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
            return await self._fallback_query_stream(question, document_ids)

    async def _fallback_query(self, question: str, document_ids: List[str] = None) -> Dict[str, Any]:
        """Fallback query method"""
        try:
            # Simple response using Ollama directly
            import requests
            
            # Create context from stored documents
            context = ""
            for doc in self.documents:
                if document_ids and doc["id"] not in document_ids:
                    continue
                context += doc["content"] + "\n\n"
            
            # Create prompt
            prompt = f"""Answer the question based on the following context:

Context:
{context}

Question: {question}

Please provide a comprehensive answer based on the context. If the context doesn't contain enough information to answer the question, please say so and suggest what additional information might be helpful.

Answer:"""

            # Call Ollama directly
            response = requests.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("response", "Sorry, I couldn't generate a response."),
                    "sources": [{"content": doc["content"][:200] + "...", "metadata": {"id": doc["id"]}} for doc in self.documents]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to connect to Ollama"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _fallback_query_stream(self, question: str, document_ids: List[str] = None) -> Dict[str, Any]:
        """Fallback streaming query method"""
        try:
            # Simple streaming response using Ollama directly
            import requests
            import json
            
            # Create context from stored documents
            context = ""
            for doc in self.documents:
                if document_ids and doc["id"] not in document_ids:
                    continue
                context += doc["content"] + "\n\n"
            
            # Create prompt
            prompt = f"""Answer the question based on the following context:

Context:
{context}

Question: {question}

Please provide a comprehensive answer based on the context. If the context doesn't contain enough information to answer the question, please say so and suggest what additional information might be helpful.

Answer:"""

            # Call Ollama with streaming
            response = requests.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                async def stream_generator():
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if 'response' in data:
                                    yield data['response']
                            except json.JSONDecodeError:
                                continue
                
                return {
                    "success": True,
                    "stream": stream_generator(),
                    "sources": [{"content": doc["content"][:200] + "...", "metadata": {"id": doc["id"]}} for doc in self.documents]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to connect to Ollama"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a document from the vector store"""
        try:
            if LANGCHAIN_AVAILABLE and self.vectorstore:
                # Note: ChromaDB doesn't have a direct delete by metadata
                # This would require rebuilding the vector store
                pass
            
            # Remove from fallback storage
            self.documents = [doc for doc in self.documents if doc["id"] != document_id]
            
            # Save to persistent storage
            self._save_documents_to_storage()
            
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
            print(f"Getting document count. Documents list exists: {hasattr(self, 'documents')}")
            if hasattr(self, 'documents'):
                count = len(self.documents)
                print(f"Document count: {count}")
                return count
            else:
                print("Documents list not found, returning 0")
                return 0
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0

# Global RAG service instance
rag_service = FixedRAGService()
