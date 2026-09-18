# backend/app/models/document.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    document_type = Column(String(100))
    university_id = Column(String(36), ForeignKey("universities.id"), nullable=True)
    academic_year = Column(String(20))
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=True)
    source_url = Column(String(500))
    source_type = Column(String(50))  # TCU_OFFICIAL, UNIVERSITY_OFFICIAL, HESLB, NACTVET, OTHER
    file_path = Column(String(500))
    file_size = Column(Integer)  # in bytes
    mime_type = Column(String(100))
    is_indexed = Column(Boolean, default=False)
    verification_status = Column(String(50), default="PENDING")  # PENDING, VERIFIED, REJECTED
    verified_at = Column(DateTime(timezone=True))
    verified_by = Column(String(36))
    chunk_count = Column(Integer, default=0)
    embedding_model = Column(String(100))
    embedding_model_version = Column(String(50))  # e.g., "text-embedding-ada-002-v1"
    content_hash = Column(String(64))  # SHA-256 for change detection
    extra_metadata = Column("metadata", Text)   # keep DB column name
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    university = relationship("University", backref="documents")
    academic_year_rel = relationship("AcademicYear", backref="documents")