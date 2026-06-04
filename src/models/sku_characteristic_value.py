from sqlalchemy import Column, Text, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class SkuCharacteristicValue(AsyncAttrs, Base):
    __tablename__ = 'sku_characteristic_values'

    sku_id = Column(Uuid(as_uuid=True), ForeignKey("skus.id"), primary_key=True)
    characteristic_id = Column(Uuid(as_uuid=True), ForeignKey("characteristics.id"), primary_key=True)
    value = Column(Text, nullable=False)

    sku = relationship("Sku", backref="characteristic_values")
    characteristic = relationship("Characteristic", backref="sku_values")

    @property
    def name(self) -> str | None:
        return self.characteristic.name if self.characteristic is not None else None
