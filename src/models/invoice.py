import uuid

from sqlalchemy import Column, String, DateTime, Index, Uuid
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class Invoice(AsyncAttrs, Base):
    __tablename__ = 'invoices'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(Uuid(as_uuid=True), nullable=False)
    status = Column(String(50), nullable=False, server_default='CREATED')
    created_at = Column(DateTime, server_default=func.now())
    accepted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_invoices_seller_id', 'seller_id'),
        Index('idx_invoices_status', 'status'),
    )
