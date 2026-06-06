from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.sku_repository import SkuRepository
from src.schemas.sku import SkuUpdate, SkuResponse, SkuCreate
from src.core.exceptions import (
    ConflictException,
    NotFoundException,
    NotOwnerException,
    ForbiddenException, ValidationException,
)
from src.services.moderation_event_service import ModerationEventService

STATUSES_RETURN_TO_MODERATION = {"MODERATED", "BLOCKED"}


class SkuService:
    def __init__(self, session: AsyncSession):
        self.repo = SkuRepository(session)
        self.session = session
        self.moderation_service = ModerationEventService()

    async def create_sku(
            self,
            seller_id: UUID,
            data: SkuCreate
    ) -> SkuResponse:
        product = await self.repo.get_product_by_id(data.product_id)
        if product is None:
            raise NotFoundException(f"Product not found")
        if product.seller_id != seller_id:
            raise NotOwnerException("Product does not belong to the authenticated seller")

        if product.status == "HARD_BLOCKED":
            raise ForbiddenException("Cannot add SKU to hard-blocked product")

        if data.price <= 0:
            raise ValidationException("price must be a positive integer (kopecks)")

        if data.cost_price is not None and data.cost_price <= 0:
            raise ValidationException("cost_price must be a positive integer (kopecks")

        if len(data.images) == 0:
            raise ValidationException("image is required")

        resolved_characteristics = None
        if data.characteristics is not None:
            resolved_characteristics = await self._resolve_characteristics(
                category_id=product.category_id,
                characteristics=data.characteristics,
            )

        has_skus = await self.repo.has_skus(product_id=product.id)

        should_send_event = False
        event = "EDITED"
        if product.status == "CREATED" and not has_skus:
            event = "CREATED"
            should_send_event = True
        elif product.status in STATUSES_RETURN_TO_MODERATION:
            event = "EDITED"
            should_send_event = True

        if should_send_event:
            product.status = "ON_MODERATION"
            product.blocking_reason_id = None
            product.moderator_comment = None

        try:
            sku = await self.repo.create_sku(
                product_id=product.id,
                name=data.name,
                article=data.article,
                price=data.price,
                discount=data.discount,
                cost_price=data.cost_price,
                characteristics=resolved_characteristics,
                images=[img.model_dump() for img in data.images],
            )
            self.session.add(sku)
            await self.session.commit()
        except:
            await self.session.rollback()
            raise ValidationException("SKU with this article already exists")

        if should_send_event:
            await self.moderation_service.send_product_edited(
                product_id=sku.product_id,
                seller_id=seller_id,
                event=event,
            )

        sku = await self.repo.get_sku_with_product(sku.id)
        return SkuResponse.model_validate(sku)

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

    async def update_sku(
            self,
            seller_id: UUID,
            sku_id: UUID,
            data: SkuUpdate,
    ) -> SkuResponse:
        sku = await self.repo.get_sku_with_product(sku_id)
        if not sku:
            raise NotFoundException("SKU not found")

        product = sku.product
        if product.seller_id != seller_id:
            raise NotOwnerException("Product does not belong to the authenticated seller")

        if product.status == "HARD_BLOCKED":
            raise ForbiddenException("Cannot edit hard-blocked product")

        old_product_status = product.status
        should_send_event = old_product_status in STATUSES_RETURN_TO_MODERATION

        resolved_characteristics = None
        if data.characteristics is not None:
            resolved_characteristics = await self._resolve_characteristics(
                category_id=product.category_id,
                characteristics=data.characteristics,
            )

        # Сохраняем складские поля, даже если клиент передаст их extra-полями.
        old_reserved_quantity = sku.reserved_quantity
        old_active_quantity = sku.active_quantity
        old_stock_quantity = sku.stock_quantity

        if data.name is not None:
            sku.name = data.name
        if data.article is not None:
            sku.article = data.article
        if data.price is not None:
            sku.price = data.price
        if data.discount is not None:
            sku.discount = data.discount
        if data.cost_price is not None:
            sku.cost_price = data.cost_price

        sku.reserved_quantity = old_reserved_quantity
        sku.active_quantity = old_active_quantity
        sku.stock_quantity = old_stock_quantity

        if resolved_characteristics is not None:
            await self.repo.replace_sku_characteristics(sku_id, resolved_characteristics)

        if should_send_event:
            product.status = "ON_MODERATION"
            product.blocking_reason_id = None
            product.moderator_comment = None

        self.session.add(sku)
        await self.session.commit()

        if should_send_event:
            await self.moderation_service.send_product_edited(
                product_id=sku.product_id,
                seller_id=seller_id,
                event="EDITED",
            )

        sku = await self.repo.get_sku_with_product(sku_id)
        return SkuResponse.model_validate(sku)
