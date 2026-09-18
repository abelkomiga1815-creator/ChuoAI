# backend/app/models/university.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum

class UniversityType(str, enum.Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"

class UniversityStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    INACTIVE = "INACTIVE"
    UNKNOWN = "UNKNOWN"

class University(Base):
    __tablename__ = "universities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
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
    
    # TCU Verification fields
    tcu_accredited = Column(Boolean, default=False)
    tcu_registration_number = Column(String(100))
    tcu_accreditation_date = Column(DateTime(timezone=True))
    tcu_status = Column(Enum(UniversityStatus), default=UniversityStatus.UNVERIFIED)
    tcu_last_verified_at = Column(DateTime(timezone=True))
    tcu_source_url = Column(String(500))
    
    # Source tracking
    source_url = Column(String(500))
    last_verified_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UniversityAlias(Base):
    """Aliases/abbreviations for universities to handle name variations."""
    __tablename__ = "university_aliases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String(36), ForeignKey("universities.id", ondelete="CASCADE"), nullable=False)
    alias = Column(String(255), nullable=False, index=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())