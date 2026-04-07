from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db
from src.services.sku_service import SkuService
from src.schemas.sku import CategoryCreate, CategoryResponse
from src.schemas.error import ErrorResponse

router = APIRouter(
    prefix="/skus",
    tags=["Skus"]
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
    service = SkuService(db)
    return await service.register_category(data)
