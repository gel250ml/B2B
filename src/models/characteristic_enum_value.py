import uuid

from sqlalchemy import (
    Column, String, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class CharacteristicEnumValue(AsyncAttrs, Base):
    __tablename__ = 'characteristic_enum_values'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    characteristic_id = Column(UUID(as_uuid=True), ForeignKey("characteristics.id"), nullable=False)
    value = Column(String(255), nullable=False)

    # Связи
    characteristic = relationship("Characteristic", backref="enum_values")

    # Уникальное ограничение на пару (characteristic_id, value)
    __table_args__ = (
        UniqueConstraint('characteristic_id', 'value', name='uq_characteristic_enum_value'),
    )