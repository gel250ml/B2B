import uuid

from sqlalchemy import (
    Column, Text, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class SkuCharacteristicValue(AsyncAttrs, Base):
    __tablename__ = 'sku_characteristic_values'

    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), primary_key=True)
    characteristic_id = Column(UUID(as_uuid=True), ForeignKey("characteristics.id"), primary_key=True)
    value = Column(Text, nullable=False)

    # Связи
    sku = relationship("Sku", backref="characteristic_values")
    characteristic = relationship("Characteristic", backref="sku_values")