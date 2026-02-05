"""
Chat API endpoints
"""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from backend.services.rag_service import get_rag_service
from backend.services.chat_history_service import ChatHistoryService
from backend.models.database import get_db
from backend.config import get_settings

router = APIRouter()
settings = get_settings()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[int] = None  # For logged-in users
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
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a message to AI Tutor and get a response.
    
    - **message**: User's question
    - **conversation_id**: Optional conversation ID for context continuity
    - **user_id**: Optional user ID for logged-in users
    - **use_rag**: Whether to use RAG for retrieval (default: True)
    """
    # Check if API key is configured
    if not settings.deepseek_api_key:
        raise HTTPException(
            status_code=503,
            detail="LLM API Key 未配置。请在 .env 文件中设置 DEEPSEEK_API_KEY。"
        )
    
    # Get or create chat session
    chat_service = ChatHistoryService(db)
    session = chat_service.get_or_create_session(
        session_id=request.conversation_id,
        user_id=request.user_id
    )
    conversation_id = session.session_id
    
    try:
        # Save user message
        chat_service.add_message(
            session_id=conversation_id,
            role="user",
            content=request.message,
            user_id=request.user_id
        )
        
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
            
            answer = result["answer"]
            has_context = result.get("has_context", True)
            
            # Save assistant message with sources
            chat_service.add_message(
                session_id=conversation_id,
                role="assistant",
                content=answer,
                sources=[s.dict() for s in sources],
                has_rag_context=has_context
            )
            
            return ChatResponse(
                answer=answer,
                conversation_id=conversation_id,
                sources=sources,
                has_context=has_context
            )
        else:
            # Direct LLM call without RAG
            from backend.core.llm import chat_completion
            
            answer = await chat_completion([
                {"role": "system", "content": "你是一个专业的《数据结构》课程助教。"},
                {"role": "user", "content": request.message}
            ])
            
            # Save assistant message
            chat_service.add_message(
                session_id=conversation_id,
                role="assistant",
                content=answer,
                has_rag_context=False
            )
            
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
async def get_chat_history(conversation_id: str, db: Session = Depends(get_db)):
    """Get chat history for a conversation"""
    chat_service = ChatHistoryService(db)
    messages = chat_service.get_session_history_formatted(conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "messages": messages
    }


@router.delete("/session/{conversation_id}")
async def delete_chat_session(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a chat session"""
    chat_service = ChatHistoryService(db)
    success = chat_service.delete_session(conversation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {"status": "success", "message": "会话已删除"}
