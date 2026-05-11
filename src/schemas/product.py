from datetime import datetime
from typing import Optional, List
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
    characteristic_id: int = Field(..., description="ID характеристики из справочника")
    value: str = Field(..., description="Значение характеристики")

    class Config:
        json_schema_extra = {
            "example": {
                "characteristic_id": 1,
                "value": "Apple"
            }
        }


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

    class Config:
        json_schema_extra = {
            "example": {
                "title": "iPhone 15 Pro Max",
                "description": "Флагманский смартфон Apple 2024 года с чипом A17 Pro",
                "category_id": 1,
                "images": [
                    {"url": "/s3/iphone15-front.jpg", "ordering": 0},
                    {"url": "/s3/iphone15-back.jpg", "ordering": 1}
                ],
                "characteristics": [
                    {"characteristic_id": 1, "value": "Apple"},
                    {"characteristic_id": 2, "value": "Китай"}
                ]
            }
        }


class ProductImageResponse(BaseModel):
    id: int
    url: str
    ordering: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "url": "/s3/iphone15-front.jpg",
                "ordering": 0
            }
        }


class ProductCharacteristicResponse(BaseModel):
    characteristic_id: int
    value: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "characteristic_id": 1,
                "value": "Apple"
            }
        }


class SkuShortResponse(BaseModel):
    id: int
    name: str
    price: int
    active_quantity: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "256GB Black",
                "price": 12999000,
                "active_quantity": 0
            }
        }


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
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "iPhone 15 Pro Max",
                "description": "Флагманский смартфон Apple 2024 года с чипом A17 Pro",
                "status": "CREATED",
                "seller_id": 1,
                "category_id": 1,
                "deleted": False,
                "images": [
                    {"id": 1, "url": "/s3/iphone15-front.jpg", "ordering": 0}
                ],
                "characteristic_values": [
                    {"characteristic_id": 1, "value": "Apple"}
                ],
                "skus": [],
                "created_at": "2026-05-11T10:00:00",
                "updated_at": "2026-05-11T10:00:00"
            }
        }