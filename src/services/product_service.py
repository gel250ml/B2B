from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import ProductAccessContext
from src.repositories.product_repository import ProductRepository
from src.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from src.core.exceptions import (
    NotFoundException,
    NotOwnerException,
    ForbiddenException, ValidationException,
)
from src.services.moderation_event_service import ModerationEventService


STATUSES_RETURN_TO_MODERATION = {"MODERATED", "BLOCKED"}
BLOCKED_STATUSES = {"BLOCKED", "HARD_BLOCKED"}


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
            await self.repo.delete_product_field_reports(product_id)

        self.session.add(product)
        await self.session.commit()

        if should_send_event:
            await self.moderation_service.send_product_edited(
                product_id=product_id,
                seller_id=seller_id,
            )

        product = await self.repo.get_product_with_relations_by_id(product_id)
        return ProductResponse.model_validate(product)

    async def delete_product(self, seller_id: UUID, product_id: UUID) -> None:
        product = await self.repo.get_product_by_id_any(product_id)
        if not product:
            raise NotFoundException("Product not found")
        if product.seller_id != seller_id:
            raise NotOwnerException(...)
        if product.deleted:  # уже удалён — 400
            raise ValidationException("Product already deleted")

        sku_ids = [sku.id for sku in product.skus if not sku.deleted]

        product.deleted = True
        self.session.add(product)
        await self.session.commit()

        # fire-and-forget
        await self.moderation_service.send_product_edited(
            product_id=product_id, seller_id=seller_id, event="DELETED"
        )
        await self.moderation_service.send_product_deleted_to_b2c(
            product_id=product_id, sku_ids=sku_ids
        )

    async def get_product_detail(
        self,
        access: ProductAccessContext,
        product_id: UUID,
    ) -> dict:
        product = await self.repo.get_product_with_relations_by_id(product_id)
        if not product:
            raise NotFoundException("Product not found")

        if access.mode == "seller" and product.seller_id != access.seller_id:
            # IDOR protection: do not reveal that another seller's product exists.
            raise NotFoundException("Product not found")

        return self._serialize_product_detail(
            product,
            include_seller_private=access.mode == "seller",
        )

    async def list_products_catalog(
        self,
        ids: list[UUID] | None,
        limit: int,
        offset: int,
    ) -> dict:

        products, total = await self.repo.list_products_catalog(
            ids=ids,
            limit=limit,
            offset=offset,
        )

        return {
            "items": [
                self._serialize_product_detail(
                    product,
                    include_seller_private=False,
                )
                for product in products
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def _dt(self, value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    def _serialize_image(self, image) -> dict:
        return {
            "id": str(image.id),
            "url": image.url,
            "ordering": image.ordering,
        }

    def _serialize_characteristic_value(self, value) -> dict:
        characteristic = value.characteristic
        return {
            "id": str(value.characteristic_id),
            "name": characteristic.name if characteristic is not None else None,
            "value": value.value,
        }

    def _serialize_sku(self, sku, include_seller_private: bool) -> dict:
        data = {
            "id": str(sku.id),
            "product_id": str(sku.product_id),
            "name": sku.name,
            "price": sku.price,
            "discount": sku.discount,
            "stock_quantity": sku.stock_quantity,
            "active_quantity": sku.active_quantity,
            "article": sku.article,
            "images": [self._serialize_image(image) for image in sku.images],
            "characteristics": [
                self._serialize_characteristic_value(value)
                for value in sku.characteristic_values
            ],
            "created_at": self._dt(sku.created_at),
            "updated_at": self._dt(sku.updated_at),
        }

        if sku.images:
            data["image"] = sku.images[0].url

        if include_seller_private:
            data["cost_price"] = sku.cost_price
            data["reserved_quantity"] = sku.reserved_quantity

        return data

    def _serialize_blocking_reason(self, product) -> dict | None:
        if product.status not in BLOCKED_STATUSES or product.blocking_reason is None:
            return None

        return {
            "id": str(product.blocking_reason.id),
            "title": product.blocking_reason.title,
            "comment": (
                product.moderator_comment
                or product.blocking_reason.description
                or ""
            ),
        }

    def _serialize_field_reports(self, product) -> list[dict]:
        if product.status not in BLOCKED_STATUSES:
            return []

        return [
            {
                "field_name": report.field_name,
                "sku_id": str(report.sku_id) if report.sku_id is not None else None,
                "comment": report.comment,
            }
            for report in product.field_reports
        ]

    def _serialize_product_detail(self, product, include_seller_private: bool) -> dict:
        category = product.category
        blocked = product.status in BLOCKED_STATUSES

        return {
            "id": str(product.id),
            "seller_id": str(product.seller_id),
            "category_id": str(product.category_id),
            "category": (
                {"id": str(category.id), "name": category.name}
                if category is not None
                else None
            ),
            "title": product.title,
            "slug": product.slug,
            "description": product.description,
            "status": product.status,
            "deleted": product.deleted,
            "images": [self._serialize_image(image) for image in product.images],
            "characteristics": [
                self._serialize_characteristic_value(value)
                for value in product.characteristic_values
            ],
            "skus": [
                self._serialize_sku(sku, include_seller_private)
                for sku in product.skus
                if not sku.deleted
            ],
            "created_at": self._dt(product.created_at),
            "updated_at": self._dt(product.updated_at),
            "blocked": blocked,
            "blocking_reason": self._serialize_blocking_reason(product),
            "field_reports": self._serialize_field_reports(product),
        }
