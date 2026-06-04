import uuid

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, Index, Uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class Product(AsyncAttrs, Base):
    __tablename__ = 'products'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, server_default='CREATED')
    category_id = Column(Uuid(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    seller_id = Column(Uuid(as_uuid=True), nullable=False)
    blocking_reason_id = Column(Uuid(as_uuid=True), nullable=True)
    moderator_comment = Column(Text, nullable=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    category = relationship("Category", backref="products")

    @property
    def characteristics(self):
        return self.characteristic_values

    __table_args__ = (
        Index('idx_products_seller_id', 'seller_id'),
        Index('idx_products_status', 'status'),
        Index('idx_products_category_id', 'category_id'),
        Index('idx_products_deleted', 'deleted'),
        Index('idx_products_created_at', 'created_at'),
        Index('idx_products_updated_at', 'updated_at'),
    )
