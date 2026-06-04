import uuid

from sqlalchemy import (
    Column, Text, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class ProductCharacteristicValue(AsyncAttrs, Base):
    __tablename__ = 'product_characteristic_values'

    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True)
    characteristic_id = Column(UUID(as_uuid=True), ForeignKey("characteristics.id"), primary_key=True)
    value = Column(Text, nullable=False)

    # Связи
    product = relationship("Product", backref="characteristic_values")
    characteristic = relationship("Characteristic", backref="product_values")

    @property
    def name(self) -> str:
        return self.characteristic.name if self.characteristic is not None else None
