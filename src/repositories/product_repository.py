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

    async def get_characteristic_by_name(
        self,
        name: str,
        category_id: UUID | None = None,
    ) -> Characteristic | None:
        stmt = select(Characteristic).where(Characteristic.name == name)
        if category_id is not None:
            stmt = stmt.where(Characteristic.category_id == category_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _product_options(self):
        return (
            selectinload(Product.images),
            selectinload(Product.characteristic_values).selectinload(
                ProductCharacteristicValue.characteristic
            ),
            selectinload(Product.skus),
        )

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

        await self.replace_product_images(product.id, images)
        await self.replace_product_characteristics(product.id, characteristics)
        await self.session.flush()

        product_with_relations = await self.get_product_with_relations_by_id(product.id)
        assert product_with_relations is not None
        return product_with_relations

    async def get_product_by_id(self, product_id: UUID) -> Product | None:
        return await self.get_product_with_relations_by_id(product_id)

    async def get_product_with_relations_by_id(self, product_id: UUID) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product_id, Product.deleted.is_(False))
            .options(*self._product_options())
        )
        return result.scalar_one_or_none()

    async def replace_product_images(self, product_id: UUID, images: list[dict]) -> None:
        await self.session.execute(
            delete(ProductImage).where(ProductImage.product_id == product_id)
        )
        for image in images:
            self.session.add(
                ProductImage(
                    product_id=product_id,
                    url=image["url"],
                    ordering=image.get("ordering", 0),
                )
            )

    async def replace_product_characteristics(
        self,
        product_id: UUID,
        characteristics: list[dict],
    ) -> None:
        await self.session.execute(
            delete(ProductCharacteristicValue).where(
                ProductCharacteristicValue.product_id == product_id
            )
        )
        for characteristic in characteristics:
            self.session.add(
                ProductCharacteristicValue(
                    product_id=product_id,
                    characteristic_id=characteristic["characteristic_id"],
                    value=characteristic["value"],
                )
            )
