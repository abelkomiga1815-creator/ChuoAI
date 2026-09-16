# backend/app/services/auth_service.py
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.user import User, UserRole
from ..core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from ..core.exceptions import UnauthorizedException, NotFoundException
from ..schemas.auth import UserCreate, UserLogin

class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def register(self, user_data: UserCreate) -> Dict[str, Any]:
        """Register a new user."""
        # Check if user exists
        existing_user = self.db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise ValueError("Email already registered")
            else:
                raise ValueError("Username already taken")
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            role=UserRole.USER
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Generate tokens
        tokens = self._generate_tokens(user)
        
        return {
            "user": user,
            "tokens": tokens
        }
    
    async def login(self, credentials: UserLogin) -> Dict[str, Any]:
        """Authenticate a user."""
        # Find user by email or username
        user = self.db.query(User).filter(
            (User.email == credentials.email) | (User.username == credentials.email)
        ).first()
        
        if not user:
            raise UnauthorizedException("Invalid credentials")
        
        if not verify_password(credentials.password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")
        
        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Generate tokens
        tokens = self._generate_tokens(user)
        
        return {
            "user": user,
            "tokens": tokens
        }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an access token."""
        payload = decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid refresh token")
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")
        
        # Generate new tokens
        tokens = self._generate_tokens(user)
        
        return {
            "user": user,
            "tokens": tokens
        }
    
    def _generate_tokens(self, user: User) -> Dict[str, str]:
        """Generate access and refresh tokens for a user."""
        token_data = {
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role.value
        }
        
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer"
        }
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return self.db.query(User).filter(User.email == email).first()