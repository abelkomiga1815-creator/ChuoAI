# backend/app/models/university.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum

class UniversityType(str, enum.Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"

class University(Base):
    __tablename__ = "universities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    abbreviation = Column(String(50))
    type = Column(Enum(UniversityType), nullable=False)
    ownership = Column(String(100))
    location = Column(String(255))
    region = Column(String(100))
    city = Column(String(100))
    website = Column(String(255))
    description = Column(Text)
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    contact_address = Column(Text)
    established_year = Column(String(4))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())