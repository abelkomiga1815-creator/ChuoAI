# backend/app/schemas/admin.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DashboardStats(BaseModel):
    total_universities: int
    total_programmes: int
    total_users: int
    total_conversations: int
    total_documents: int
    indexed_documents: int


class DocumentUploadResponse(BaseModel):
    document_id: str
    title: str
    status: str
    chunk_count: Optional[int] = 0
    message: str


class IndexResponse(BaseModel):
    document_id: str
    status: str
    chunk_count: int
    message: str