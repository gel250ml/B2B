from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db, get_current_seller_id
from src.services.product_service import ProductService
from src.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from src.schemas.error import ErrorResponse

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)

# TODO: связь с US-B2B-02 — после создания первого SKU отправить событие CREATED в Moderation:
# POST {moderation_url}/api/v1/events/product
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Category or characteristic not found"},
    },
)
async def create_product(
    data: ProductCreate,
    seller_id: int = Depends(get_current_seller_id),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    service = ProductService(db)
    return await service.create_product(seller_id, data)


@router.patch(
    "/{product_id}",
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    seller_id: UUID = Depends(get_current_seller_id),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    service = ProductService(db)
    return await service.update_product(seller_id, product_id, data)