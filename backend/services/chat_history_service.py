"""
Chat history service for storing and retrieving conversations
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.chat_history import ChatSession, ChatMessage


class ChatHistoryService:
    """Service for managing chat history"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(
        self,
        user_id: Optional[int] = None,
        title: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session by UUID"""
        return self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
    
    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> ChatSession:
        """Get existing session or create new one"""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        
        return self.create_session(user_id=user_id)
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: Optional[int] = None,
        sources: Optional[List[Dict]] = None,
        has_rag_context: bool = False,
        knowledge_points: Optional[List[str]] = None
    ) -> ChatMessage:
        """Add a message to a session"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        message = ChatMessage(
            session_id=session.id,
            user_id=user_id,
            role=role,
            content=content,
            sources=sources,
            has_rag_context=has_rag_context,
            knowledge_points=knowledge_points
        )
        
        self.db.add(message)
        
        # Update session title from first user message
        if role == "user" and not session.title:
            session.title = content[:50] + ("..." if len(content) > 50 else "")
        
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get all messages in a session"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        query = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_user_sessions(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[ChatSession]:
        """Get user's chat sessions"""
        return self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(desc(ChatSession.updated_at)).limit(limit).all()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Delete messages first
        self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).delete()
        
        # Delete session
        self.db.delete(session)
        self.db.commit()
        return True
    
    def get_session_history_formatted(self, session_id: str) -> List[Dict]:
        """Get session messages formatted for display"""
        messages = self.get_session_messages(session_id)
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "sources": msg.sources or [],
                "timestamp": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]
