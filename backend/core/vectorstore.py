"""
ChromaDB vector store management
"""
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.config import get_settings
from backend.core.embeddings import get_embeddings_for_langchain

settings = get_settings()


class VectorStoreManager:
    """Manage ChromaDB vector store operations"""
    
    _instance: Optional['VectorStoreManager'] = None
    _client = None
    _collection = None
    _langchain_store = None
    
    COLLECTION_NAME = "ai_tutor_knowledge"
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._init_client()
    
    def _init_client(self):
        """Initialize ChromaDB client with persistence"""
        persist_dir = settings.chroma_persist_dir
        
        # Ensure directory exists
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize persistent client
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )
        
        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "AI Tutor course knowledge base"}
        )
    
    def get_langchain_store(self) -> Chroma:
        """Get LangChain-compatible Chroma store"""
        if self._langchain_store is None:
            self._langchain_store = Chroma(
                client=self._client,
                collection_name=self.COLLECTION_NAME,
                embedding_function=get_embeddings_for_langchain()
            )
        return self._langchain_store
    
    def add_documents(
        self,
        chunks: List[Dict],
        document_id: str
    ) -> int:
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of chunk dicts with 'content' and 'metadata'
            document_id: Unique identifier for the source document
            
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        # Prepare documents for LangChain
        documents = []
        for i, chunk in enumerate(chunks):
            metadata = chunk.get("metadata", {})
            metadata["document_id"] = document_id
            metadata["chunk_id"] = f"{document_id}_{i}"
            metadata["added_at"] = datetime.now().isoformat()
            
            doc = Document(
                page_content=chunk["content"],
                metadata=metadata
            )
            documents.append(doc)
        
        # Add to vector store
        store = self.get_langchain_store()
        store.add_documents(documents)
        
        return len(documents)
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of search results with content and metadata
        """
        store = self.get_langchain_store()
        
        # Perform similarity search with scores
        if filter_dict:
            results = store.similarity_search_with_score(
                query, k=k, filter=filter_dict
            )
        else:
            results = store.similarity_search_with_score(query, k=k)
        
        # Format results
        formatted = []
        for doc, score in results:
            formatted.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": 1 - score  # Convert distance to similarity
            })
        
        return formatted
    
    def search_with_sources(
        self,
        query: str,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Search and return results grouped by source.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            Dict with 'results' and 'sources' summary
        """
        results = self.search(query, k)
        
        # Group by source
        sources = {}
        for r in results:
            source = r["metadata"].get("source", "Unknown")
            page = r["metadata"].get("page", "N/A")
            key = f"{source} (第{page}页)"
            
            if key not in sources:
                sources[key] = {
                    "source": source,
                    "page": page,
                    "chunks": []
                }
            sources[key]["chunks"].append(r["content"][:200] + "...")
        
        return {
            "results": results,
            "sources": list(sources.values())
        }
    
    def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Number of chunks deleted
        """
        # Get chunks with this document_id
        results = self._collection.get(
            where={"document_id": document_id}
        )
        
        if results and results["ids"]:
            self._collection.delete(ids=results["ids"])
            return len(results["ids"])
        
        return 0
    
    def get_stats(self) -> Dict:
        """Get vector store statistics"""
        count = self._collection.count()
        
        # Get unique documents
        results = self._collection.get(include=["metadatas"])
        doc_ids = set()
        if results and results["metadatas"]:
            for meta in results["metadatas"]:
                if meta and "document_id" in meta:
                    doc_ids.add(meta["document_id"])
        
        return {
            "total_chunks": count,
            "total_documents": len(doc_ids),
            "collection_name": self.COLLECTION_NAME
        }
    
    def list_documents(self) -> List[Dict]:
        """List all documents in the store"""
        results = self._collection.get(include=["metadatas"])
        
        documents = {}
        if results and results["metadatas"]:
            for meta in results["metadatas"]:
                if meta and "document_id" in meta:
                    doc_id = meta["document_id"]
                    if doc_id not in documents:
                        documents[doc_id] = {
                            "id": doc_id,
                            "source": meta.get("source", "Unknown"),
                            "chunk_count": 0,
                            "added_at": meta.get("added_at", "Unknown")
                        }
                    documents[doc_id]["chunk_count"] += 1
        
        return list(documents.values())


def get_vector_store() -> VectorStoreManager:
    """Get the singleton vector store manager"""
    return VectorStoreManager()
