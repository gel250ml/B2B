from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """Схема для создания новой категории"""
    name: str = Field(..., max_length=255, description="Название категории")
    slug: str = Field(..., max_length=255, description="URL- slug категории (уникальный)")
    parent_id: Optional[int] = Field(None, description="ID родительской категории")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Электроника",
                "slug": "elektronika",
                "parent_id": None
            }
        }


class CategoryResponse(BaseModel):
    """Схема для ответа с данными категории"""
    id: int
    name: str
    slug: str
    parent_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryUpdate(BaseModel):
    """Схема для обновления категории (все поля опциональны)"""
    name: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[int] = Field(None)


    class Config:
        json_schema_extra = {
            "example": {
                "name": "Мужская одежда",
                "slug": "muzhskaya-odezhda",
                "parent_id": 4
            }
        }


class SkuUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    article: Optional[str] = Field(None, max_length=100)
    price: Optional[int]


class SkuResponse(BaseModel):
    id: int
    product_id: int
    name: str
    article: Optional[str]
    price: int
    active_quantity: int
    reserved_quantity: int
    deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True