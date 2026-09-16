# backend/app/api/programmes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.database import get_db
from ..services.programme_service import ProgrammeService
from ..schemas.programmes import ProgrammeResponse

router = APIRouter()


@router.get("", response_model=List[ProgrammeResponse])
async def list_programmes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    university_id: Optional[str] = None,
    level: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List programmes with optional filters."""
    service = ProgrammeService(db)
    programmes = await service.list_programmes(
        skip=skip,
        limit=limit,
        search=search,
        university_id=university_id,
        level=level,
    )
    return programmes


@router.get("/{programme_id}", response_model=ProgrammeResponse)
async def get_programme(programme_id: str, db: Session = Depends(get_db)):
    """Get a programme by ID."""
    service = ProgrammeService(db)
    programme = await service.get_programme(programme_id)
    if not programme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme not found",
        )
    return programme