from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import B2B_TO_B2C_KEY
from src.database.dependencies import (
    get_db,
)
from src.services.product_service import ProductService

router = APIRouter(prefix="/public/products", tags=["Public Catalog"])

async def require_service_key(
    x_service_key: str | None = Header(None, alias="X-Service-Key"),
) -> None:
    if not B2B_TO_B2C_KEY:
        raise HTTPException(
            status_code=500,
            detail={"code": "CONFIG_ERROR", "message": "Service key not configured"},
        )

    if x_service_key != B2B_TO_B2C_KEY:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Invalid service key",
            },
        )

@router.get("/")
async def list_products_catalog(
    ids: list[UUID] | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(require_service_key),
    db: AsyncSession = Depends(get_db),
) -> dict:

    service = ProductService(db)

    return await service.list_products_catalog(
        ids,
        limit,
        offset,
    )