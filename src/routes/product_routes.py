from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import B2C_TO_B2B_KEY
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
from fastapi import HTTPException

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


from src.database.dependencies import seller_id_from_authorization


@router.get("", responses={401: {"model": ErrorResponse, "description": "Unauthorized"}})
async def list_products(
    ids: str | None = Query(None, description="Comma-separated UUIDs (B2C catalog only)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
    search: str | None = Query(None),
    x_service_key: str | None = Header(None, alias="X-Service-Key"),
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = ProductService(db)

    if x_service_key is not None:
        if not B2C_TO_B2B_KEY or x_service_key != B2C_TO_B2B_KEY:
            raise HTTPException(
                status_code=401,
                detail={"code": "UNAUTHORIZED", "message": "Invalid X-Service-Key"},
            )
        parsed_ids: list[UUID] | None = None
        if ids:
            try:
                parsed_ids = [UUID(i.strip()) for i in ids.split(",") if i.strip()]
            except ValueError:
                raise ValidationException("ids must be valid UUIDs")
        return await service.list_products_catalog(parsed_ids, limit, offset)

    seller_id = seller_id_from_authorization(authorization)
    return await service.list_products_seller(seller_id, status, search, limit, offset)


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