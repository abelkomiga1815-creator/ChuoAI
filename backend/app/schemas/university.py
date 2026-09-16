# backend/app/schemas/university.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime


class UniversityBase(BaseModel):
    name: str
    abbreviation: Optional[str] = None
    type: str  # "PUBLIC" | "PRIVATE"
    ownership: Optional[str] = None
    location: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    established_year: Optional[str] = None


class UniversityCreate(UniversityBase):
    pass


class UniversityUpdate(BaseModel):
    name: Optional[str] = None
    abbreviation: Optional[str] = None
    type: Optional[str] = None
    ownership: Optional[str] = None
    location: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    established_year: Optional[str] = None
    is_active: Optional[bool] = None


class UniversityResponse(UniversityBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UniversityDetailResponse(UniversityResponse):
    programme_count: Optional[int] = 0