"""
FastAPI main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import chat, knowledge, user, quiz
from backend.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AI Tutor API",
    description="基于大模型与RAG技术的个性化智能学习与助教系统",
    version="0.1.0"
)

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "AI Tutor API is running"}


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "services": {
            "api": "ok",
            "database": "pending",  # Will be updated when DB is connected
            "vectorstore": "pending"
        }
    }
