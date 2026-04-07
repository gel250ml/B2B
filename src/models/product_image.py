from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Index, UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class ProductImage(AsyncAttrs, Base):
    __tablename__ = 'product_images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
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