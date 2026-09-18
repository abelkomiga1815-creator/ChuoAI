# backend/app/models/source.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum


class SourceType(str, enum.Enum):
    TCU_OFFICIAL = "TCU_OFFICIAL"
    UNIVERSITY_OFFICIAL = "UNIVERSITY_OFFICIAL"
    HESLB = "HESLB"
    NACTVET = "NACTVET"
    GOVERNMENT = "GOVERNMENT"
    OTHER = "OTHER"


class SourceAuthority(str, enum.Enum):
    LEVEL_1 = "LEVEL_1"  # TCU official
    LEVEL_2 = "LEVEL_2"  # University official
    LEVEL_3 = "LEVEL_3"  # Admission portals
    LEVEL_4 = "LEVEL_4"  # Official PDFs/prospectuses
    LEVEL_5 = "LEVEL_5"  # Other reliable


class Source(Base):
    __tablename__ = "sources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    source_type = Column(Enum(SourceType), nullable=False)
    authority_level = Column(Enum(SourceAuthority), default=SourceAuthority.LEVEL_5)
    url = Column(String(500))
    university_id = Column(String(36), ForeignKey("universities.id"), nullable=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    academic_year = Column(String(20))
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=True)
    page_number = Column(Integer)
    section_title = Column(String(255))
    priority = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))
    last_crawled_at = Column(DateTime(timezone=True))
    content_hash = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    university = relationship("University", backref="sources")
    document = relationship("Document", backref="sources")
    academic_year_rel = relationship("AcademicYear", backref="sources")