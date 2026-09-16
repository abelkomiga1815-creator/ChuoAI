# backend/app/schemas/programme.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProgrammeBase(BaseModel):
    name: str
    code: Optional[str] = None
    level: Optional[str] = None
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


class ProgrammeResponse(ProgrammeBase):
    id: str
    university_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProgrammeDetailResponse(ProgrammeResponse):
    university_name: Optional[str] = None
    admission_requirements: Optional[List[dict]] = None