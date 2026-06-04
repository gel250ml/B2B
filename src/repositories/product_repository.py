from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.product import Product
from src.models.product_image import ProductImage
from src.models.product_characteristic_value import ProductCharacteristicValue
from src.models.category import Category
from src.models.characteristic import Characteristic


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_category_by_id(self, category_id: UUID) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_characteristic_by_id(self, characteristic_id: UUID) -> Characteristic | None:
        result = await self.session.execute(
            select(Characteristic).where(Characteristic.id == characteristic_id)
        )
        return result.scalar_one_or_none()

    async def get_characteristic_by_name(self, name: str) -> Characteristic | None:
        result = await self.session.execute(
            select(Characteristic).where(Characteristic.name == name)
        )
        return result.scalar_one_or_none()

    async def create_product(
        self,
        seller_id: UUID,
        title: str,
        description: Optional[str],
        category_id: UUID,
        images: list[dict],
        characteristics: list[dict],
    ) -> Product:
        product = Product(
            seller_id=seller_id,
            title=title,
            description=description,
            category_id=category_id,
            status="CREATED",
            deleted=False,
        )
        self.session.add(product)
        await self.session.flush()

        for img in images:
            self.session.add(ProductImage(
                product_id=product.id,
                url=img["url"],
                ordering=img.get("ordering", 0),
            ))

        for char in characteristics:
            self.session.add(ProductCharacteristicValue(
                product_id=product.id,
                characteristic_id=char["characteristic_id"],
                value=char["value"],
            ))

        await self.session.flush()

        result = await self.session.execute(
            select(Product)
            .where(Product.id == product.id)
            .options(
                selectinload(Product.images),
                selectinload(Product.characteristic_values),
                selectinload(Product.skus),
            )
        )
        return result.scalar_one()

    async def get_product_by_id(self, product_id: UUID) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_product_with_relations_by_id(self, product_id: UUID) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.images),
                selectinload(Product.characteristic_values),
                selectinload(Product.skus),
            )
        )
        return result.scalar_one_or_none()

    async def delete_product_images(self, product_id: UUID) -> None:
        await self.session.execute(
            delete(ProductImage).where(ProductImage.product_id == product_id)
        )

    async def delete_product_characteristic_values(self, product_id: UUID) -> None:
        await self.session.execute(
            delete(ProductCharacteristicValue).where(
                ProductCharacteristicValue.product_id == product_id
            )
        )

    async def add_product_image(self, product_id: UUID, image: dict) -> None:
        self.session.add(ProductImage(
            product_id=product_id,
            url=image["url"],
            ordering=image.get("ordering", 0),
        ))

    async def add_product_characteristic_value(
        self,
        product_id: UUID,
        characteristic_id: UUID,
        value: str,
    ) -> None:
        self.session.add(ProductCharacteristicValue(
            product_id=product_id,
            characteristic_id=characteristic_id,
            value=value,
        ))
