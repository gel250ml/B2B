from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.invoice_repository import InvoiceRepository
from src.schemas.invoice import CategoryCreate, CategoryResponse, InvoiceCreate, InvoiceResponse
from src.core.exceptions import ConflictException, NotFoundException, NotOwnerException, ValidationException


class InvoiceService:
    def __init__(self, session: AsyncSession):
        self.repo = InvoiceRepository(session)
        self.session = session

    async def register_category(self, data: CategoryCreate) -> CategoryResponse:
        try:
            category_dict = data.model_dump()

            category = await self.repo.create_category(category_dict)

            await self.session.commit()
            return CategoryResponse.model_validate(category)
        except IntegrityError:
            await self.session.rollback()
            raise ConflictException("Category with this slug already exists")

    async def create_invoice(self, seller_id: UUID, data: InvoiceCreate) -> InvoiceResponse:
        self._validate_create_request(data)

        requested_sku_ids = [item.sku_id for item in data.items]
        unique_sku_ids = list(dict.fromkeys(requested_sku_ids))
        skus = await self.repo.get_skus_with_products(unique_sku_ids)
        skus_by_id = {sku.id: sku for sku in skus}

        if len(skus_by_id) != len(unique_sku_ids):
            raise NotFoundException("SKU not found")

        if any(sku.product.seller_id != seller_id for sku in skus):
            raise NotOwnerException("One or more SKUs do not belong to the authenticated seller")

        if any(sku.product.status != "MODERATED" for sku in skus):
            raise ValidationException("Invoice can only be created for MODERATED products")

        items_data = [
            {
                "sku_id": item.sku_id,
                "quantity": item.quantity,
                "sku_name": skus_by_id[item.sku_id].name,
                "accepted_quantity": None,
            }
            for item in data.items
        ]

        try:
            invoice = await self.repo.create_invoice(seller_id=seller_id, items_data=items_data)
            await self.session.commit()
            return InvoiceResponse.model_validate(invoice)
        except IntegrityError:
            await self.session.rollback()
            raise ValidationException("Invalid invoice items")

    @staticmethod
    def _validate_create_request(data: InvoiceCreate) -> None:
        if not data.items:
            raise ValidationException("At least one item is required")

        if any(item.quantity <= 0 for item in data.items):
            raise ValidationException("quantity must be > 0")
