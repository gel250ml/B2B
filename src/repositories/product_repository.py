from typing import Optional

from sqlalchemy import select
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

    async def get_category_by_id(self, category_id: int) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_characteristic_by_id(self, characteristic_id: int) -> Characteristic | None:
        result = await self.session.execute(
            select(Characteristic).where(Characteristic.id == characteristic_id)
        )
        return result.scalar_one_or_none()

    async def create_product(
        self,
        seller_id: int,
        title: str,
        description: Optional[str],
        category_id: int,
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