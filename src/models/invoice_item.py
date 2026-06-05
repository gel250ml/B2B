import uuid

from sqlalchemy import Column, Integer, String, ForeignKey, Index, UniqueConstraint, CheckConstraint, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from src.database.base import Base


class InvoiceItem(AsyncAttrs, Base):
    __tablename__ = 'invoice_items'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(Uuid(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    sku_id = Column(Uuid(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    sku_name = Column(String(255), nullable=False)
    accepted_quantity = Column(Integer, nullable=True)

    invoice = relationship("Invoice", backref="items")
    sku = relationship("Sku", backref="invoice_items")

    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        UniqueConstraint('invoice_id', 'sku_id', name='uq_invoice_item'),
        Index('idx_invoice_items_invoice_id', 'invoice_id'),
        Index('idx_invoice_items_sku_id', 'sku_id'),
    )
