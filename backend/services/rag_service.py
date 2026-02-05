"""
RAG (Retrieval-Augmented Generation) service
"""
from typing import List, Dict, Optional, AsyncGenerator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from backend.core.llm import get_chat_llm
from backend.core.vectorstore import get_vector_store
from backend.core.prompts import RAG_SYSTEM_PROMPT


class RAGService:
    """
    RAG service for retrieval-augmented question answering.
    
    Combines vector search with LLM generation to provide
    accurate, source-backed answers.
    """
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.llm = get_chat_llm()
    
    async def query(
        self,
        question: str,
        k: int = 5,
        include_sources: bool = True
    ) -> Dict:
        """
        Answer a question using RAG.
        
        Args:
            question: User's question
            k: Number of context chunks to retrieve
            include_sources: Whether to include source references
            
        Returns:
            Dict with 'answer' and optionally 'sources'
        """
        # Step 1: Retrieve relevant context
        search_results = self.vector_store.search_with_sources(question, k=k)
        context_chunks = search_results["results"]
        
        if not context_chunks:
            # No relevant context found
            return {
                "answer": "抱歉，我在知识库中没有找到与您问题相关的内容。请确保已上传相关的课程资料，或尝试换一种方式提问。",
                "sources": [],
                "has_context": False
            }
        
        # Step 2: Format context
        context = self._format_context(context_chunks)
        
        # Step 3: Generate answer with LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("human", "{question}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        answer = await chain.ainvoke({
            "context": context,
            "question": question
        })
        
        # Step 4: Format response
        result = {
            "answer": answer,
            "has_context": True
        }
        
        if include_sources:
            result["sources"] = self._format_sources(context_chunks)
        
        return result
    
    def query_sync(
        self,
        question: str,
        k: int = 5,
        include_sources: bool = True
    ) -> Dict:
        """Synchronous version of query"""
        # Retrieve context
        search_results = self.vector_store.search_with_sources(question, k=k)
        context_chunks = search_results["results"]
        
        if not context_chunks:
            return {
                "answer": "抱歉，我在知识库中没有找到与您问题相关的内容。请确保已上传相关的课程资料，或尝试换一种方式提问。",
                "sources": [],
                "has_context": False
            }
        
        # Format context and generate
        context = self._format_context(context_chunks)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("human", "{question}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": context,
            "question": question
        })
        
        result = {
            "answer": answer,
            "has_context": True
        }
        
        if include_sources:
            result["sources"] = self._format_sources(context_chunks)
        
        return result
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks into context string"""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            source = chunk["metadata"].get("source", "Unknown")
            page = chunk["metadata"].get("page", "N/A")
            content = chunk["content"]
            
            context_parts.append(
                f"【参考资料 {i}】\n"
                f"来源：{source}，第{page}页\n"
                f"内容：{content}\n"
            )
        
        return "\n".join(context_parts)
    
    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Format source references for response"""
        sources = []
        seen = set()
        
        for chunk in chunks:
            source = chunk["metadata"].get("source", "Unknown")
            page = chunk["metadata"].get("page", "N/A")
            key = f"{source}_{page}"
            
            if key not in seen:
                seen.add(key)
                sources.append({
                    "source": f"《{source}》第{page}页",
                    "content": chunk["content"][:150] + "...",
                    "relevance_score": chunk.get("relevance_score", 0)
                })
        
        return sources
    
    def get_relevant_context(self, question: str, k: int = 5) -> List[Dict]:
        """
        Get relevant context without generating answer.
        
        Useful for debugging or showing retrieved chunks.
        """
        return self.vector_store.search(question, k=k)


class KnowledgeService:
    """
    Service for managing the knowledge base.
    """
    
    def __init__(self):
        self.vector_store = get_vector_store()
    
    def add_document(
        self,
        chunks: List[Dict],
        document_id: str,
        filename: str
    ) -> Dict:
        """
        Add a processed document to the knowledge base.
        
        Args:
            chunks: Document chunks from TextSplitter
            document_id: Unique document identifier
            filename: Original filename
            
        Returns:
            Summary of the operation
        """
        # Add source filename to each chunk's metadata
        for chunk in chunks:
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            chunk["metadata"]["source"] = filename
        
        # Add to vector store
        count = self.vector_store.add_documents(chunks, document_id)
        
        return {
            "document_id": document_id,
            "filename": filename,
            "chunks_added": count,
            "status": "success"
        }
    
    def delete_document(self, document_id: str) -> Dict:
        """Delete a document from the knowledge base"""
        count = self.vector_store.delete_document(document_id)
        
        return {
            "document_id": document_id,
            "chunks_deleted": count,
            "status": "success" if count > 0 else "not_found"
        }
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        return self.vector_store.get_stats()
    
    def list_documents(self) -> List[Dict]:
        """List all documents in the knowledge base"""
        return self.vector_store.list_documents()


def get_rag_service() -> RAGService:
    """Get RAG service instance"""
    return RAGService()


def get_knowledge_service() -> KnowledgeService:
    """Get knowledge service instance"""
    return KnowledgeService()
