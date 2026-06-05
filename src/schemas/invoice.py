from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Название категории")
    slug: str = Field(..., max_length=255, description="URL-slug категории (уникальный)")
    parent_id: Optional[UUID] = Field(None, description="ID родительской категории")


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    parent_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[UUID] = Field(None)


class InvoiceCreateItem(BaseModel):
    sku_id: UUID = Field(..., description="ID SKU")
    quantity: int = Field(..., description="Заявленное количество")


class InvoiceCreate(BaseModel):
    items: list[InvoiceCreateItem] = Field(..., description="Позиции накладной. Минимум 1")


class InvoiceItemResponse(BaseModel):
    sku_id: UUID
    sku_name: str
    quantity: int
    accepted_quantity: Optional[int] = None

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    items: list[InvoiceItemResponse]

    class Config:
        from_attributes = True
