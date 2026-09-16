# backend/app/api/comparison.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..services.comparison_service import ComparisonService
from ..schemas.comparison import ComparisonRequest, ComparisonResponse

router = APIRouter()


@router.post("", response_model=ComparisonResponse)
async def compare_universities(
    request: ComparisonRequest,
    db: Session = Depends(get_db),
):
    """Compare two or more universities, optionally for a specific programme."""
    service = ComparisonService(db)
    result = await service.compare(
        university_ids=request.university_ids,
        programme=request.programme,
    )
    return result