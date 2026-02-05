"""
Embedding models for vector representation
"""
from typing import List, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

from backend.config import get_settings

settings = get_settings()


class EmbeddingManager:
    """Manage embedding models for text vectorization"""
    
    _instance: Optional['EmbeddingManager'] = None
    _embeddings = None
    
    def __new__(cls):
        """Singleton pattern to reuse embedding model"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_embeddings(self):
        """
        Get the embedding model instance.
        
        Uses HuggingFace sentence-transformers by default (free, local).
        Can be configured to use OpenAI embeddings if needed.
        """
        if self._embeddings is None:
            self._embeddings = self._create_embeddings()
        return self._embeddings
    
    def _create_embeddings(self):
        """Create the embedding model based on configuration"""
        model_name = settings.embedding_model
        
        # Use HuggingFace embeddings (local, free)
        # Good multilingual model for Chinese + English content
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if GPU available
            encode_kwargs={
                'normalize_embeddings': True,  # For cosine similarity
                'batch_size': 32
            }
        )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.get_embeddings()
        return embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector
        """
        embeddings = self.get_embeddings()
        return embeddings.embed_query(text)


def get_embedding_model():
    """Get the singleton embedding manager"""
    return EmbeddingManager()


def get_embeddings_for_langchain():
    """Get embeddings object for use with LangChain"""
    return EmbeddingManager().get_embeddings()
