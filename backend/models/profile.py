"""
Learning profile model for tracking student progress
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from backend.models.database import Base


class LearningProfile(Base):
    """Student learning profile for personalization"""
    
    __tablename__ = "learning_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Overall statistics
    total_questions = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    total_study_time_minutes = Column(Integer, default=0)
    
    # Knowledge mastery (JSON: {knowledge_point: mastery_score})
    knowledge_mastery = Column(JSON, default=dict)
    
    # Weak points (auto-analyzed)
    weak_points = Column(JSON, default=list)  # List of weak knowledge points
    
    # Quiz statistics
    total_quizzes = Column(Integer, default=0)
    total_quiz_score = Column(Float, default=0.0)
    quiz_history = Column(JSON, default=list)  # Recent quiz results
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="learning_profile")
    
    def __repr__(self):
        return f"<LearningProfile(user_id={self.user_id})>"


class KnowledgePointRecord(Base):
    """Record of knowledge point interactions"""
    
    __tablename__ = "knowledge_point_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Knowledge point info
    knowledge_point = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=True)  # e.g., "线性表", "树", "图"
    
    # Interaction type
    interaction_type = Column(String(20), nullable=False)  # "question", "quiz", "correct", "incorrect"
    
    # Related content
    related_message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<KnowledgePointRecord(user_id={self.user_id}, kp='{self.knowledge_point}')>"
