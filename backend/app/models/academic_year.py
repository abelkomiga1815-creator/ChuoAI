# backend/app/models/academic_year.py
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, UniqueConstraint, Text, Numeric, Enum
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum


class TCUStatisticType(str, enum.Enum):
    """Types of TCU statistics tracked."""
    UNIVERSITY_INSTITUTIONS = "UNIVERSITY_INSTITUTIONS"
    ACADEMIC_PROGRAMMES = "ACADEMIC_PROGRAMMES"
    ACCREDITED_UNIVERSITIES = "ACCREDITED_UNIVERSITIES"
    REGISTERED_STUDENTS = "REGISTERED_STUDENTS"
    GRADUATES = "GRADUATES"
    STAFF_COUNT = "STAFF_COUNT"
    CAMPUSES = "CAMPUSES"
    FACULTIES = "FACULTIES"
    DEPARTMENTS = "DEPARTMENTS"
    OTHER = "OTHER"


class TCUStatistic(Base):
    """Structured TCU statistics for direct lookup."""
    __tablename__ = "tcu_statistics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    statistic_type = Column(Enum(TCUStatisticType), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)  # e.g., "university_institutions"
    value = Column(Integer, nullable=False)  # The actual count/value
    unit = Column(String(50), default="count")  # count, percentage, etc.
    
    # Source tracking
    source_url = Column(String(500), nullable=False)
    source_page_title = Column(String(255))
    source_section = Column(String(255))  # Section on the page where found
    
    # Academic year context
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=True)
    academic_year_label = Column(String(20))  # e.g., "2026/2027"
    
    # Metadata
    is_verified = Column(Boolean, default=True, index=True)
    verified_at = Column(DateTime(timezone=True))
    last_crawled_at = Column(DateTime(timezone=True))
    content_hash = Column(String(64))  # For change detection
    
    # Additional context
    notes = Column(Text)
    metadata_json = Column(Text)  # JSON for additional structured data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('metric_name', 'academic_year_label', name='uq_tcu_statistic_metric_year'),
    )


class AcademicYear(Base):
    """Academic year model with current year tracking."""
    __tablename__ = "academic_years"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    year_label = Column(String(20), nullable=False, unique=True)  # e.g., "2026/2027"
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    is_current = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True)
    description = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('start_year', 'end_year', name='uq_academic_year_range'),
    )


class FeeStructure(Base):
    """Structured fee information for programmes."""
    __tablename__ = "fee_structures"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    programme_id = Column(String(36), ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False)
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=False)
    
    # Tuition fees
    tuition_fee_tzs = Column(Integer)  # Stored in smallest unit (cents/shillings)
    fee_currency = Column(String(3), default="TZS")
    
    # Additional fees
    registration_fee_tzs = Column(Integer)
    examination_fee_tzs = Column(Integer)
    library_fee_tzs = Column(Integer)
    medical_fee_tzs = Column(Integer)
    student_union_fee_tzs = Column(Integer)
    other_fees_tzs = Column(Integer)
    other_fees_description = Column(Text)
    
    # Total
    total_estimated_tzs = Column(Integer)
    
    # Metadata
    source_url = Column(String(500))
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # programme = relationship("Programme", backref="fee_structures")
    # academic_year = relationship("AcademicYear", backref="fee_structures")


class SubjectRequirement(Base):
    """Structured subject-grade requirements for programmes."""
    __tablename__ = "subject_requirements"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    programme_id = Column(String(36), ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False)
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=True)
    
    # Qualification pathway
    qualification_type = Column(String(100), nullable=False)  # "A-LEVEL", "DIPLOMA", "CERTIFICATE", "MATURE"
    
    # Subject requirements (comma-separated or JSON)
    required_subjects = Column(Text, nullable=False)  # e.g., "Physics, Chemistry, Mathematics"
    subject_combination = Column(String(50))  # e.g., "PCM", "PCB", "CBM"
    
    # Grade requirements
    minimum_grades = Column(String(100))  # e.g., "C,C,C" or "Division I-III"
    minimum_points = Column(Integer)  # For points-based systems
    
    # Additional conditions
    conditions = Column(Text)
    
    # Alternative pathways
    alternative_qualifications = Column(Text)  # JSON array of alternative paths
    
    # Source
    source_url = Column(String(500))
    source_type = Column(String(50))  # TCU_OFFICIAL, UNIVERSITY_OFFICIAL, etc.
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class IngestionJob(Base):
    """Track automated ingestion/crawling jobs."""
    __tablename__ = "ingestion_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type = Column(String(50), nullable=False)  # "TCU_CRAWL", "UNIVERSITY_CRAWL", "PDF_DOWNLOAD", "MANUAL_UPLOAD"
    source_url = Column(String(500))
    target_university_id = Column(String(36), ForeignKey("universities.id", ondelete="SET NULL"), nullable=True)
    target_programme_id = Column(String(36), ForeignKey("programmes.id", ondelete="SET NULL"), nullable=True)
    
    # Status
    status = Column(String(50), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED, PARTIAL
    documents_found = Column(Integer, default=0)
    documents_new = Column(Integer, default=0)
    documents_updated = Column(Integer, default=0)
    documents_failed = Column(Integer, default=0)
    
    # Content hash for change detection
    last_content_hash = Column(String(64))
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Error tracking
    error_message = Column(Text)
    error_details = Column(Text)  # JSON
    
    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    schedule_cron = Column(String(100))  # Cron expression
    next_run_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())