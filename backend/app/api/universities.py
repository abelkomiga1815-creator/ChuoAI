# backend/app/api/universities.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.database import get_db
from ..models.university import UniversityType
from ..services.university_service import UniversityService
from ..schemas.university import UniversityResponse, UniversityDetailResponse

router = APIRouter()

@router.get("", response_model=List[UniversityResponse])
async def list_universities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    region: Optional[str] = None,
    type: Optional[UniversityType] = None,
    db: Session = Depends(get_db)
):
    """List universities with optional filters."""
    service = UniversityService(db)
    universities = await service.list_universities(
        skip=skip,
        limit=limit,
        search=search,
        region=region,
        university_type=type
    )
    return universities

@router.get("/{university_id}", response_model=UniversityDetailResponse)
async def get_university(
    university_id: str,
    db: Session = Depends(get_db)
):
    """Get university details."""
    service = UniversityService(db)
    university = await service.get_university(university_id)
    
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )
    
    return university

@router.get("/search/programme")
async def search_by_programme(
    programme: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Search universities by programme."""
    service = UniversityService(db)
    results = await service.search_universities_by_programme(
        programme_name=programme,
        skip=skip,
        limit=limit
    )
    return results