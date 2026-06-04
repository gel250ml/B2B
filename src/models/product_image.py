import uuid

from sqlalchemy import (
    Column, String, ForeignKey, DateTime, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class ProductImage(AsyncAttrs, Base):
    __tablename__ = 'product_images'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    url = Column(String(1000), nullable=False)
    ordering = Column(Integer, nullable=False, server_default='0')
    created_at = Column(DateTime, server_default=func.now())

    # Связи
    product = relationship("Product", backref="images")

    # Индексы
    __table_args__ = (
        Index('idx_product_images_product_id', 'product_id'),
        UniqueConstraint('product_id', 'ordering', name='uq_product_image_ordering'),
    )