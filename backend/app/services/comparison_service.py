# backend/app/services/comparison_service.py
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.university import University
from ..models.programme import Programme


class ComparisonService:
    def __init__(self, db: Session):
        self.db = db

    async def compare(self, university_ids: List[str], programme: Optional[str] = None) -> dict:
        universities = (
            self.db.query(University)
            .filter(University.id.in_(university_ids))
            .all()
        )
        result = []
        for u in universities:
            entry = {
                "university_id": u.id,
                "university_name": u.name,
                "location": u.location,
                "type": u.type.value if u.type else None,
                "ownership": u.ownership,
                "programme": None,
                "duration": None,
                "entry_requirements": None,
                "fees": None,
                "accommodation": None,
                "application_info": None,
                "sources": [],
            }
            if programme:
                prog = (
                    self.db.query(Programme)
                    .filter(
                        Programme.university_id == u.id,
                        Programme.name.ilike(f"%{programme}%"),
                        Programme.is_active == True,
                    )
                    .first()
                )
                if prog:
                    entry["programme"] = prog.name
                    entry["duration"] = prog.duration
            result.append(entry)

        return {
            "programme": programme,
            "universities": result,
            "notes": (
                "Values marked 'Not verified' indicate missing data in our knowledge base."
            ),
        }