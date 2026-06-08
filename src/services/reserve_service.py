from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.sku import Sku
from src.models.reservation import Reservation
from src.services.moderation_event_service import ModerationEventService
from src.schemas.reserve import ReserveRequest


class ReserveService:

    def __init__(self, session: AsyncSession, event_service: ModerationEventService):
        self.session = session
        self.event_service = event_service

    async def reserve(self, data: ReserveRequest):

        existing = await self.session.execute(
            select(Reservation).where(
                Reservation.idempotency_key == data.idempotency_key
            )
        )
        if existing.scalars().first():
            return True  # уже выполнено

        sku_ids = [i.sku_id for i in data.items]

        stmt = (
            select(Sku)
            .where(Sku.id.in_(sku_ids))
            .with_for_update()
        )

        result = await self.session.execute(stmt)
        skus = {s.id: s for s in result.scalars().all()}

        for item in data.items:
            sku = skus.get(item.sku_id)

            if not sku or sku.active_quantity < item.quantity:
                await self.session.rollback()
                return None  # в роуте → 409

        for item in data.items:
            sku = skus[item.sku_id]

            sku.active_quantity -= item.quantity
            sku.reserved_quantity += item.quantity

            self.session.add(
                Reservation(
                    idempotency_key=data.idempotency_key,
                    order_id=data.order_id,
                    sku_id=item.sku_id,
                    quantity=item.quantity,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                )
            )

        await self.session.commit()

        for sku in skus.values():
            if sku.active_quantity == 0:
                await self.event_service.send_sku_out_of_stock(
                    sku_id=sku.id,
                    product_id=sku.product_id,
                )

        return True

    async def unreserve(self, order_id: UUID):

        result = await self.session.execute(
            select(Reservation).where(
                Reservation.order_id == order_id,
                Reservation.is_active.is_(True),
            )
        )

        reservations = result.scalars().all()

        if not reservations:
            return True

        sku_ids = [r.sku_id for r in reservations]

        skus_result = await self.session.execute(
            select(Sku).where(Sku.id.in_(sku_ids)).with_for_update()
        )

        skus = {s.id: s for s in skus_result.scalars().all()}

        for r in reservations:
            sku = skus[r.sku_id]

            sku.active_quantity += r.quantity
            sku.reserved_quantity -= r.quantity

            r.is_active = False

        await self.session.commit()

        return True