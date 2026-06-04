from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.product_repository import ProductRepository
from src.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from src.core.exceptions import (
    NotFoundException,
    ValidationException,
    NotOwnerException,
    ForbiddenException,
)
from src.services.moderation_event_service import ModerationEventService


STATUSES_RETURN_TO_MODERATION = {"MODERATED", "BLOCKED"}


class ProductService:
    def __init__(self, session: AsyncSession):
        self.repo = ProductRepository(session)
        self.session = session
        self.moderation_service = ModerationEventService()

    async def _resolve_characteristics(
        self,
        category_id: UUID,
        characteristics: list,
    ) -> list[dict]:
        resolved: list[dict] = []
        for char in characteristics:
            characteristic = await self.repo.get_characteristic_by_name(
                name=char.name,
                category_id=category_id,
            )
            if not characteristic:
                raise NotFoundException(f"Characteristic {char.name} not found")
            resolved.append(
                {"characteristic_id": characteristic.id, "value": char.value}
            )
        return resolved

    async def create_product(
        self,
        seller_id: UUID,
        data: ProductCreate,
    ) -> ProductResponse:
        category = await self.repo.get_category_by_id(data.category_id)
        if not category:
            raise NotFoundException("Category not found")

        characteristics = await self._resolve_characteristics(
            category_id=data.category_id,
            characteristics=data.characteristics,
        )

        product = await self.repo.create_product(
            seller_id=seller_id,
            title=data.title,
            description=data.description,
            category_id=data.category_id,
            images=[img.model_dump() for img in data.images],
            characteristics=characteristics,
        )

        await self.session.commit()
        product = await self.repo.get_product_with_relations_by_id(product.id)
        return ProductResponse.model_validate(product)

    async def update_product(
        self,
        seller_id: UUID,
        product_id: UUID,
        data: ProductUpdate,
    ) -> ProductResponse:
        product = await self.repo.get_product_with_relations_by_id(product_id)
        if not product:
            raise NotFoundException("Product not found")

        if product.seller_id != seller_id:
            raise NotOwnerException("Product does not belong to the authenticated seller")

        if product.status == "HARD_BLOCKED":
            raise ForbiddenException("Cannot edit hard-blocked product")

        old_status = product.status
        should_send_event = old_status in STATUSES_RETURN_TO_MODERATION

        target_category_id = data.category_id or product.category_id
        if data.category_id is not None:
            category = await self.repo.get_category_by_id(data.category_id)
            if not category:
                raise NotFoundException("Category not found")

        resolved_characteristics = None
        if data.characteristics is not None:
            resolved_characteristics = await self._resolve_characteristics(
                category_id=target_category_id,
                characteristics=data.characteristics,
            )

        if data.title is not None:
            product.title = data.title
        if data.description is not None:
            product.description = data.description
        if data.category_id is not None:
            product.category_id = data.category_id

        if data.images is not None:
            await self.repo.replace_product_images(
                product_id,
                [img.model_dump() for img in data.images],
            )

        if resolved_characteristics is not None:
            await self.repo.replace_product_characteristics(
                product_id,
                resolved_characteristics,
            )

        if should_send_event:
            product.status = "ON_MODERATION"
            product.blocking_reason_id = None
            product.moderator_comment = None

        self.session.add(product)
        await self.session.commit()

        if should_send_event:
            await self.moderation_service.send_product_edited(
                product_id=product_id,
                seller_id=seller_id,
            )

        product = await self.repo.get_product_with_relations_by_id(product_id)
        return ProductResponse.model_validate(product)
