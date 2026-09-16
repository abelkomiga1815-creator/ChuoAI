# backend/app/models/admission.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class AdmissionRequirement(Base):
    __tablename__ = "admission_requirements"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    programme_id = Column(String(36), ForeignKey("programmes.id"), nullable=False)
    qualification_type = Column(String(100))  # Certificate, Diploma, A-Level, etc.
    subjects = Column(Text)  # Required subjects
    grades = Column(Text)  # Required grades
    points = Column(String(50))  # Required points
    conditions = Column(Text)  # Additional conditions
    academic_year = Column(String(20))
    source = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    programme = relationship("Programme", backref="admission_requirements")