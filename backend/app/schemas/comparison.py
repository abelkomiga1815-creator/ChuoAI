# backend/app/schemas/comparison.py
from pydantic import BaseModel
from typing import List, Optional


class ComparisonRequest(BaseModel):
    university_ids: List[str]
    programme: Optional[str] = None


class UniversityComparison(BaseModel):
    university_id: str
    university_name: str
    location: Optional[str] = None
    type: Optional[str] = None
    ownership: Optional[str] = None
    programme: Optional[str] = None
    duration: Optional[str] = None
    entry_requirements: Optional[str] = None
    fees: Optional[str] = None
    accommodation: Optional[str] = None
    application_info: Optional[str] = None
    sources: List[dict] = []


class ComparisonResponse(BaseModel):
    programme: Optional[str] = None
    universities: List[UniversityComparison]
    notes: Optional[str] = None