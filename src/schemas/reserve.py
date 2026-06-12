from uuid import UUID
from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    sku_id: UUID
    quantity: int = Field(gt=0)


class ReserveRequest(BaseModel):
    idempotency_key: UUID
    order_id: UUID
    items: list[InventoryItem]


class ReserveResponse(BaseModel):
    order_id: UUID
    status: str = "RESERVED"
    reserved_at: str


class InventoryOrderRequest(BaseModel):
    order_id: UUID
    items: list[InventoryItem]


class InventoryOrderResponse(BaseModel):
    order_id: UUID
    status: str
    processed_at: str

