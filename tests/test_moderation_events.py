from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import src.database.dependencies as dependencies
from src.models.blocking_reason import BlockingReason
from src.models.category import Category
from src.models.processed_event import ProcessedEvent
from src.models.product import Product
from src.models.product_field_report import ProductFieldReport
from src.models.sku import Sku
from tests.conftest import create_jwt_token

SERVICE_KEY = "moderation-secret"


def service_headers() -> dict[str, str]:
    return {"X-Service-Key": SERVICE_KEY}


def auth_headers(seller_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_jwt_token(seller_id)}"}


@pytest.fixture(autouse=True)
def moderation_service_key(monkeypatch):
    monkeypatch.setattr(dependencies, "MOD_TO_B2B_KEY", SERVICE_KEY)
    monkeypatch.setattr(dependencies, "B2B_TO_MOD_KEY", None)


async def create_product_with_sku(
    test_db: AsyncSession,
    seller_id: UUID,
    status: str = "ON_MODERATION",
) -> tuple[Product, Sku]:
    category = Category(id=uuid4(), name="Electronics", slug=f"electronics-{uuid4()}")
    test_db.add(category)
    await test_db.flush()

    product = Product(
        id=uuid4(),
        title="Product",
        description="Description",
        status=status,
        category_id=category.id,
        seller_id=seller_id,
        deleted=False,
    )
    test_db.add(product)
    await test_db.flush()

    sku = Sku(
        id=uuid4(),
        product_id=product.id,
        name="SKU",
        article=f"SKU-{uuid4()}",
        price=10000,
        discount=0,
        cost_price=7000,
        stock_quantity=10,
        active_quantity=5,
        reserved_quantity=0,
        deleted=False,
    )
    test_db.add(sku)
    await test_db.commit()
    return product, sku


async def get_product(test_db: AsyncSession, product_id: UUID) -> Product:
    result = await test_db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one()
    await test_db.refresh(product)
    return product


async def count_field_reports(test_db: AsyncSession, product_id: UUID) -> int:
    result = await test_db.execute(
        select(func.count(ProductFieldReport.id)).where(
            ProductFieldReport.product_id == product_id
        )
    )
    return result.scalar_one()


@pytest.mark.asyncio
async def test_moderated_event_clears_blocking_data(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product, _ = await create_product_with_sku(test_db, seller_id, "BLOCKED")
    reason = BlockingReason(
        id=uuid4(),
        title="Bad description",
        description="Old comment",
    )
    product.blocking_reason_id = reason.id
    product.moderator_comment = "Old moderator comment"
    test_db.add(reason)
    test_db.add(product)
    test_db.add(
        ProductFieldReport(
            product_id=product.id,
            field_name="description",
            sku_id=None,
            comment="Old field report",
        )
    )
    await test_db.commit()

    response = await async_client.post(
        "/api/v1/events/moderation",
        json={
            "idempotency_key": str(uuid4()),
            "product_id": str(product.id),
            "status": "MODERATED",
        },
        headers=service_headers(),
    )

    assert response.status_code == 200
    product = await get_product(test_db, product.id)
    assert product.status == "MODERATED"
    assert product.blocking_reason_id is None
    assert product.moderator_comment is None
    assert await count_field_reports(test_db, product.id) == 0


@pytest.mark.asyncio
async def test_blocked_soft_saves_field_reports(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product, sku = await create_product_with_sku(test_db, seller_id)
    reason_id = uuid4()
    key = uuid4()

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_blocked_to_b2c",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.post(
            "/api/v1/events/moderation",
            json={
                "idempotency_key": str(key),
                "product_id": str(product.id),
                "status": "BLOCKED",
                "hard_block": False,
                "blocking_reason": {
                    "id": str(reason_id),
                    "title": "Описание не соответствует товару",
                    "comment": "Несоответствие описания и фотографий",
                },
                "field_reports": [
                    {
                        "field_name": "description",
                        "sku_id": None,
                        "comment": "Текст описания скопирован с другого товара",
                    }
                ],
            },
            headers=service_headers(),
        )

    assert response.status_code == 200
    product = await get_product(test_db, product.id)
    assert product.status == "BLOCKED"
    assert product.blocking_reason_id == reason_id
    assert product.moderator_comment == "Несоответствие описания и фотографий"
    assert await count_field_reports(test_db, product.id) == 1
    mock_send.assert_awaited_once_with(
        product_id=product.id,
        sku_ids=[sku.id],
        source_idempotency_key=key,
        reason="Описание не соответствует товару",
    )


@pytest.mark.asyncio
async def test_blocked_hard_sets_terminal_status(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product, sku = await create_product_with_sku(test_db, seller_id)
    product_id = product.id
    sku_id = sku.id
    key = uuid4()

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_blocked_to_b2c",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.post(
            "/api/v1/events/moderation",
            json={
                "idempotency_key": str(key),
                "product_id": str(product.id),
                "status": "BLOCKED",
                "hard_block": True,
                "blocking_reason": {
                    "id": str(uuid4()),
                    "title": "Грубое нарушение правил",
                    "comment": "Товар нельзя продавать",
                },
                "field_reports": [],
            },
            headers=service_headers(),
        )

    assert response.status_code == 200
    product = await get_product(test_db, product.id)
    assert product.status == "HARD_BLOCKED"
    assert product.moderator_comment == "Товар нельзя продавать"
    mock_send.assert_awaited_once_with(
        product_id=product.id,
        sku_ids=[sku.id],
        source_idempotency_key=key,
        reason="Грубое нарушение правил",
    )


@pytest.mark.asyncio
async def test_hard_blocked_product_rejects_seller_edits(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product, _ = await create_product_with_sku(test_db, seller_id, "HARD_BLOCKED")

    put_response = await async_client.put(
        f"/api/v1/products/{product.id}",
        json={"title": "New title"},
        headers=auth_headers(seller_id),
    )
    delete_response = await async_client.delete(
        f"/api/v1/products/{product.id}",
        headers=auth_headers(seller_id),
    )

    assert put_response.status_code == 403
    assert put_response.json()["code"] == "FORBIDDEN"
    assert delete_response.status_code == 403
    assert delete_response.json()["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_duplicate_event_same_idempotency_key_no_side_effects(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product, sku = await create_product_with_sku(test_db, seller_id)
    product_id = product.id
    sku_id = sku.id
    key = uuid4()
    payload = {
        "idempotency_key": str(key),
        "product_id": str(product_id),
        "status": "BLOCKED",
        "hard_block": False,
        "blocking_reason": {
            "id": str(uuid4()),
            "title": "Описание не соответствует товару",
            "comment": "Первое решение",
        },
        "field_reports": [
            {
                "field_name": "description",
                "sku_id": None,
                "comment": "Первое замечание",
            }
        ],
    }

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_blocked_to_b2c",
        new_callable=AsyncMock,
    ) as mock_send:
        first_response = await async_client.post(
            "/api/v1/events/moderation",
            json=payload,
            headers=service_headers(),
        )
        second_payload = {
            **payload,
            "status": "MODERATED",
        }
        second_response = await async_client.post(
            "/api/v1/events/moderation",
            json=second_payload,
            headers=service_headers(),
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    product = await get_product(test_db, product_id)
    assert product.status == "BLOCKED"
    assert product.moderator_comment == "Первое решение"
    assert await count_field_reports(test_db, product_id) == 1
    mock_send.assert_awaited_once_with(
        product_id=product_id,
        sku_ids=[sku_id],
        source_idempotency_key=key,
        reason="Описание не соответствует товару",
    )

    result = await test_db.execute(select(func.count(ProcessedEvent.id)))
    assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_missing_service_key_returns_401(
    async_client: httpx.AsyncClient,
):
    response = await async_client.post(
        "/api/v1/events/moderation",
        json={
            "idempotency_key": str(uuid4()),
            "product_id": str(uuid4()),
            "status": "MODERATED",
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_openapi_moderation_events_accepts_event_type_and_returns_204(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product, sku = await create_product_with_sku(test_db, seller_id)
    reason_id = uuid4()
    key = uuid4()

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_blocked_to_b2c",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.post(
            "/api/v1/moderation/events",
            json={
                "idempotency_key": str(key),
                "product_id": str(product.id),
                "event_type": "BLOCKED",
                "moderator_id": str(uuid4()),
                "moderator_comment": "Описание не соответствует товару",
                "blocking_reason_id": str(reason_id),
                "hard_block": False,
                "field_reports": [
                    {
                        "field_name": "description",
                        "sku_id": None,
                        "comment": "Плохое описание",
                    }
                ],
                "occurred_at": "2026-06-06T20:53:15.487Z",
            },
            headers=service_headers(),
        )

    assert response.status_code == 204
    assert response.content == b""

    product = await get_product(test_db, product.id)
    assert product.status == "BLOCKED"
    assert product.blocking_reason_id == reason_id
    assert product.moderator_comment == "Описание не соответствует товару"
    assert await count_field_reports(test_db, product.id) == 1
    mock_send.assert_awaited_once_with(
        product_id=product.id,
        sku_ids=[sku.id],
        source_idempotency_key=key,
        reason="Описание не соответствует товару",
    )
