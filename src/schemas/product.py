from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator


class ProductImageCreate(BaseModel):
    url: str = Field(..., description="URL изображения")
    ordering: int = Field(0, description="Порядок отображения")


class ProductCharacteristicCreate(BaseModel):
    characteristic_id: int = Field(..., description="ID характеристики из справочника")
    value: str = Field(..., description="Значение характеристики")


class ProductCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    category_id: int
    images: List[ProductImageCreate]
    characteristics: List[ProductCharacteristicCreate] = []

    @model_validator(mode='after')
    def check_images(self):
        if not self.images:
            raise ValueError('At least one image is required')
        return self


class ProductImageResponse(BaseModel):
    id: int
    url: str
    ordering: int

    class Config:
        from_attributes = True


class ProductCharacteristicResponse(BaseModel):
    characteristic_id: int
    value: str

    class Config:
        from_attributes = True


class SkuShortResponse(BaseModel):
    id: int
    name: str
    price: int
    active_quantity: int

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    seller_id: int
    category_id: int
    deleted: bool
    images: List[ProductImageResponse] = []
    characteristic_values: List[ProductCharacteristicResponse] = []
    skus: List[SkuShortResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True