import uuid

from sqlalchemy import Column, DateTime, Index, UniqueConstraint, Uuid
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.sql import func

from src.database.base import Base


class FulfilledOrder(AsyncAttrs, Base):
    __tablename__ = "fulfilled_orders"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(Uuid(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("order_id", name="uq_fulfilled_orders_order_id"),
        Index("idx_fulfilled_orders_order_id", "order_id"),
    )
