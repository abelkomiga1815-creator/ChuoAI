# backend/app/services/programme_service.py
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.programme import Programme
from ..models.university import University


class ProgrammeService:
    def __init__(self, db: Session):
        self.db = db

    async def list_programmes(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        university_id: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[Programme]:
        q = self.db.query(Programme).filter(Programme.is_active == True)
        if search:
            q = q.filter(Programme.name.ilike(f"%{search}%"))
        if university_id:
            q = q.filter(Programme.university_id == university_id)
        if level:
            q = q.filter(Programme.level == level)
        return q.offset(skip).limit(limit).all()

    async def get_programme(self, programme_id: str) -> Optional[Programme]:
        return self.db.query(Programme).filter(Programme.id == programme_id).first()

    async def create_programme(self, data) -> Programme:
        programme = Programme(**data.dict())
        self.db.add(programme)
        self.db.commit()
        self.db.refresh(programme)
        return programme

    async def update_programme(self, programme_id: str, data) -> Optional[Programme]:
        programme = await self.get_programme(programme_id)
        if not programme:
            return None
        for field, value in data.dict(exclude_unset=True).items():
            setattr(programme, field, value)
        self.db.commit()
        self.db.refresh(programme)
        return programme

    async def delete_programme(self, programme_id: str) -> bool:
        programme = await self.get_programme(programme_id)
        if not programme:
            return False
        programme.is_active = False
        self.db.commit()
        return True