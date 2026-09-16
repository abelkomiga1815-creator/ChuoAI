# backend/app/api/search.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..core.database import get_db
from ..services.university_service import UniversityService
from ..services.programme_service import ProgrammeService

router = APIRouter()


@router.get("")
async def search(
    q: str = Query(..., min_length=2),
    type: Optional[str] = Query("all", regex="^(all|universities|programmes)$"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Unified search across universities and programmes."""
    results = {"universities": [], "programmes": []}

    if type in ("all", "universities"):
        uni_service = UniversityService(db)
        results["universities"] = await uni_service.list_universities(
            search=q, limit=limit
        )

    if type in ("all", "programmes"):
        prog_service = ProgrammeService(db)
        results["programmes"] = await prog_service.list_programmes(
            search=q, limit=limit
        )

    return results