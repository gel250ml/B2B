from sqlalchemy import (
    Column, Integer, String, DateTime, Index
)
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class Invoice(AsyncAttrs, Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, server_default='CREATED')
    created_at = Column(DateTime, server_default=func.now())
    accepted_at = Column(DateTime, nullable=True)


    # Индексы
    __table_args__ = (
        Index('idx_invoices_seller_id', 'seller_id'),
        Index('idx_invoices_status', 'status'),
    )