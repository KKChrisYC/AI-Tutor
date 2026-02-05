"""
Knowledge base management API endpoints
"""
import uuid
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from backend.utils.pdf_parser import PDFParser
from backend.utils.text_splitter import CodeAwareTextSplitter
from backend.services.rag_service import get_knowledge_service
from backend.config import get_settings

router = APIRouter()
settings = get_settings()


class DocumentInfo(BaseModel):
    """Document information model"""
    id: str
    source: str
    chunk_count: int
    added_at: str


class KnowledgeBaseStats(BaseModel):
    """Knowledge base statistics"""
    total_documents: int
    total_chunks: int
    collection_name: str


class UploadResponse(BaseModel):
    """Upload response model"""
    status: str
    message: str
    document_id: str
    filename: str
    chunks_added: int


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to the knowledge base.
    
    Supported formats: PDF, TXT, MD
    """
    # Validate file type
    filename = file.filename or "unknown"
    file_ext = filename.lower().split(".")[-1]
    
    if file_ext not in ["pdf", "txt", "md"]:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}。请上传 PDF、TXT 或 MD 文件。"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse document based on type
        if file_ext == "pdf":
            parsed = PDFParser.extract_text_from_bytes(content, filename)
        else:
            # TXT or MD - direct text
            text_content = content.decode("utf-8")
            parsed = {
                "filename": filename,
                "total_pages": 1,
                "pages": [{"page_number": 1, "content": text_content}],
                "full_text": text_content
            }
        
        # Split into chunks
        splitter = CodeAwareTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_document(parsed)
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="无法从文档中提取有效内容。请检查文件是否为空或损坏。"
            )
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Add to knowledge base
        knowledge_service = get_knowledge_service()
        result = knowledge_service.add_document(
            chunks=chunks,
            document_id=document_id,
            filename=filename
        )
        
        return UploadResponse(
            status="success",
            message=f"文档 '{filename}' 上传成功！",
            document_id=document_id,
            filename=filename,
            chunks_added=result["chunks_added"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理文档时发生错误: {str(e)}"
        )


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all documents in the knowledge base"""
    knowledge_service = get_knowledge_service()
    documents = knowledge_service.list_documents()
    
    return [
        DocumentInfo(
            id=doc["id"],
            source=doc["source"],
            chunk_count=doc["chunk_count"],
            added_at=doc.get("added_at", "Unknown")
        )
        for doc in documents
    ]


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the knowledge base"""
    knowledge_service = get_knowledge_service()
    result = knowledge_service.delete_document(document_id)
    
    if result["status"] == "not_found":
        raise HTTPException(
            status_code=404,
            detail=f"文档 {document_id} 未找到"
        )
    
    return {
        "status": "success",
        "message": f"已删除 {result['chunks_deleted']} 个文档块"
    }


@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats():
    """Get knowledge base statistics"""
    knowledge_service = get_knowledge_service()
    stats = knowledge_service.get_stats()
    
    return KnowledgeBaseStats(
        total_documents=stats["total_documents"],
        total_chunks=stats["total_chunks"],
        collection_name=stats["collection_name"]
    )


@router.post("/search")
async def search_knowledge(query: str, k: int = 5):
    """
    Search the knowledge base.
    
    - **query**: Search query
    - **k**: Number of results to return
    """
    from backend.core.vectorstore import get_vector_store
    
    vector_store = get_vector_store()
    results = vector_store.search_with_sources(query, k=k)
    
    return {
        "query": query,
        "results": [
            {
                "content": r["content"][:300] + "..." if len(r["content"]) > 300 else r["content"],
                "source": r["metadata"].get("source", "Unknown"),
                "page": r["metadata"].get("page", "N/A"),
                "relevance_score": r.get("relevance_score", 0)
            }
            for r in results["results"]
        ]
    }
