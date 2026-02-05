"""
User service for authentication and profile management
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.profile import LearningProfile


class AuthService:
    """Authentication service"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{hashed}"
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            salt, stored_hash = hashed_password.split(":")
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == stored_hash
        except ValueError:
            return False
    
    @staticmethod
    def generate_token() -> str:
        """Generate a simple session token"""
        return secrets.token_urlsafe(32)


class UserService:
    """User management service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        display_name: Optional[str] = None
    ) -> Dict:
        """
        Create a new user account.
        
        Returns:
            Dict with user info or error
        """
        # Check if username exists
        if self.db.query(User).filter(User.username == username).first():
            return {"success": False, "error": "用户名已存在"}
        
        # Check if email exists
        if self.db.query(User).filter(User.email == email).first():
            return {"success": False, "error": "邮箱已被注册"}
        
        # Create user
        user = User(
            username=username,
            email=email,
            hashed_password=AuthService.hash_password(password),
            display_name=display_name or username
        )
        
        self.db.add(user)
        self.db.flush()  # Get user ID
        
        # Create learning profile
        profile = LearningProfile(user_id=user.id)
        self.db.add(profile)
        
        self.db.commit()
        self.db.refresh(user)
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name
            }
        }
    
    def authenticate(self, username: str, password: str) -> Dict:
        """
        Authenticate user credentials.
        
        Returns:
            Dict with token or error
        """
        # Find user by username or email
        user = self.db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return {"success": False, "error": "用户不存在"}
        
        if not user.is_active:
            return {"success": False, "error": "账户已被禁用"}
        
        if not AuthService.verify_password(password, user.hashed_password):
            return {"success": False, "error": "密码错误"}
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        self.db.commit()
        
        # Generate token
        token = AuthService.generate_token()
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name
            }
        }
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def update_user(self, user_id: int, **kwargs) -> Dict:
        """Update user profile"""
        user = self.get_user_by_id(user_id)
        if not user:
            return {"success": False, "error": "用户不存在"}
        
        # Update allowed fields
        allowed_fields = ["display_name", "avatar_url", "email"]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(user, field, value)
        
        self.db.commit()
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name
            }
        }
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict:
        """Change user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return {"success": False, "error": "用户不存在"}
        
        if not AuthService.verify_password(old_password, user.hashed_password):
            return {"success": False, "error": "原密码错误"}
        
        user.hashed_password = AuthService.hash_password(new_password)
        self.db.commit()
        
        return {"success": True, "message": "密码修改成功"}
