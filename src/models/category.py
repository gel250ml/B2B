import uuid

from sqlalchemy import Column, String, ForeignKey, DateTime, Uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class Category(AsyncAttrs, Base):
    __tablename__ = 'categories'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    parent_id = Column(Uuid(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    parent = relationship("Category", remote_side=[id], backref="children")
