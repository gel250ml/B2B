import uuid

from sqlalchemy import (
    Column, Integer, String, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class SkuImage(AsyncAttrs, Base):
    __tablename__ = 'sku_images'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    url = Column(String(1000), nullable=False)
    ordering = Column(Integer, nullable=False, server_default='0')

    # Связи
    sku = relationship("Sku", backref="images")

    # Индексы
    __table_args__ = (
        Index('idx_sku_images_sku_id', 'sku_id'),
    )