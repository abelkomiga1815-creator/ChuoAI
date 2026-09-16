# backend/app/services/eligibility_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from dataclasses import dataclass
from enum import Enum

from ..models.programme import Programme
from ..models.admission import AdmissionRequirement
from ..ai.router import QueryRouter

class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    POTENTIALLY_ELIGIBLE = "POTENTIALLY_ELIGIBLE"
    MORE_INFO_REQUIRED = "MORE_INFO_REQUIRED"

@dataclass
class EligibilityResult:
    status: EligibilityStatus
    programme: str
    university: str
    requirements: List[Dict[str, Any]]
    student_qualifications: Dict[str, Any]
    reasoning: str
    sources: List[Dict[str, Any]]

class EligibilityService:
    """Service for checking eligibility."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def check_eligibility(
        self,
        programme_name: str,
        qualifications: Dict[str, Any],
        university_name: Optional[str] = None
    ) -> EligibilityResult:
        """Check if a student is eligible for a programme."""
        
        # Find programme
        programme_query = self.db.query(Programme).filter(
            Programme.name.ilike(f"%{programme_name}%"),
            Programme.is_active == True
        )
        
        if university_name:
            from ..models.university import University
            programme_query = programme_query.join(
                University,
                Programme.university_id == University.id
            ).filter(
                University.name.ilike(f"%{university_name}%")
            )
        
        programme = programme_query.first()
        
        if not programme:
            return EligibilityResult(
                status=EligibilityStatus.MORE_INFO_REQUIRED,
                programme=programme_name,
                university=university_name or "Unknown",
                requirements=[],
                student_qualifications=qualifications,
                reasoning=f"Programme '{programme_name}' not found in our database. Please verify the programme name.",
                sources=[]
            )
        
        # Get admission requirements
        requirements = self.db.query(AdmissionRequirement).filter(
            AdmissionRequirement.programme_id == programme.id,
            AdmissionRequirement.is_active == True
        ).all()
        
        if not requirements:
            return EligibilityResult(
                status=EligibilityStatus.MORE_INFO_REQUIRED,
                programme=programme.name,
                university=programme.university.name if programme.university else "Unknown",
                requirements=[],
                student_qualifications=qualifications,
                reasoning=f"No admission requirements found for {programme.name}. Please check the official university website for current requirements.",
                sources=[]
            )
        
        # Check eligibility against each requirement
        results = []
        for req in requirements:
            result = self._check_requirement(qualifications, req)
            results.append({
                "requirement": req,
                "result": result
            })
        
        # Determine overall status
        status = self._determine_status(results, qualifications)
        
        # Build reasoning
        reasoning = self._build_reasoning(results, programme, qualifications)
        
        # Build sources
        sources = []
        for req in requirements:
            if req.source:
                sources.append({
                    "title": f"Admission Requirements - {programme.name}",
                    "source_type": "official",
                    "academic_year": req.academic_year,
                    "university": programme.university.name if programme.university else None
                })
        
        return EligibilityResult(
            status=status,
            programme=programme.name,
            university=programme.university.name if programme.university else "Unknown",
            requirements=[{
                "qualification_type": req.qualification_type,
                "subjects": req.subjects,
                "grades": req.grades,
                "points": req.points,
                "conditions": req.conditions,
                "academic_year": req.academic_year
            } for req in requirements],
            student_qualifications=qualifications,
            reasoning=reasoning,
            sources=sources
        )
    
    def _check_requirement(
        self,
        qualifications: Dict[str, Any],
        requirement: AdmissionRequirement
    ) -> Dict[str, Any]:
        """Check a single admission requirement."""
        result = {
            "qualification_type": requirement.qualification_type,
            "satisfied": False,
            "details": []
        }
        
        # Check qualification type
        student_qual_type = qualifications.get("qualification_type", "").lower()
        if requirement.qualification_type and student_qual_type:
            if requirement.qualification_type.lower() in student_qual_type or student_qual_type in requirement.qualification_type.lower():
                result["details"].append(f"✓ Qualification type matches: {requirement.qualification_type}")
            else:
                result["details"].append(f"✗ Qualification type mismatch: required {requirement.qualification_type}, got {qualifications.get('qualification_type')}")
                return result
        
        # Check subjects
        if requirement.subjects:
            required_subjects = [s.strip().lower() for s in requirement.subjects.split(",")]
            student_subjects = qualifications.get("subjects", [])
            if isinstance(student_subjects, str):
                student_subjects = [s.strip().lower() for s in student_subjects.split(",")]
            else:
                student_subjects = [s.strip().lower() for s in student_subjects]
            
            missing_subjects = [s for s in required_subjects if s not in student_subjects]
            if not missing_subjects:
                result["details"].append(f"✓ All required subjects present: {requirement.subjects}")
            else:
                result["details"].append(f"✗ Missing subjects: {', '.join(missing_subjects)}")
                return result
        
        # Check grades
        if requirement.grades and qualifications.get("grades"):
            # Simple grade comparison (this should be more sophisticated in production)
            required_grades = requirement.grades.lower()
            student_grades = str(qualifications.get("grades", "")).lower()
            
            if required_grades in student_grades or student_grades in required_grades:
                result["details"].append(f"✓ Grades match: {requirement.grades}")
            else:
                result["details"].append(f"✗ Grade requirement: {requirement.grades} (you have {qualifications.get('grades')})")
                return result
        
        # Check points
        if requirement.points and qualifications.get("points"):
            try:
                required_points = float(requirement.points)
                student_points = float(qualifications.get("points", 0))
                if student_points >= required_points:
                    result["details"].append(f"✓ Points requirement met: {student_points} >= {required_points}")
                else:
                    result["details"].append(f"✗ Points requirement not met: {student_points} < {required_points}")
                    return result
            except ValueError:
                pass
        
        result["satisfied"] = True
        return result
    
    def _determine_status(
        self,
        results: List[Dict[str, Any]],
        qualifications: Dict[str, Any]
    ) -> EligibilityStatus:
        """Determine overall eligibility status."""
        if not results:
            return EligibilityStatus.MORE_INFO_REQUIRED
        
        # Count satisfied requirements
        satisfied = sum(1 for r in results if r["result"]["satisfied"])
        total = len(results)
        
        if satisfied == total:
            return EligibilityStatus.ELIGIBLE
        elif satisfied > 0:
            return EligibilityStatus.POTENTIALLY_ELIGIBLE
        else:
            # Check if we have enough info
            if not qualifications.get("subjects") and not qualifications.get("grades"):
                return EligibilityStatus.MORE_INFO_REQUIRED
            return EligibilityStatus.NOT_ELIGIBLE
    
    def _build_reasoning(
        self,
        results: List[Dict[str, Any]],
        programme: Programme,
        qualifications: Dict[str, Any]
    ) -> str:
        """Build a human-readable reasoning string."""
        lines = [f"Eligibility Check for {programme.name}"]
        
        if programme.university:
            lines.append(f"University: {programme.university.name}")
        
        lines.append("")
        
        for result in results:
            req = result["requirement"]
            check = result["result"]
            
            lines.append(f"Requirement: {req.qualification_type or 'General'}")
            for detail in check["details"]:
                lines.append(f"  {detail}")
            lines.append("")
        
        return "\n".join(lines)