# backend/app/schemas/eligibility.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class StudentQualifications(BaseModel):
    qualification_type: Optional[str] = None
    subjects: Optional[List[str]] = None
    grades: Optional[str] = None
    points: Optional[float] = None
    division: Optional[str] = None
    other: Optional[Dict[str, Any]] = None

class EligibilityRequest(BaseModel):
    programme: str = Field(..., min_length=2)
    university: Optional[str] = None
    qualifications: StudentQualifications

class EligibilityResponse(BaseModel):
    status: str
    programme: str
    university: str
    requirements: List[Dict[str, Any]]
    student_qualifications: Dict[str, Any]
    reasoning: str
    sources: List[Dict[str, Any]]