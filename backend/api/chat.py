"""
Chat API endpoints
"""
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from backend.services.rag_service import get_rag_service
from backend.config import get_settings

router = APIRouter()
settings = get_settings()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: Optional[str] = None
    use_rag: bool = True


class SourceReference(BaseModel):
    """Knowledge source reference"""
    content: str
    source: str  # e.g., "《数据结构》第5章第3节"
    relevance_score: float = 0.0


class ChatResponse(BaseModel):
    """Chat response model"""
    answer: str
    conversation_id: str
    sources: List[SourceReference] = []
    has_context: bool = True


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to AI Tutor and get a response.
    
    - **message**: User's question
    - **conversation_id**: Optional conversation ID for context continuity
    - **use_rag**: Whether to use RAG for retrieval (default: True)
    """
    # Check if API key is configured
    if not settings.deepseek_api_key:
        raise HTTPException(
            status_code=503,
            detail="LLM API Key 未配置。请在 .env 文件中设置 DEEPSEEK_API_KEY。"
        )
    
    # Generate conversation ID if not provided
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    try:
        if request.use_rag:
            # Use RAG service for retrieval-augmented generation
            rag_service = get_rag_service()
            result = await rag_service.query(
                question=request.message,
                k=5,
                include_sources=True
            )
            
            # Format sources
            sources = [
                SourceReference(
                    content=s.get("content", ""),
                    source=s.get("source", "Unknown"),
                    relevance_score=s.get("relevance_score", 0.0)
                )
                for s in result.get("sources", [])
            ]
            
            return ChatResponse(
                answer=result["answer"],
                conversation_id=conversation_id,
                sources=sources,
                has_context=result.get("has_context", True)
            )
        else:
            # Direct LLM call without RAG
            from backend.core.llm import chat_completion
            
            answer = await chat_completion([
                {"role": "system", "content": "你是一个专业的《数据结构》课程助教。"},
                {"role": "user", "content": request.message}
            ])
            
            return ChatResponse(
                answer=answer,
                conversation_id=conversation_id,
                sources=[],
                has_context=False
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理请求时发生错误: {str(e)}"
        )


@router.get("/history/{conversation_id}")
async def get_chat_history(conversation_id: str):
    """Get chat history for a conversation"""
    # TODO: Implement chat history retrieval
    return {"conversation_id": conversation_id, "messages": []}
