# backend/app/models/programme.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum

class ProgrammeLevel(str, enum.Enum):
    CERTIFICATE = "Certificate"
    DIPLOMA = "Diploma"
    BACHELOR = "Bachelor"
    MASTER = "Master"
    PHD = "PhD"

class ProgrammeStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    INACTIVE = "INACTIVE"
    UNKNOWN = "UNKNOWN"

class StudyMode(str, enum.Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    DISTANCE = "Distance"
    ONLINE = "Online"

class Programme(Base):
    __tablename__ = "programmes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String(36), ForeignKey("universities.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    level = Column(Enum(ProgrammeLevel), nullable=False)
    duration = Column(String(50))
    faculty = Column(String(255))
    description = Column(Text)
    study_mode = Column(Enum(StudyMode))
    is_active = Column(Boolean, default=True)
    
    # TCU Verification fields
    tcu_accredited = Column(Boolean, default=False)
    tcu_programme_code = Column(String(100))
    tcu_accreditation_date = Column(DateTime(timezone=True))
    tcu_status = Column(Enum(ProgrammeStatus), default=ProgrammeStatus.UNVERIFIED)
    tcu_last_verified_at = Column(DateTime(timezone=True))
    tcu_source_url = Column(String(500))
    
    # Fee structure
    tuition_fee_tzs = Column(Numeric(15, 2))
    fee_currency = Column(String(3), default="TZS")
    fee_year = Column(String(20))  # Academic year this fee applies to
    fee_source_url = Column(String(500))
    fee_last_updated = Column(DateTime(timezone=True))
    
    # Admission
    heslb_eligible = Column(Boolean, default=False)
    application_deadline = Column(DateTime(timezone=True))
    intake_months = Column(String(100))  # e.g., "September, October"
    
    # Source tracking
    source_url = Column(String(500))
    last_verified_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    university = relationship("University", backref="programmes")


class ProgrammeAlias(Base):
    """Aliases/name variations for programmes."""
    __tablename__ = "programme_aliases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    programme_id = Column(String(36), ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False)
    alias = Column(String(255), nullable=False, index=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())