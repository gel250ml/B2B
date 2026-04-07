from sqlalchemy import (
    Column, Integer, String, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class SkuImage(AsyncAttrs, Base):
    __tablename__ = 'sku_images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(Integer, ForeignKey("skus.id"), nullable=False)
    url = Column(String(1000), nullable=False)
    ordering = Column(Integer, nullable=False, server_default='0')

    # Связи
    sku = relationship("Sku", backref="images")

    # Индексы
    __table_args__ = (
        Index('idx_sku_images_sku_id', 'sku_id'),
    )