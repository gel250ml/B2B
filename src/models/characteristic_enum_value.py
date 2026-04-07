from sqlalchemy import (
    Column, Integer, String, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class CharacteristicEnumValue(AsyncAttrs, Base):
    __tablename__ = 'characteristic_enum_values'

    id = Column(Integer, primary_key=True, autoincrement=True)
    characteristic_id = Column(Integer, ForeignKey("characteristics.id"), nullable=False)
    value = Column(String(255), nullable=False)

    # Связи
    characteristic = relationship("Characteristic", backref="enum_values")

    # Уникальное ограничение на пару (characteristic_id, value)
    __table_args__ = (
        UniqueConstraint('characteristic_id', 'value', name='uq_characteristic_enum_value'),
    )