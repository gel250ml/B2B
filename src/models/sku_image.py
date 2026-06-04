import uuid

from sqlalchemy import Column, Integer, String, ForeignKey, Index, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class SkuImage(AsyncAttrs, Base):
    __tablename__ = 'sku_images'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku_id = Column(Uuid(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    url = Column(String(1000), nullable=False)
    ordering = Column(Integer, nullable=False, server_default='0')

    sku = relationship("Sku", backref="images")

    __table_args__ = (
        Index('idx_sku_images_sku_id', 'sku_id'),
    )
