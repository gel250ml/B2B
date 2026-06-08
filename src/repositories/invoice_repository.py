from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Category, Invoice, InvoiceItem, Sku


class InvoiceRepository:
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

    async def get_skus_with_products(self, sku_ids: list[UUID]) -> list[Sku]:
        result = await self.session.execute(
            select(Sku)
            .options(selectinload(Sku.product))
            .where(Sku.id.in_(sku_ids), Sku.deleted.is_(False))
        )
        return list(result.scalars().all())

    async def create_invoice(
            self,
            seller_id: UUID,
            items_data: list[dict],
    ) -> Invoice:
        invoice = Invoice(seller_id=seller_id, status="CREATED")
        self.session.add(invoice)
        await self.session.flush()

        for item_data in items_data:
            self.session.add(
                InvoiceItem(
                    invoice_id=invoice.id,
                    **item_data
                )
            )

        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(invoice, attribute_names=["items"])
        return invoice