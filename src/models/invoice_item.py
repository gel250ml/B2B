from sqlalchemy import (
    Column, Integer, String, ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class InvoiceItem(AsyncAttrs, Base):
    __tablename__ = 'invoice_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    sku_id = Column(String(36), ForeignKey("skus.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    sku_name = Column(String(255), nullable=False)

    # Связи
    invoice = relationship("Invoice", backref="items")
    sku = relationship("Sku", backref="invoice_items")

    # Ограничения и индексы
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        UniqueConstraint('invoice_id', 'sku_id', name='uq_invoice_item'),
        Index('idx_invoice_items_invoice_id', 'invoice_id'),
        Index('idx_invoice_items_sku_id', 'sku_id'),
    )