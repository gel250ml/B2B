from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ProductImageCreate(BaseModel):
    url: str = Field(..., description="URL изображения")
    ordering: int = Field(0, description="Порядок отображения")

    class Config:
        json_schema_extra = {
            "example": {"url": "/s3/iphone15-front.jpg", "ordering": 0}
        }


class ProductCharacteristicCreate(BaseModel):
    name: str = Field(..., description="Название характеристики")
    value: str = Field(..., description="Значение характеристики")

    class Config:
        json_schema_extra = {
            "example": {"name": "Бренд", "value": "Apple"}
        }


class ProductCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=5000)
    category_id: UUID
    images: List[ProductImageCreate]
    characteristics: List[ProductCharacteristicCreate] = []

    @model_validator(mode='after')
    def check_images(self):
        if not self.images:
            raise ValueError('At least one image is required')
        return self


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    category_id: Optional[UUID] = None
    images: Optional[List[ProductImageCreate]] = None
    characteristics: Optional[List[ProductCharacteristicCreate]] = None


class ProductImageResponse(BaseModel):
    id: UUID
    url: str
    ordering: int

    class Config:
        from_attributes = True


class ProductCharacteristicResponse(BaseModel):
    name: str
    value: str

    class Config:
        from_attributes = True


class SkuShortResponse(BaseModel):
    id: UUID
    product_id: Optional[UUID] = None
    name: str
    price: int
    discount: int = 0
    cost_price: int = 0
    stock_quantity: int = 0
    active_quantity: int
    reserved_quantity: int = 0
    article: Optional[str] = None

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: UUID
    seller_id: UUID
    category_id: UUID
    title: str
    slug: Optional[str] = None
    description: Optional[str]
    status: str
    deleted: bool
    blocking_reason_id: Optional[UUID] = None
    moderator_comment: Optional[str] = None
    images: List[ProductImageResponse] = []
    characteristics: List[ProductCharacteristicResponse] = []
    skus: List[SkuShortResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
