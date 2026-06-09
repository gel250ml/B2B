from uuid import UUID

from sqlalchemy import delete, select, exists, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Category, Sku, Product, ProductCharacteristicValue, SkuImage
from src.models.sku_characteristic_value import SkuCharacteristicValue
from src.models.characteristic import Characteristic
from src.schemas.sku import SkuCreate


class SkuRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

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

    def _sku_options(self):
        return (
            selectinload(Sku.product),
            selectinload(Sku.images),
            selectinload(Sku.characteristic_values).selectinload(
                SkuCharacteristicValue.characteristic
            ),
        )

    async def get_sku_with_product(self, sku_id: UUID) -> Sku | None:
        result = await self.session.execute(
            select(Sku)
            .where(Sku.id == sku_id, Sku.deleted.is_(False))
            .options(*self._sku_options())
        )
        return result.scalar_one_or_none()

    async def replace_sku_characteristics(
            self,
            sku_id: UUID,
            characteristics: list[dict],
    ) -> None:
        await self.session.execute(
            delete(SkuCharacteristicValue).where(SkuCharacteristicValue.sku_id == sku_id)
        )
        for characteristic in characteristics:
            self.session.add(
                SkuCharacteristicValue(
                    sku_id=sku_id,
                    characteristic_id=characteristic["characteristic_id"],
                    value=characteristic["value"],
                )
            )

    async def get_product_by_id(self, product_id: UUID) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product_id, Product.deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def has_skus(self, product_id: UUID) -> bool:
        result = await self.session.scalar(
            select(
                exists().where(
                    Sku.product_id == product_id,
                    Sku.deleted.is_(False),
                )
            )
        )
        return result

    async def count_skus(self, product_id: UUID) -> int:
        result = await self.session.scalar(
            select(func.count())
            .select_from(Sku)
            .where(
                Sku.product_id == product_id,
                Sku.deleted.is_(False),
            )
        )
        return result or 0

    async def create_sku(
            self,
            product_id: UUID,
            name: str,
            article: str | None,
            price: int,
            discount: int,
            cost_price: int,
            characteristics: list[dict],
            images: list[dict],
            stock_quantity: int = 0,
            active_quantity: int = 0,
            reserved_quantity: int = 0,
    ) -> Sku:
        sku = Sku(
            product_id=product_id,
            name=name,
            article=article,
            price=price,
            discount=discount,
            cost_price=cost_price,
            stock_quantity=stock_quantity,
            active_quantity=active_quantity,
            reserved_quantity=reserved_quantity,
            deleted=False,
        )

        self.session.add(sku)

        await self.session.flush()
        await self.session.refresh(sku)

        await self.create_sku_characteristics(sku_id=sku.id, characteristics=characteristics)
        await self.create_sku_images(sku_id=sku.id, images=images)
        await self.session.flush()
        return sku

    async def create_sku_characteristics(
            self,
            sku_id: UUID,
            characteristics: list[dict],
    ) -> None:
        for characteristic in characteristics:
            self.session.add(
                SkuCharacteristicValue(
                    sku_id=sku_id,
                    characteristic_id=characteristic["characteristic_id"],
                    value=characteristic["value"],
                )
            )

    async def create_sku_images(
            self,
            sku_id: UUID,
            images: list[dict]
    ) -> None:
        for image in images:
            self.session.add(
                SkuImage(
                    sku_id=sku_id,
                    url=image["url"],
                    ordering=image.get("ordering", 0),
                )
            )
