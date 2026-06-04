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
