from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class ProductImageCreate(BaseModel):
    url: str = Field(..., description="URL изображения")
    ordering: int = Field(0, description="Порядок отображения")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "/s3/iphone15-front.jpg",
                "ordering": 0
            }
        }


class ProductCharacteristicCreate(BaseModel):
    name: str = Field(..., description="Название характеристики")
    value: str = Field(..., description="Значение характеристики")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Brand",
                "value": "Apple"
            }
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

    class Config:
        json_schema_extra = {
            "example": {
                "title": "iPhone 15 Pro Max",
                "description": "Флагманский смартфон Apple 2024 года с чипом A17 Pro",
                "category_id": "b1f1c3f5-66d0-47ff-8f4e-a953a0d9c0fb",
                "images": [
                    {"url": "/s3/iphone15-front.jpg", "ordering": 0},
                    {"url": "/s3/iphone15-back.jpg", "ordering": 1}
                ],
                "characteristics": [
                    {"name": "Brand", "value": "Apple"},
                    {"name": "Origin", "value": "China"}
                ]
            }
        }


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    category_id: Optional[UUID]
    images: Optional[List[ProductImageCreate]]
    characteristics: Optional[List[ProductCharacteristicCreate]]

    @model_validator(mode='after')
    def check_images(self):
        if self.images is not None and not self.images:
            raise ValueError('At least one image is required')
        return self


class ProductImageResponse(BaseModel):
    id: UUID
    url: str
    ordering: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "c09f3f58-5dd4-4303-bcf8-4e272b3c0741",
                "url": "/s3/iphone15-front.jpg",
                "ordering": 0
            }
        }


class ProductCharacteristicResponse(BaseModel):
    name: str
    value: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Brand",
                "value": "Apple"
            }
        }


class SkuShortResponse(BaseModel):
    id: UUID
    name: str
    price: int
    active_quantity: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "8dbbb3f3-7d3e-4ea9-b9b5-19d7f1a2d81c",
                "name": "256GB Black",
                "price": 12999000,
                "active_quantity": 0
            }
        }


class ProductResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    status: str
    seller_id: UUID
    category_id: UUID
    deleted: bool
    images: List[ProductImageResponse] = []
    characteristic_values: List[ProductCharacteristicResponse] = []
    skus: List[SkuShortResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "2d48d447-45ec-4b9f-a2ad-0ed12a4f033a",
                "title": "iPhone 15 Pro Max",
                "description": "Флагманский смартфон Apple 2024 года с чипом A17 Pro",
                "status": "CREATED",
                "seller_id": "9b9d17d4-9d87-4f33-bf7d-124aa7c82dc9",
                "category_id": "b1f1c3f5-66d0-47ff-8f4e-a953a0d9c0fb",
                "deleted": False,
                "images": [
                    {"id": "c09f3f58-5dd4-4303-bcf8-4e272b3c0741", "url": "/s3/iphone15-front.jpg", "ordering": 0}
                ],
                "characteristic_values": [
                    {"name": "Brand", "value": "Apple"}
                ],
                "skus": [],
                "created_at": "2026-05-11T10:00:00",
                "updated_at": "2026-05-11T10:00:00"
            }
        }