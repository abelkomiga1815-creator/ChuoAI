# backend/app/schemas/programme.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProgrammeBase(BaseModel):
    name: str
    code: Optional[str] = None
    level: str  # Certificate, Diploma, Bachelor, Master, PhD
    duration: Optional[str] = None
    faculty: Optional[str] = None
    description: Optional[str] = None
    study_mode: Optional[str] = None


class ProgrammeCreate(ProgrammeBase):
    university_id: str


class ProgrammeUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    level: Optional[str] = None
    duration: Optional[str] = None
    faculty: Optional[str] = None
    description: Optional[str] = None
    study_mode: Optional[str] = None
    is_active: Optional[bool] = None
    
    # TCU Verification fields
    tcu_accredited: Optional[bool] = None
    tcu_programme_code: Optional[str] = None
    tcu_accreditation_date: Optional[datetime] = None
    tcu_status: Optional[str] = None
    tcu_source_url: Optional[str] = None
    
    # Fee structure
    tuition_fee_tzs: Optional[float] = None
    fee_currency: Optional[str] = None
    fee_year: Optional[str] = None
    fee_source_url: Optional[str] = None
    
    # Admission
    heslb_eligible: Optional[bool] = None
    application_deadline: Optional[datetime] = None
    intake_months: Optional[str] = None
    
    # Source
    source_url: Optional[str] = None


class ProgrammeResponse(ProgrammeBase):
    id: str
    university_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # TCU Verification fields
    tcu_accredited: Optional[bool] = None
    tcu_programme_code: Optional[str] = None
    tcu_accreditation_date: Optional[datetime] = None
    tcu_status: Optional[str] = None
    tcu_source_url: Optional[str] = None
    tcu_last_verified_at: Optional[datetime] = None
    
    # Fee structure
    tuition_fee_tzs: Optional[float] = None
    fee_currency: Optional[str] = None
    fee_year: Optional[str] = None
    fee_source_url: Optional[str] = None
    fee_last_updated: Optional[datetime] = None
    
    # Admission
    heslb_eligible: Optional[bool] = None
    application_deadline: Optional[datetime] = None
    intake_months: Optional[str] = None
    
    # Source
    source_url: Optional[str] = None
    last_verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProgrammeDetailResponse(ProgrammeResponse):
    university_name: Optional[str] = None
    admission_requirements: Optional[List[dict]] = None


class ProgrammeAliasCreate(BaseModel):
    alias: str
    is_primary: bool = False


class ProgrammeAliasResponse(BaseModel):
    id: str
    programme_id: str
    alias: str
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProgrammeVerificationResult(BaseModel):
    verified: bool
    official_sources_found: int
    total_sources_found: int
    verification_date: str