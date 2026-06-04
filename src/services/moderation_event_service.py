import httpx
from uuid import uuid4
from datetime import datetime, timezone
from src.core.config import MODERATION_URL, B2B_TO_MOD_KEY


class ModerationEventService:
    async def send_product_edited(self, product_id, seller_id) -> None:
        """Send EDITED event to Moderation service."""
        if not MODERATION_URL or not B2B_TO_MOD_KEY:
            return

        payload = {
            "idempotency_key": str(uuid4()),
            "product_id": str(product_id),
            "seller_id": str(seller_id),
            "event": "EDITED",
            "date": datetime.now(timezone.utc).isoformat(),
        }

        headers = {
            "X-Service-Key": B2B_TO_MOD_KEY,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{MODERATION_URL}/api/v1/events/product",
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
            except Exception:
                pass
