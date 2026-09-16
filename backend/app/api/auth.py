# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from ..core.database import get_db
from ..core.exceptions import UnauthorizedException
from ..services.auth_service import AuthService
from ..schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest
)
from ..auth.dependencies import get_current_user

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        auth_service = AuthService(db)
        result = await auth_service.register(user_data)
        
        return {
            "message": "User registered successfully",
            "user": UserResponse.from_orm(result["user"]),
            "tokens": result["tokens"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=dict)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Login a user."""
    auth_service = AuthService(db)
    result = await auth_service.login(credentials)
    
    return {
        "message": "Login successful",
        "user": UserResponse.from_orm(result["user"]),
        "tokens": result["tokens"]
    }

@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh an access token."""
    auth_service = AuthService(db)
    result = await auth_service.refresh_token(request.refresh_token)
    
    return {
        "message": "Token refreshed successfully",
        "tokens": result["tokens"]
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """Get current user information."""
    return UserResponse.from_orm(current_user)

@router.post("/logout")
async def logout():
    """Logout (client-side token removal)."""
    return {"message": "Logged out successfully"}