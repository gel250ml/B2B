from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db, get_current_seller_id
from src.services.sku_service import SkuService
from src.schemas.sku import SkuUpdate, SkuResponse, SkuCreate
from src.schemas.error import ErrorResponse

router = APIRouter(
    prefix="/skus",
    tags=["Skus"]
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not fount"},
    },
)
async def create_sku(
        data: SkuCreate,
        seller_id: UUID = Depends(get_current_seller_id),
        db: AsyncSession = Depends(get_db)
) -> SkuResponse:
    service = SkuService(db)
    return await service.create_sku(seller_id, data)


@router.patch(
    "/{sku_id}",
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "SKU not found"},
    },
)
async def update_sku(
        sku_id: UUID,
        data: SkuUpdate,
        seller_id: UUID = Depends(get_current_seller_id),
        db: AsyncSession = Depends(get_db),
) -> SkuResponse:
    service = SkuService(db)
    return await service.update_sku(seller_id, sku_id, data)


@router.delete(
    "skus/{sku_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "SKU not found"},
        409: {"model": ErrorResponse, "description": "Conflict"},
    },
)
async def delete_sku(
        sku_id: UUID,
        seller_id: UUID = Depends(get_current_seller_id),
        db: AsyncSession = Depends(get_db),
):
    service = SkuService(db)
    return await service.delete_sku(seller_id=seller_id, sku_id=sku_id)