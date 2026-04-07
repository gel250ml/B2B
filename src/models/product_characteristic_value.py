from sqlalchemy import (
    Column, Integer, Text, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class ProductCharacteristicValue(AsyncAttrs, Base):
    __tablename__ = 'product_characteristic_values'

    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    characteristic_id = Column(Integer, ForeignKey("characteristics.id"), primary_key=True)
    value = Column(Text, nullable=False)

    # Связи
    product = relationship("Product", backref="characteristic_values")
    characteristic = relationship("Characteristic", backref="product_values")