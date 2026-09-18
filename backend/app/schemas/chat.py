# backend/app/schemas/chat.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    language: Optional[str] = "auto"


class SourceResponse(BaseModel):
    title: str
    source_type: str
    authority_level: Optional[str] = None
    url: Optional[str] = None
    university: Optional[str] = None
    university_id: Optional[str] = None
    academic_year: Optional[str] = None
    academic_year_id: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    similarity: float
    is_verified: bool = False


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    sources: Optional[List[SourceResponse]] = None
    metadata: Optional[Dict[str, Any]] = None
    entities: Optional[Dict[str, Any]] = None
    filters_applied: Optional[Dict[str, Any]] = None


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: Optional[List[SourceResponse]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    title: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    messages: Optional[List[MessageResponse]] = None
    
    class Config:
        from_attributes = True