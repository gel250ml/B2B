from fastapi import APIRouter, Depends, HTTPException, status

from src.schemas.reserve import ReserveRequest, InventoryOrderRequest
from src.services.reserve_service import ReserveService

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)

@router.post("/reserve")
async def reserve_inventory(
    payload: ReserveRequest,
    service: ReserveService = Depends(),
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
    service: ReserveService = Depends(),
):
    await service.unreserve(payload.order_id)
    return {"status": "UNRESERVED", "order_id": payload.order_id}