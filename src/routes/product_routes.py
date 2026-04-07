from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db
from src.services.product_service import ProductService
from src.schemas.product import CategoryCreate, CategoryResponse
from src.schemas.error import ErrorResponse

router = APIRouter(
    prefix="/products",
    tags=["Products"]
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
    service = ProductService(db)
    return await service.register_category(data)
