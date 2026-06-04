from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Category, Sku
from src.models.product import Product

class SkuRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_category(self, category_data: dict) -> Category:
        category = Category(**category_data)
        self.session.add(category)

        await self.session.flush()   # чтобы получить id
        return category

    async def get_category_by_id(self, category_id: UUID) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_sku_with_product(self, sku_id: UUID) -> Sku | None:
        result = await self.session.execute(
            select(Sku)
            .where(Sku.id == sku_id)
            .options(selectinload(Sku.product))
        )
        return result.scalar_one_or_none()