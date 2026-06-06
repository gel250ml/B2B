from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.product import ProductCharacteristicCreate, ProductCharacteristicResponse, ProductImageResponse, \
    ProductImageCreate


class SkuCreate(BaseModel):
    product_id: UUID
    name: str = Field(min_length=1, max_length=255)
    price: int
    discount: int
    cost_price: Optional[int] = None
    article: Optional[str] = None
    images: List[ProductImageCreate] = []
    characteristics: List[ProductCharacteristicCreate] = []

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
