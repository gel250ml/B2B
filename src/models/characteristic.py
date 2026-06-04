import uuid

from sqlalchemy import (
    Column, String, ForeignKey, DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class Characteristic(AsyncAttrs, Base):
    __tablename__ = 'characteristics'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    value_type = Column(String(20), nullable=False, server_default='string')
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Связи
    category = relationship("Category", backref="characteristics")