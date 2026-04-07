from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


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