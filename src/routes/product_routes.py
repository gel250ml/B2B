from uuid import UUID

from fastapi import APIRouter, Depends, Response, status, Header, HTTPException, Query
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
from src.core.config import B2B_TO_B2C_KEY

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)

async def require_service_key(
    x_service_key: str | None = Header(
        None,
        alias="X-Service-Key",
    ),
) -> None:
    if x_service_key != B2B_TO_B2C_KEY:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Invalid service key",
            },
        )

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

@router.get("")
async def list_products_catalog(
    ids: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(require_service_key),
    db: AsyncSession = Depends(get_db),
) -> dict:

    parsed_ids = None

    if ids:
        try:
            parsed_ids = [
                UUID(item.strip())
                for item in ids.split(",")
                if item.strip()
            ]
        except ValueError:
            raise ValidationException(
                "ids must contain valid UUID values"
            )

    service = ProductService(db)

    return await service.list_products_catalog(
        parsed_ids,
        limit,
        offset,
    )

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

@router.put(
    "/{product_id}",
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
)
async def put_product(
    product_id: UUID,
    data: ProductUpdate,
    seller_id: UUID = Depends(get_current_seller_id),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    service = ProductService(db)
    return await service.update_product(seller_id, product_id, data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
)
async def delete_product(
    product_id: UUID,
    seller_id: UUID = Depends(get_current_seller_id),
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = ProductService(db)
    await service.delete_product(seller_id, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

