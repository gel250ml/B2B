from sqlalchemy import (
    Column, Integer, Text, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class SkuCharacteristicValue(AsyncAttrs, Base):
    __tablename__ = 'sku_characteristic_values'

    sku_id = Column(Integer, ForeignKey("skus.id"), primary_key=True)
    characteristic_id = Column(Integer, ForeignKey("characteristics.id"), primary_key=True)
    value = Column(Text, nullable=False)

    # Связи
    sku = relationship("Sku", backref="characteristic_values")
    characteristic = relationship("Characteristic", backref="sku_values")