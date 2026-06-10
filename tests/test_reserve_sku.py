from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from src.models.category import Category
from src.models.product import Product
from src.models.reservation import Reservation
from src.models.sku import Sku


async def create_sku(test_db, quantity: int):
    category = Category(
        name="Phones",
        slug=f"phones-{uuid4()}",
    )
    test_db.add(category)
    await test_db.flush()

    product = Product(
        title="iPhone",
        category_id=category.id,
        seller_id=uuid4(),
        status="MODERATED",
    )
    test_db.add(product)
    await test_db.flush()

    sku = Sku(
        product_id=product.id,
        name="iPhone 16 Pro",
        article=f"ART-{uuid4()}",
        price=100000,
        stock_quantity=quantity,
        active_quantity=quantity,
        reserved_quantity=0,
    )

    test_db.add(sku)
    await test_db.commit()

    return sku


@pytest.mark.asyncio
async def test_reserve_all_skus_succeeds(async_client, test_db):
    sku1 = await create_sku(test_db, 10)
    sku2 = await create_sku(test_db, 20)

    response = await async_client.post(
        "/api/v1/inventory/reserve",
        json={
            "order_id": str(uuid4()),
            "idempotency_key": str(uuid4()),
            "items": [
                {"sku_id": str(sku1.id), "quantity": 3},
                {"sku_id": str(sku2.id), "quantity": 5},
            ],
        },
    )

    assert response.status_code == 200

    await test_db.refresh(sku1)
    await test_db.refresh(sku2)

    assert sku1.active_quantity == 7
    assert sku1.reserved_quantity == 3

    assert sku2.active_quantity == 15
    assert sku2.reserved_quantity == 5


@pytest.mark.asyncio
async def test_partial_insufficient_stock_returns_409_all_rollback(
    async_client,
    test_db,
):
    sku1 = await create_sku(test_db, 10)
    sku2 = await create_sku(test_db, 1)

    response = await async_client.post(
        "/api/v1/inventory/reserve",
        json={
            "order_id": str(uuid4()),
            "idempotency_key": str(uuid4()),
            "items": [
                {"sku_id": str(sku1.id), "quantity": 3},
                {"sku_id": str(sku2.id), "quantity": 5},
            ],
        },
    )

    assert response.status_code == 409

    await test_db.refresh(sku1)
    await test_db.refresh(sku2)

    assert sku1.active_quantity == 10
    assert sku1.reserved_quantity == 0

    assert sku2.active_quantity == 1
    assert sku2.reserved_quantity == 0

    reservations = (
        await test_db.execute(select(Reservation))
    ).scalars().all()

    assert len(reservations) == 0


@pytest.mark.asyncio
async def test_idempotent_reserve_returns_200_without_double_deduction(
    async_client,
    test_db,
):
    sku = await create_sku(test_db, 10)

    payload = {
        "order_id": str(uuid4()),
        "idempotency_key": str(uuid4()),
        "items": [
            {
                "sku_id": str(sku.id),
                "quantity": 4,
            }
        ],
    }

    first = await async_client.post(
        "/api/v1/inventory/reserve",
        json=payload,
    )

    second = await async_client.post(
        "/api/v1/inventory/reserve",
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    await test_db.refresh(sku)

    assert sku.active_quantity == 6
    assert sku.reserved_quantity == 4

    reservations = (
        await test_db.execute(select(Reservation))
    ).scalars().all()

    assert len(reservations) == 1


@pytest.mark.asyncio
async def test_sku_out_of_stock_event_emitted(
    async_client,
    test_db,
):
    sku = await create_sku(test_db, 3)

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_sku_out_of_stock",
        new_callable=AsyncMock,
    ) as mocked:
        response = await async_client.post(
            "/api/v1/inventory/reserve",
            json={
                "order_id": str(uuid4()),
                "idempotency_key": str(uuid4()),
                "items": [
                    {
                        "sku_id": str(sku.id),
                        "quantity": 3,
                    }
                ],
            },
        )

        assert response.status_code == 200
        mocked.assert_awaited_once()


@pytest.mark.asyncio
async def test_unreserve_restores_quantities(
    async_client,
    test_db,
):
    sku = await create_sku(test_db, 10)

    order_id = uuid4()

    reserve_response = await async_client.post(
        "/api/v1/inventory/reserve",
        json={
            "order_id": str(order_id),
            "idempotency_key": str(uuid4()),
            "items": [
                {
                    "sku_id": str(sku.id),
                    "quantity": 5,
                }
            ],
        },
    )

    assert reserve_response.status_code == 200

    response = await async_client.post(
        "/api/v1/inventory/unreserve",
        json={
            "order_id": str(order_id),
            "items": [],
        },
    )

    assert response.status_code == 200

    await test_db.refresh(sku)

    assert sku.active_quantity == 10
    assert sku.reserved_quantity == 0

    reservation = (
        await test_db.execute(select(Reservation))
    ).scalars().first()

    assert reservation.is_active is False