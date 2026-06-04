from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.sku_repository import SkuRepository
from src.schemas.sku import CategoryCreate, CategoryResponse, SkuUpdate, SkuResponse
from src.core.exceptions import (
    ConflictException,
    NotFoundException,
    NotOwnerException,
    ForbiddenException,
)
from src.services.moderation_event_service import ModerationEventService


class SkuService:
    def __init__(self, session: AsyncSession):
        self.repo = SkuRepository(session)
        self.session = session
        self.moderation_service = ModerationEventService()

    async def register_category(self, data: CategoryCreate) -> CategoryResponse:
        try:
            category_dict = data.model_dump()

            category = await self.repo.create_category(category_dict)

            await self.session.commit()
            return CategoryResponse.model_validate(category)
        except IntegrityError:
            await self.session.rollback()
            raise ConflictException("Category with this slug already exists")

    async def update_sku(
        self,
        seller_id: int,
        sku_id: int,
        data: SkuUpdate,
    ) -> SkuResponse:
        sku = await self.repo.get_sku_with_product(sku_id)
        if not sku:
            raise NotFoundException("SKU not found")

        if sku.product.seller_id != seller_id:
            raise NotOwnerException(
                "SKU does not belong to the authenticated seller"
            )

        if sku.product.status == "HARD_BLOCKED":
            raise ForbiddenException("Cannot edit hard-blocked product")

        old_product_status = sku.product.status
        should_send_event = old_product_status in ["MODERATED", "BLOCKED"]

        if data.name is not None:
            sku.name = data.name
        if data.article is not None:
            sku.article = data.article
        if data.price is not None:
            sku.price = data.price

        if should_send_event:
            sku.product.status = "ON_MODERATION"

        self.session.add(sku)
        await self.session.commit()

        if should_send_event:
            await self.moderation_service.send_product_edited(
                product_id=sku.product_id, seller_id=seller_id
            )

        return SkuResponse.model_validate(sku)