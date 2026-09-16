# backend/app/models/faq.py
from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from ..core.database import Base
import uuid


class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100))
    language = Column(String(10), default="en")  # en, sw
    source = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())