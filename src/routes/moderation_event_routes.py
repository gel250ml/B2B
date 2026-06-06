from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dependencies import get_db, verify_moderation_service_key
from src.schemas.error import ErrorResponse
from src.schemas.moderation_event import ModerationEventRequest, ModerationEventResponse
from src.services.moderation_decision_service import ModerationDecisionService

router = APIRouter(tags=["Moderation Events"])


async def _apply_moderation_event(
    data: ModerationEventRequest,
    db: AsyncSession,
) -> None:
    service = ModerationDecisionService(db)
    await service.apply(data)


@router.post(
    "/events/moderation",
    response_model=ModerationEventResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Invalid service key"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
)
async def apply_moderation_event_flow(
    data: ModerationEventRequest,
    _: None = Depends(verify_moderation_service_key),
    db: AsyncSession = Depends(get_db),
) -> ModerationEventResponse:
    """Canonical-flow endpoint: returns 200 with a small accepted body."""
    await _apply_moderation_event(data, db)
    return ModerationEventResponse()


@router.post(
    "/moderation/events",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Accepted and processed, or duplicate"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Invalid service key"},
        404: {"model": ErrorResponse, "description": "Product not found"},
    },
)
async def apply_moderation_event_openapi(
    data: ModerationEventRequest,
    _: None = Depends(verify_moderation_service_key),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """OpenAPI endpoint: returns 204 without body."""
    await _apply_moderation_event(data, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
