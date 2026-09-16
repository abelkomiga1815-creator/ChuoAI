# backend/app/api/__init__.py
from fastapi import APIRouter

from .auth import router as auth_router
from .chat import router as chat_router
from .universities import router as universities_router
from .programmes import router as programmes_router
from .eligibility import router as eligibility_router
from .comparison import router as comparison_router
from .search import router as search_router
from .admin import admin_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(universities_router, prefix="/universities", tags=["Universities"])
api_router.include_router(programmes_router, prefix="/programmes", tags=["Programmes"])
api_router.include_router(eligibility_router, prefix="/eligibility", tags=["Eligibility"])
api_router.include_router(comparison_router, prefix="/compare", tags=["Comparison"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])