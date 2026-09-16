# backend/app/models/programme.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class Programme(Base):
    __tablename__ = "programmes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String(36), ForeignKey("universities.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    level = Column(String(50))  # Bachelor, Master, PhD, Diploma, Certificate
    duration = Column(String(50))
    faculty = Column(String(255))
    description = Column(Text)
    study_mode = Column(String(50))  # Full-time, Part-time, Distance
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    university = relationship("University", backref="programmes")