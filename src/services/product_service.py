from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.product_repository import ProductRepository
from src.schemas.product import CategoryCreate, CategoryResponse
from src.core.exceptions import ConflictException

class ProductService:
    def __init__(self, session: AsyncSession):
        self.repo = ProductRepository(session)
        self.session = session

    async def register_category(self, data: CategoryCreate) -> CategoryResponse:
        try:
            category_dict = data.model_dump()

            category = await self.repo.create_category(category_dict)

            await self.session.commit()
            return CategoryResponse.model_validate(category)
        except IntegrityError:
            await self.session.rollback()
            raise ConflictException("Category with this slug already exists")