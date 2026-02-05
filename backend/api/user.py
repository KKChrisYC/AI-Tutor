"""
User and student profile API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.user_service import UserService
from backend.services.chat_history_service import ChatHistoryService

router = APIRouter()


# Request/Response Models
class UserCreate(BaseModel):
    """User registration model"""
    username: str
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login model"""
    username: str  # Can be username or email
    password: str


class UserResponse(BaseModel):
    """User info response"""
    id: int
    username: str
    email: str
    display_name: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response with token"""
    success: bool
    token: Optional[str] = None
    user: Optional[UserResponse] = None
    error: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """Chat session info"""
    session_id: str
    title: Optional[str] = None
    created_at: str
    updated_at: str


# API Endpoints
@router.post("/register", response_model=LoginResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (min 6 characters)
    - **display_name**: Optional display name
    """
    if len(user.username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少3个字符")
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6个字符")
    
    user_service = UserService(db)
    result = user_service.create_user(
        username=user.username,
        email=user.email,
        password=user.password,
        display_name=user.display_name
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Auto login after registration
    login_result = user_service.authenticate(user.username, user.password)
    
    return LoginResponse(
        success=True,
        token=login_result.get("token"),
        user=UserResponse(**login_result["user"])
    )


@router.post("/login", response_model=LoginResponse)
async def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    User login.
    
    - **username**: Username or email
    - **password**: Password
    """
    user_service = UserService(db)
    result = user_service.authenticate(credentials.username, credentials.password)
    
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    
    return LoginResponse(
        success=True,
        token=result["token"],
        user=UserResponse(**result["user"])
    )


@router.get("/profile/{user_id}", response_model=UserResponse)
async def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get user profile by ID"""
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name
    )


@router.get("/sessions/{user_id}", response_model=List[ChatSessionResponse])
async def get_user_chat_sessions(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's chat session history"""
    chat_service = ChatHistoryService(db)
    sessions = chat_service.get_user_sessions(user_id, limit=limit)
    
    return [
        ChatSessionResponse(
            session_id=s.session_id,
            title=s.title,
            created_at=s.created_at.isoformat() if s.created_at else "",
            updated_at=s.updated_at.isoformat() if s.updated_at else ""
        )
        for s in sessions
    ]


@router.get("/learning-profile/{user_id}")
async def get_learning_profile(user_id: int, db: Session = Depends(get_db)):
    """Get student's learning profile with knowledge mastery analysis"""
    from backend.models.profile import LearningProfile
    
    profile = db.query(LearningProfile).filter(
        LearningProfile.user_id == user_id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="学习档案不存在")
    
    return {
        "user_id": user_id,
        "total_questions": profile.total_questions,
        "total_sessions": profile.total_sessions,
        "total_study_time_minutes": profile.total_study_time_minutes,
        "knowledge_mastery": profile.knowledge_mastery or {},
        "weak_points": profile.weak_points or [],
        "total_quizzes": profile.total_quizzes,
        "average_quiz_score": (
            profile.total_quiz_score / profile.total_quizzes 
            if profile.total_quizzes > 0 else 0
        ),
        "last_active": profile.last_active_at.isoformat() if profile.last_active_at else None
    }
