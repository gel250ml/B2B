from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Category # или другие модели с которыми будем работать

class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_category(self, category_data: dict) -> Category:
        category = Category(**category_data)
        self.session.add(category)

        await self.session.flush()   # чтобы получить id
        return category

    async def get_category_by_id(self, category_id: int) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()