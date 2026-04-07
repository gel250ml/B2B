from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.invoice_repository import InvoiceRepository
from src.schemas.invoice import CategoryCreate, CategoryResponse
from src.core.exceptions import ConflictException

class InvoiceService:
    def __init__(self, session: AsyncSession):
        self.repo = InvoiceRepository(session)
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