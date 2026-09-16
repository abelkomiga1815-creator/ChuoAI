# backend/app/models/scholarship.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer
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
    amount = Column(String(255))
    level = Column(String(100))  # Undergraduate, Postgraduate, etc.
    academic_year = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())