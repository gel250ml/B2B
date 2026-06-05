from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db, get_current_seller_id
from src.services.invoice_service import InvoiceService
from src.schemas.invoice import CategoryCreate, CategoryResponse, InvoiceCreate, InvoiceResponse
from src.schemas.error import ErrorResponse

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        403: {"model": ErrorResponse, "description": "One or more SKUs do not belong to seller"},
        404: {"model": ErrorResponse, "description": "SKU not found"},
    },
)
async def create_invoice(
    data: InvoiceCreate,
    seller_id: UUID = Depends(get_current_seller_id),
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    # TODO: когда появится отдельный сервис склада/поставок, здесь нужно будет отправлять событие
    # о создании накладной или вызывать его API. Сейчас создание выполняется локально в БД.
    service = InvoiceService(db)
    return await service.create_invoice(seller_id, data)


@router.post(
    "/category",
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Category already exists",
        }
    },
)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    service = InvoiceService(db)
    return await service.register_category(data)
