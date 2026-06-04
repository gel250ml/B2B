from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db, get_current_seller_id
from src.services.sku_service import SkuService
from src.schemas.sku import CategoryCreate, CategoryResponse, SkuUpdate, SkuResponse
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


@router.patch(
    "/{sku_id}",
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "SKU not found"},
    },
)
async def update_sku(
    sku_id: int,
    data: SkuUpdate,
    seller_id: int = Depends(get_current_seller_id),
    db: AsyncSession = Depends(get_db),
) -> SkuResponse:
    service = SkuService(db)
    return await service.update_sku(seller_id, sku_id, data)
