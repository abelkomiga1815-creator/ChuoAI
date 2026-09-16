# backend/app/core/exceptions.py
from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class ChuoAIException(HTTPException):
    """Base exception for ChuoAI."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class UnauthorizedException(ChuoAIException):
    """Unauthorized exception."""
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class NotFoundException(ChuoAIException):
    """Resource not found exception."""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ValidationException(ChuoAIException):
    """Validation exception."""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

class RateLimitException(ChuoAIException):
    """Rate limit exception."""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)