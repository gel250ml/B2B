from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import (
    ProductAccessContext,
    get_db,
    get_current_seller_id,
    get_product_access_context,
)
from src.services.product_service import ProductService
from src.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from src.schemas.error import ErrorResponse
from src.core.exceptions import ValidationException

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
    seller_id: UUID = Depends(get_current_seller_id),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    service = ProductService(db)
    return await service.create_product(seller_id, data)


@router.get(
    "/{product_id}",
    responses={
        200: {"description": "Product detail"},
        400: {"model": ErrorResponse, "description": "Invalid product id"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
)
async def get_product(
    product_id: str,
    access: ProductAccessContext = Depends(get_product_access_context),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        parsed_product_id = UUID(product_id)
    except ValueError:
        raise ValidationException("id must be a valid UUID")

    service = ProductService(db)
    return await service.get_product_detail(access, parsed_product_id)


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