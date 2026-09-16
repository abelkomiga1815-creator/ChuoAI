# backend/app/services/document_service.py
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.document import Document


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    async def list_documents(self, skip: int = 0, limit: int = 50) -> List[Document]:
        return self.db.query(Document).offset(skip).limit(limit).all()

    async def get_document(self, document_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id).first()

    async def delete_document(self, document_id: str) -> bool:
        doc = await self.get_document(document_id)
        if not doc:
            return False
        self.db.delete(doc)
        self.db.commit()
        return True