# backend/app/schemas/academic_year.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AcademicYearBase(BaseModel):
    year_label: str  # e.g., "2026/2027"
    start_year: int
    end_year: int
    is_current: bool = False
    is_active: bool = True
    description: Optional[str] = None


class AcademicYearCreate(AcademicYearBase):
    pass


class AcademicYearUpdate(BaseModel):
    year_label: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    is_current: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class AcademicYearResponse(AcademicYearBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FeeStructureBase(BaseModel):
    programme_id: str
    academic_year_id: str
    tuition_fee_tzs: int
    fee_currency: str = "TZS"
    registration_fee_tzs: Optional[int] = 0
    examination_fee_tzs: Optional[int] = 0
    library_fee_tzs: Optional[int] = 0
    medical_fee_tzs: Optional[int] = 0
    student_union_fee_tzs: Optional[int] = 0
    other_fees_tzs: Optional[int] = 0
    other_fees_description: Optional[str] = None
    source_url: Optional[str] = None
    is_verified: bool = False


class FeeStructureCreate(FeeStructureBase):
    pass


class FeeStructureUpdate(BaseModel):
    tuition_fee_tzs: Optional[int] = None
    fee_currency: Optional[str] = None
    registration_fee_tzs: Optional[int] = None
    examination_fee_tzs: Optional[int] = None
    library_fee_tzs: Optional[int] = None
    medical_fee_tzs: Optional[int] = None
    student_union_fee_tzs: Optional[int] = None
    other_fees_tzs: Optional[int] = None
    other_fees_description: Optional[str] = None
    source_url: Optional[str] = None
    is_verified: Optional[bool] = None
    notes: Optional[str] = None


class FeeStructureResponse(FeeStructureBase):
    id: str
    total_estimated_tzs: Optional[int] = None
    is_verified: bool
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubjectRequirementBase(BaseModel):
    programme_id: str
    academic_year_id: Optional[str] = None
    qualification_type: str  # A-LEVEL, DIPLOMA, CERTIFICATE, MATURE, FOREIGN, EQUIVALENT
    required_subjects: str  # Comma-separated
    subject_combination: Optional[str] = None  # PCM, PCB, CBM, etc.
    minimum_grades: Optional[str] = None
    minimum_points: Optional[int] = None
    conditions: Optional[str] = None
    alternative_qualifications: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    is_verified: bool = False


class SubjectRequirementCreate(SubjectRequirementBase):
    pass


class SubjectRequirementUpdate(BaseModel):
    required_subjects: Optional[str] = None
    subject_combination: Optional[str] = None
    minimum_grades: Optional[str] = None
    minimum_points: Optional[int] = None
    conditions: Optional[str] = None
    alternative_qualifications: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    is_verified: Optional[bool] = None


class SubjectRequirementResponse(SubjectRequirementBase):
    id: str
    is_verified: bool
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IngestionJobBase(BaseModel):
    job_type: str  # TCU_CRAWL, UNIVERSITY_CRAWL, PDF_DOWNLOAD, MANUAL_UPLOAD
    source_url: Optional[str] = None
    target_university_id: Optional[str] = None
    target_programme_id: Optional[str] = None
    is_scheduled: bool = False
    schedule_cron: Optional[str] = None


class IngestionJobCreate(IngestionJobBase):
    pass


class IngestionJobUpdate(BaseModel):
    status: Optional[str] = None
    documents_found: Optional[int] = None
    documents_new: Optional[int] = None
    documents_updated: Optional[int] = None
    documents_failed: Optional[int] = None
    error_message: Optional[str] = None
    is_scheduled: Optional[bool] = None
    schedule_cron: Optional[str] = None
    next_run_at: Optional[datetime] = None


class IngestionJobResponse(IngestionJobBase):
    id: str
    status: str
    documents_found: int
    documents_new: int
    documents_updated: int
    documents_failed: int
    last_content_hash: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    error_details: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TCUCrawlResult(BaseModel):
    job_id: str
    status: str
    message: str


class UniversityCrawlResult(BaseModel):
    job_id: str
    status: str
    message: str


class PDFDownloadResult(BaseModel):
    job_id: str
    status: str
    message: str


class IngestionResult(BaseModel):
    documents_found: int
    documents_new: int
    documents_updated: int
    documents_failed: int
    universities_found: Optional[int] = 0
    programmes_found: Optional[int] = 0