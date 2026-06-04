from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Category, Sku
from src.models.sku_characteristic_value import SkuCharacteristicValue
from src.models.characteristic import Characteristic


class SkuRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_category(self, category_data: dict) -> Category:
        category = Category(**category_data)
        self.session.add(category)
        await self.session.flush()
        return category

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
