"""
Chat API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: Optional[str] = None
    use_rag: bool = True


class SourceReference(BaseModel):
    """Knowledge source reference"""
    content: str
    source: str  # e.g., "《数据结构》第5章第3节"
    page: Optional[int] = None
    relevance_score: float


class ChatResponse(BaseModel):
    """Chat response model"""
    answer: str
    conversation_id: str
    sources: List[SourceReference] = []


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to AI Tutor and get a response.
    
    - **message**: User's question
    - **conversation_id**: Optional conversation ID for context continuity
    - **use_rag**: Whether to use RAG for retrieval (default: True)
    """
    # TODO: Implement RAG-based chat logic
    # For now, return a placeholder response
    return ChatResponse(
        answer="这是一个占位回复。RAG 功能待实现。",
        conversation_id=request.conversation_id or "new_conversation",
        sources=[]
    )


@router.get("/history/{conversation_id}")
async def get_chat_history(conversation_id: str):
    """Get chat history for a conversation"""
    # TODO: Implement chat history retrieval
    return {"conversation_id": conversation_id, "messages": []}
