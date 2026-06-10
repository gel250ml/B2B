from fastapi import APIRouter, Depends, HTTPException, status

from src.schemas.reserve import ReserveRequest, InventoryOrderRequest
from src.services.reserve_service import ReserveService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependencies import get_db
from src.services.moderation_event_service import ModerationEventService


def get_reserve_service(
    session: AsyncSession = Depends(get_db),
):
    event_service = ModerationEventService()
    return ReserveService(session, event_service)
router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)

@router.post("/reserve")
async def reserve_inventory(
    payload: ReserveRequest,
    service: ReserveService = Depends(get_reserve_service),
):
    ok = await service.reserve(payload)

    if ok is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INSUFFICIENT_STOCK",
                "message": "Not enough stock",
            },
        )

    return {"status": "RESERVED", "order_id": payload.order_id}


@router.post("/unreserve")
async def unreserve_inventory(
    payload: InventoryOrderRequest,
    service: ReserveService = Depends(get_reserve_service),
):
    await service.unreserve(payload.order_id)
    return {"status": "UNRESERVED", "order_id": payload.order_id}