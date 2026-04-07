from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db
from src.services.invoice_service import InvoiceService
from src.schemas.invoice import CategoryCreate, CategoryResponse
from src.schemas.error import ErrorResponse

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"]
)


@router.post(
    "/category",
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Category already exists",
        }
    }
)
async def create_category(
        data: CategoryCreate,
        db: AsyncSession = Depends(get_db)
) -> CategoryResponse:
    service = InvoiceService(db)
    return await service.register_category(data)
