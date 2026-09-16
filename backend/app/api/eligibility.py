# backend/app/api/eligibility.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..auth.dependencies import get_current_user
from ..services.eligibility_service import EligibilityService, EligibilityStatus
from ..schemas.eligibility import EligibilityRequest, EligibilityResponse

router = APIRouter()

@router.post("/check", response_model=EligibilityResponse)
async def check_eligibility(
    request: EligibilityRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Check eligibility for a programme."""
    service = EligibilityService(db)
    
    result = await service.check_eligibility(
        programme_name=request.programme,
        qualifications=request.qualifications.dict(),
        university_name=request.university
    )
    
    return EligibilityResponse(
        status=result.status.value,
        programme=result.programme,
        university=result.university,
        requirements=result.requirements,
        student_qualifications=result.student_qualifications,
        reasoning=result.reasoning,
        sources=result.sources
    )

@router.get("/status/{status}")
async def get_eligibility_status(status: str):
    """Get status description."""
    status_map = {
        "ELIGIBLE": "You meet all requirements for this programme.",
        "NOT_ELIGIBLE": "You do not currently meet the requirements for this programme.",
        "POTENTIALLY_ELIGIBLE": "You meet some but not all requirements. Please check with the university.",
        "MORE_INFO_REQUIRED": "We need more information to determine your eligibility."
    }
    return {"status": status, "description": status_map.get(status, "Unknown status")}