from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundException
from src.models.blocking_reason import BlockingReason
from src.models.processed_event import ProcessedEvent
from src.models.product import Product
from src.models.product_field_report import ProductFieldReport
from src.schemas.moderation_event import ModerationEventRequest, ModerationStatus
from src.services.moderation_event_service import ModerationEventService


class ModerationDecisionService:
    SENDER_SERVICE = "moderation"

    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = ModerationEventService()

    async def apply(self, data: ModerationEventRequest) -> bool:
        product = await self._get_product(data.product_id)
        if product is None:
            raise NotFoundException("Product not found")

        if not await self._try_register_event(data.idempotency_key):
            return False

        sku_ids_for_b2c: list[UUID] = []

        if data.decision_status == ModerationStatus.MODERATED:
            await self._apply_moderated(product)
        else:
            sku_ids_for_b2c = [
                sku.id
                for sku in product.skus
                if not sku.deleted and sku.active_quantity > 0
            ]
            await self._apply_blocked(product, data)

        await self.session.commit()

        if data.decision_status == ModerationStatus.BLOCKED and sku_ids_for_b2c:
            await self.events.send_product_blocked_to_b2c(
                product_id=product.id,
                sku_ids=sku_ids_for_b2c,
                source_idempotency_key=data.idempotency_key,
                reason=self._cascade_reason(data),
            )

        return True

    async def _get_product(self, product_id: UUID) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product_id, Product.deleted.is_(False))
            .options(selectinload(Product.skus))
        )
        return result.scalar_one_or_none()

    async def _try_register_event(self, idempotency_key: UUID) -> bool:
        self.session.add(
            ProcessedEvent(
                sender_service=self.SENDER_SERVICE,
                idempotency_key=idempotency_key,
            )
        )
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            return False
        return True

    async def _apply_moderated(self, product: Product) -> None:
        product.status = "MODERATED"
        product.blocking_reason_id = None
        product.moderator_comment = None
        await self._delete_field_reports(product.id)
        self.session.add(product)

    async def _apply_blocked(self, product: Product, data: ModerationEventRequest) -> None:
        reason = await self._resolve_blocking_reason(data)

        product.status = "HARD_BLOCKED" if data.hard_block else "BLOCKED"
        product.blocking_reason_id = reason.id
        product.moderator_comment = self._moderator_comment(data)

        await self._delete_field_reports(product.id)
        for report in data.field_reports:
            self.session.add(
                ProductFieldReport(
                    product_id=product.id,
                    field_name=report.field_name,
                    sku_id=report.sku_id,
                    comment=report.comment,
                )
            )

        self.session.add(product)

    async def _resolve_blocking_reason(self, data: ModerationEventRequest) -> BlockingReason:
        if data.blocking_reason is not None:
            return await self._upsert_blocking_reason(
                reason_id=data.blocking_reason.id,
                title=data.blocking_reason.title,
                description=data.blocking_reason.comment,
            )

        assert data.blocking_reason_id is not None
        result = await self.session.execute(
            select(BlockingReason).where(BlockingReason.id == data.blocking_reason_id)
        )
        reason = result.scalar_one_or_none()
        if reason is not None:
            return reason

        # OpenAPI sends only blocking_reason_id + moderator_comment.
        # If the dictionary has not been seeded in B2B, create a safe placeholder
        # to keep the FK valid and still preserve the moderator comment on Product.
        return await self._upsert_blocking_reason(
            reason_id=data.blocking_reason_id,
            title=data.moderator_comment or "Moderation blocking reason",
            description=data.moderator_comment,
        )

    async def _upsert_blocking_reason(
        self,
        reason_id: UUID,
        title: str,
        description: str | None,
    ) -> BlockingReason:
        result = await self.session.execute(
            select(BlockingReason).where(BlockingReason.id == reason_id)
        )
        reason = result.scalar_one_or_none()
        if reason is None:
            reason = BlockingReason(
                id=reason_id,
                title=title,
                description=description,
            )
        else:
            reason.title = title
            reason.description = description

        self.session.add(reason)
        await self.session.flush()
        return reason

    async def _delete_field_reports(self, product_id: UUID) -> None:
        await self.session.execute(
            delete(ProductFieldReport).where(ProductFieldReport.product_id == product_id)
        )

    @staticmethod
    def _moderator_comment(data: ModerationEventRequest) -> str | None:
        if data.moderator_comment is not None:
            return data.moderator_comment
        if data.blocking_reason is not None:
            return data.blocking_reason.comment
        return None

    @staticmethod
    def _cascade_reason(data: ModerationEventRequest) -> str | None:
        if data.blocking_reason is not None:
            return data.blocking_reason.title
        return data.moderator_comment
