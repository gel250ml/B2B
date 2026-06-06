import uuid

from sqlalchemy import Column, DateTime, String, Text, Uuid
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.base import Base


class BlockingReason(AsyncAttrs, Base):
    __tablename__ = "blocking_reasons"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    products = relationship("Product", back_populates="blocking_reason")
