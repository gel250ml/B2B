from datetime import datetime
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ModerationStatus(StrEnum):
    MODERATED = "MODERATED"
    BLOCKED = "BLOCKED"


class ModerationBlockingReason(BaseModel):
    id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    comment: Optional[str] = None


class ModerationFieldReport(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=50)
    sku_id: Optional[UUID] = None
    comment: str = Field(..., min_length=1)


class ModerationEventRequest(BaseModel):
    """
    Moderation decision event.

    Supports both contracts:
    - canonical flow: status + blocking_reason object
    - OpenAPI: event_type + blocking_reason_id + moderator_comment
    """

    idempotency_key: UUID
    product_id: UUID

    # Flow field.
    status: Optional[ModerationStatus] = None

    # OpenAPI field.
    event_type: Optional[ModerationStatus] = None
    moderator_id: Optional[UUID] = None
    moderator_comment: Optional[str] = None
    blocking_reason_id: Optional[UUID] = None
    occurred_at: Optional[datetime] = None

    hard_block: Optional[bool] = None
    blocking_reason: Optional[ModerationBlockingReason] = None
    field_reports: list[ModerationFieldReport] = Field(default_factory=list)

    @property
    def decision_status(self) -> ModerationStatus:
        return self.event_type or self.status  # type: ignore[return-value]

    @model_validator(mode="after")
    def validate_payload(self):
        if self.status is None and self.event_type is None:
            raise ValueError("status or event_type is required")

        if self.status is not None and self.event_type is not None and self.status != self.event_type:
            raise ValueError("status and event_type must be equal when both are provided")

        if self.decision_status == ModerationStatus.BLOCKED:
            if self.hard_block is None:
                raise ValueError("hard_block is required for BLOCKED event")
            if self.blocking_reason is None and self.blocking_reason_id is None:
                raise ValueError("blocking_reason or blocking_reason_id is required for BLOCKED event")
        return self


class ModerationEventResponse(BaseModel):
    status: str = "accepted"
