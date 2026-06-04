from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.product import ProductCharacteristicCreate, ProductCharacteristicResponse, ProductImageResponse


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


class SkuUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    price: Optional[int] = Field(None, ge=0)
    discount: Optional[int] = Field(None, ge=0)
    cost_price: Optional[int] = Field(None, ge=0)
    article: Optional[str] = Field(None, max_length=100)
    characteristics: Optional[List[ProductCharacteristicCreate]] = None


class SkuResponse(BaseModel):
    id: UUID
    product_id: UUID
    name: str
    price: int
    discount: int = 0
    cost_price: int = 0
    stock_quantity: int = 0
    active_quantity: int
    reserved_quantity: int
    article: Optional[str]
    images: List[ProductImageResponse] = []
    characteristics: List[ProductCharacteristicResponse] = []
    deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
