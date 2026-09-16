# backend/app/models/source.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    source_type = Column(String(50))  # TCU_OFFICIAL, UNIVERSITY_OFFICIAL, HESLB, NACTVET, OTHER
    url = Column(String(500))
    university_id = Column(String(36), ForeignKey("universities.id"), nullable=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    academic_year = Column(String(20))
    page_number = Column(Integer)
    priority = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    university = relationship("University", backref="sources")
    document = relationship("Document", backref="sources")