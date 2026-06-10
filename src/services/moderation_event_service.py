from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import httpx

from src.core.config import B2B_TO_B2C_KEY, B2B_TO_MOD_KEY, B2C_URL, MODERATION_URL


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class ModerationEventService:
    async def send_product_edited(self, product_id, seller_id, event: str = "EDITED") -> None:
        """
        Legacy B2B -> Moderation sender.

        US-B2B-09 does not depend on this method. It is kept as best-effort
        compatibility with the older flow.
        """
        if not MODERATION_URL or not B2B_TO_MOD_KEY:
            return

        payload = {
            "idempotency_key": str(uuid4()),
            "product_id": str(product_id),
            "seller_id": str(seller_id),
            "event": event,
            "date": _utc_now_iso(),
        }

        headers = {
            "X-Service-Key": B2B_TO_MOD_KEY,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{MODERATION_URL.rstrip('/')}/api/v1/events/product",
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
            except Exception:
                pass

    async def send_product_blocked_to_b2c(
        self,
        product_id: UUID,
        sku_ids: list[UUID],
        source_idempotency_key: UUID,
        reason: str | None = None,
    ) -> None:
        """Send PRODUCT_BLOCKED cascade event to B2C Orders service."""
        if not B2C_URL or not B2B_TO_B2C_KEY:
            return

        payload = {
            "event_type": "PRODUCT_BLOCKED",
            "idempotency_key": str(
                uuid5(NAMESPACE_URL, f"b2b:b2c:product-blocked:{source_idempotency_key}")
            ),
            "occurred_at": _utc_now_iso(),
            "payload": {
                "product_id": str(product_id),
                "reason": reason,
            },
        }

        headers = {
            "X-Service-Key": B2B_TO_B2C_KEY,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{B2C_URL.rstrip('/')}/api/v1/b2b/events",
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
                # 202 = accepted, 409 = B2C has already processed the same idempotency key.
                if response.status_code in (202, 409):
                    return
            except Exception:
                pass

    async def send_product_deleted_to_b2c(self, product_id: UUID, sku_ids: list[UUID]) -> None:
        if not B2C_URL or not B2B_TO_B2C_KEY:
            return
        payload = {
            "event_type": "PRODUCT_DELETED",
            "idempotency_key": str(uuid4()),
            "occurred_at": _utc_now_iso(),
            "payload": {
                "product_id": str(product_id),
                "sku_ids": [str(s) for s in sku_ids],
            },
        }
        headers = {"X-Service-Key": B2B_TO_B2C_KEY, "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            try:
                await client.post(f"{B2C_URL.rstrip('/')}/api/v1/events/product", json=payload, headers=headers,
                                  timeout=10.0)
            except Exception:
                pass

    async def send_sku_out_of_stock(self, sku_id: UUID, product_id: UUID) -> None:
        if not B2C_URL or not B2B_TO_B2C_KEY:
            return

        payload = {
            "event_type": "SKU_OUT_OF_STOCK",
            "idempotency_key": str(uuid4()),
            "occurred_at": _utc_now_iso(),
            "payload": {
                "sku_id": str(sku_id),
                "product_id": str(product_id),
            },
        }

        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{B2C_URL.rstrip('/')}/api/v1/b2b/events",
                    json=payload,
                    headers={"X-Service-Key": B2B_TO_B2C_KEY},
                    timeout=10.0,
                )
            except Exception:
                pass

    async def send_product_deleted_to_moderation(self, product_id: UUID) -> None:
        if not MODERATION_URL or not B2B_TO_MOD_KEY:
            return
        payload = {
            "event_type": "PRODUCT_DELETED",
            "idempotency_key": str(uuid4()),
            "occurred_at": _utc_now_iso(),
            "payload": {
                "product_id": str(product_id),
            },
        }
        headers = {"X-Service-Key": B2B_TO_MOD_KEY, "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{MODERATION_URL.rstrip('/')}/api/v1/events/product",
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
            except Exception:
                pass
