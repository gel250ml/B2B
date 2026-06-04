import uuid

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index, CheckConstraint, Uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class Reservation(AsyncAttrs, Base):
    __tablename__ = 'reservations'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reservation_id = Column(String(100), nullable=False, unique=True)
    order_id = Column(String(100), nullable=False)
    sku_id = Column(Uuid(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    sku = relationship("Sku", backref="reservations")

    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_reservation_quantity_positive'),
        Index('idx_reservations_reservation_id', 'reservation_id'),
        Index('idx_reservations_order_id', 'order_id'),
        Index('idx_reservations_sku_id', 'sku_id'),
        Index('idx_reservations_expires_at', 'expires_at'),
    )
