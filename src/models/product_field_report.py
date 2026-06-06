import uuid

from sqlalchemy import Column, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import relationship

from src.database.base import Base


class ProductFieldReport(AsyncAttrs, Base):
    __tablename__ = "product_field_reports"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(Uuid(as_uuid=True), ForeignKey("products.id"), nullable=False)
    field_name = Column(String(50), nullable=False)
    sku_id = Column(Uuid(as_uuid=True), ForeignKey("skus.id"), nullable=True)
    comment = Column(Text, nullable=False)

    product = relationship("Product", back_populates="field_reports")
    sku = relationship("Sku", backref="field_reports")

    __table_args__ = (
        Index("idx_product_field_reports_product_id", "product_id"),
        Index("idx_product_field_reports_sku_id", "sku_id"),
    )
