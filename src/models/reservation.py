import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index, CheckConstraint, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.database.base import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(UUID(as_uuid=True), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    sku = relationship("Sku", backref="reservations")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_reservation_quantity_positive"),
        Index("idx_reservation_idempotency", "idempotency_key"),
        Index("idx_reservation_order", "order_id"),
        Index("idx_reservation_sku", "sku_id"),
    )