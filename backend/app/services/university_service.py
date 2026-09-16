# backend/app/services/university_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from ..models.university import University, UniversityType
from ..models.programme import Programme
from ..schemas.university import UniversityCreate, UniversityUpdate

class UniversityService:
    """Service for university operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def list_universities(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        region: Optional[str] = None,
        university_type: Optional[UniversityType] = None,
        is_active: bool = True
    ) -> List[University]:
        """List universities with filtering."""
        query = self.db.query(University)
        
        if is_active is not None:
            query = query.filter(University.is_active == is_active)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    University.name.ilike(search_term),
                    University.abbreviation.ilike(search_term),
                    University.description.ilike(search_term)
                )
            )
        
        if region:
            query = query.filter(University.region.ilike(f"%{region}%"))
        
        if university_type:
            query = query.filter(University.type == university_type)
        
        return query.offset(skip).limit(limit).all()
    
    async def get_university(self, university_id: str) -> Optional[University]:
        """Get a university by ID."""
        return self.db.query(University).filter(
            University.id == university_id
        ).first()
    
    async def get_university_by_name(self, name: str) -> Optional[University]:
        """Get a university by name."""
        return self.db.query(University).filter(
            or_(
                University.name.ilike(f"%{name}%"),
                University.abbreviation.ilike(f"%{name}%")
            )
        ).first()
    
    async def create_university(self, data: UniversityCreate) -> University:
        """Create a new university."""
        university = University(**data.dict())
        self.db.add(university)
        self.db.commit()
        self.db.refresh(university)
        return university
    
    async def update_university(
        self,
        university_id: str,
        data: UniversityUpdate
    ) -> Optional[University]:
        """Update a university."""
        university = await self.get_university(university_id)
        if not university:
            return None
        
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(university, field, value)
        
        self.db.commit()
        self.db.refresh(university)
        return university
    
    async def delete_university(self, university_id: str) -> bool:
        """Delete (deactivate) a university."""
        university = await self.get_university(university_id)
        if not university:
            return False
        
        university.is_active = False
        self.db.commit()
        return True
    
    async def search_universities_by_programme(
        self,
        programme_name: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search universities that offer a specific programme."""
        query = self.db.query(University).join(
            Programme,
            University.id == Programme.university_id
        ).filter(
            University.is_active == True,
            Programme.is_active == True,
            Programme.name.ilike(f"%{programme_name}%")
        )
        
        results = query.offset(skip).limit(limit).all()
        
        # Format results with programme information
        formatted = []
        for university in results:
            programmes = self.db.query(Programme).filter(
                Programme.university_id == university.id,
                Programme.name.ilike(f"%{programme_name}%")
            ).all()
            
            formatted.append({
                "university": university,
                "programmes": programmes
            })
        
        return formatted