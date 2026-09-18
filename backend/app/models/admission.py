# backend/app/models/admission.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum


class QualificationType(str, enum.Enum):
    A_LEVEL = "A-LEVEL"
    DIPLOMA = "DIPLOMA"
    CERTIFICATE = "CERTIFICATE"
    MATURE = "MATURE"
    FOREIGN = "FOREIGN"
    EQUIVALENT = "EQUIVALENT"


class AdmissionRequirement(Base):
    __tablename__ = "admission_requirements"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    programme_id = Column(String(36), ForeignKey("programmes.id"), nullable=False)
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=True)
    qualification_type = Column(Enum(QualificationType), nullable=False)
    
    # Structured subject requirements
    required_subjects = Column(Text)  # Comma-separated: "Physics, Chemistry, Mathematics"
    subject_combination = Column(String(50))  # e.g., "PCM", "PCB", "CBM", "HGL"
    
    # Grade requirements
    minimum_grades = Column(String(100))  # e.g., "C,C,C" or "Two principal passes"
    minimum_points = Column(Integer)  # For points-based systems (e.g., 4.0)
    
    # Alternative requirements (JSON)
    alternative_requirements = Column(Text)
    
    # Additional conditions
    conditions = Column(Text)
    
    # Source tracking
    source = Column(String(255))
    source_url = Column(String(500))
    source_type = Column(String(50))  # TCU_OFFICIAL, UNIVERSITY_OFFICIAL, etc.
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    programme = relationship("Programme", backref="admission_requirements")
    academic_year = relationship("AcademicYear", backref="admission_requirements")