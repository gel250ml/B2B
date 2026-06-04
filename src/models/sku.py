import uuid

from sqlalchemy import (
    Column, String, Boolean, ForeignKey, DateTime, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class Sku(AsyncAttrs, Base):
    __tablename__ = 'skus'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    name = Column(String(255), nullable=False)
    article = Column(String(100), unique=True, nullable=True)
    price = Column(Integer, nullable=False)  # Цена в копейках
    active_quantity = Column(Integer, nullable=False, server_default='0')
    reserved_quantity = Column(Integer, nullable=False, server_default='0')
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Связи
    product = relationship("Product", backref="skus")

    # Индексы
    __table_args__ = (
        Index('idx_skus_product_id', 'product_id'),
        Index('idx_skus_article', 'article'),
        Index('idx_skus_deleted', 'deleted'),
    )