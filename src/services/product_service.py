from uuid import uuid4
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


class ProductService:
    def __init__(self, session: AsyncSession):
        self.repo = ProductRepository(session)
        self.session = session
        self.moderation_service = ModerationEventService()

    async def create_product(
        self,
        seller_id: int,
        data: ProductCreate,
    ) -> ProductResponse:
        category = await self.repo.get_category_by_id(data.category_id)
        if not category:
            raise NotFoundException("Category not found")

        for char in data.characteristics:
            characteristic = await self.repo.get_characteristic_by_id(
                char.characteristic_id
            )
            if not characteristic:
                raise NotFoundException(
                    f"Characteristic {char.characteristic_id} not found"
                )
            if characteristic.category_id != data.category_id:
                raise ValidationException(
                    f"Characteristic {char.characteristic_id} "
                    f"does not belong to this category"
                )

        product = await self.repo.create_product(
            seller_id=seller_id,
            title=data.title,
            description=data.description,
            category_id=data.category_id,
            images=[img.model_dump() for img in data.images],
            characteristics=[char.model_dump() for char in data.characteristics],
        )

        await self.session.commit()
        return ProductResponse.model_validate(product)

    async def update_product(
        self,
        seller_id: int,
        product_id: int,
        data: ProductUpdate,
    ) -> ProductResponse:
        product = await self.repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundException("Product not found")

        if product.seller_id != seller_id:
            raise NotOwnerException(
                "Product does not belong to the authenticated seller"
            )

        if product.status == "HARD_BLOCKED":
            raise ForbiddenException("Cannot edit hard-blocked product")

        old_status = product.status
        should_send_event = old_status in ["MODERATED", "BLOCKED"]

        if data.title is not None:
            product.title = data.title
        if data.description is not None:
            product.description = data.description
        if data.category_id is not None:
            product.category_id = data.category_id

        if data.images is not None:
            await self.repo.delete_product_images(product_id)
            for img in data.images:
                await self.repo.add_product_image(product_id, img.model_dump())

        if data.characteristics is not None:
            await self.repo.delete_product_characteristic_values(product_id)
            for char in data.characteristics:
                await self.repo.add_product_characteristic_value(
                    product_id, char.model_dump()
                )

        if should_send_event:
            product.status = "ON_MODERATION"

        self.session.add(product)
        await self.session.commit()

        if should_send_event:
            await self.moderation_service.send_product_edited(
                product_id=product_id, seller_id=seller_id
            )

        return ProductResponse.model_validate(product)