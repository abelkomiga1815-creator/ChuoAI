# backend/app/auth/jwt.py
"""
Thin re-export of token helpers from core.security so that
`from app.auth.jwt import create_access_token` works if you prefer
grouping JWT helpers under the auth package.
"""
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)

__all__ = ["create_access_token", "create_refresh_token", "decode_token"]