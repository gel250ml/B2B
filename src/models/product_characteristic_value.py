from sqlalchemy import Column, Text, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class ProductCharacteristicValue(AsyncAttrs, Base):
    __tablename__ = 'product_characteristic_values'

    product_id = Column(Uuid(as_uuid=True), ForeignKey("products.id"), primary_key=True)
    characteristic_id = Column(Uuid(as_uuid=True), ForeignKey("characteristics.id"), primary_key=True)
    value = Column(Text, nullable=False)

    product = relationship("Product", backref="characteristic_values")
    characteristic = relationship("Characteristic", backref="product_values")

    @property
    def name(self) -> str | None:
        return self.characteristic.name if self.characteristic is not None else None
