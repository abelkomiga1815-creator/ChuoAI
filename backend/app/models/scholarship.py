# backend/app/models/scholarship.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base
import uuid


class Scholarship(Base):
    __tablename__ = "scholarships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    provider = Column(String(255))
    description = Column(Text)
    eligibility = Column(Text)
    deadline = Column(String(100))
    link = Column(String(500))
    source = Column(String(500))
    source_url = Column(String(500))
    source_type = Column(String(50))
    amount = Column(String(255))
    amount_tzs = Column(Integer)
    level = Column(String(100))  # Undergraduate, Postgraduate, etc.
    academic_year = Column(String(20))
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # academic_year = relationship("AcademicYear", backref="scholarships")