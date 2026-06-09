from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import B2C_TO_B2B_KEY
from src.database.dependencies import get_db
from src.schemas.reserve import ReserveRequest, InventoryOrderRequest
from src.services.moderation_event_service import ModerationEventService
from src.services.reserve_service import ReserveService

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)


async def require_service_key(
    x_service_key: str | None = Header(None, alias="X-Service-Key"),
) -> None:
    if not B2C_TO_B2B_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "CONFIG_ERROR",
                "message": "Service key not configured",
            },
        )

    if x_service_key != B2C_TO_B2B_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Invalid or missing X-Service-Key",
            },
        )


def get_reserve_service(
    db: AsyncSession = Depends(get_db),
) -> ReserveService:
    return ReserveService(
        session=db,
        event_service=ModerationEventService(),
    )


@router.post(
    "/reserve",
    dependencies=[Depends(require_service_key)],
)
async def reserve_inventory(
    payload: ReserveRequest,
    service: ReserveService = Depends(get_reserve_service),
):
    service = ReserveService(db)
    ok = await service.reserve(payload)

    if ok is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INSUFFICIENT_STOCK",
                "message": "Not enough stock",
            },
        )

    return {
        "order_id": payload.order_id,
        "status": "RESERVED",
        "reserved_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/unreserve",
    dependencies=[Depends(require_service_key)],
)
async def unreserve_inventory(
    payload: InventoryOrderRequest,
    service: ReserveService = Depends(get_reserve_service),
):
    service = ReserveService(db)
    await service.unreserve(payload.order_id)

    return {
        "order_id": payload.order_id,
        "status": "UNRESERVED",
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
