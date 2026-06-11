from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from src.models.category import Category
from src.models.product import Product
from src.models.sku import Sku
from tests.conftest import create_jwt_token


async def create_product_with_sku(
        test_db,
        seller_id,
        *,
        product_status="MODERATED",
        active_quantity=10,
        reserved_quantity=0,
):
    category = Category(
        name="Phones",
        slug=f"phones-{uuid4()}",
    )
    test_db.add(category)
    await test_db.flush()

    product = Product(
        title="iPhone",
        category_id=category.id,
        seller_id=seller_id,
        status=product_status,
    )
    test_db.add(product)
    await test_db.flush()

    sku = Sku(
        product_id=product.id,
        name="iPhone 16 Pro",
        article=f"ART-{uuid4()}",
        price=100000,
        stock_quantity=active_quantity + reserved_quantity,
        active_quantity=active_quantity,
        reserved_quantity=reserved_quantity,
    )

    test_db.add(sku)
    await test_db.commit()

    return product, sku


@pytest.mark.asyncio
async def test_delete_sku_succeeds(
        async_client,
        test_db,
        seller_id,
):
    _, sku = await create_product_with_sku(
        test_db,
        seller_id,
    )

    token = create_jwt_token(seller_id)

    response = await async_client.delete(
        f"/api/v1/skus/{sku.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204

    await test_db.refresh(sku)

    assert sku.deleted is True


@pytest.mark.asyncio
async def test_delete_sku_with_active_reserves_returns_409(
        async_client,
        test_db,
        seller_id,
):
    _, sku = await create_product_with_sku(
        test_db,
        seller_id,
        reserved_quantity=5,
    )

    token = create_jwt_token(seller_id)

    response = await async_client.delete(
        f"/api/v1/skus/{sku.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409

    await test_db.refresh(sku)

    assert sku.deleted is False


@pytest.mark.asyncio
async def test_last_sku_on_moderation_transitions_product_to_created(
        async_client,
        test_db,
        seller_id,
):
    product, sku = await create_product_with_sku(
        test_db,
        seller_id,
        product_status="ON_MODERATION",
    )

    token = create_jwt_token(seller_id)

    with patch(
            "src.services.moderation_event_service.ModerationEventService.send_product_deleted_to_moderation",
            new_callable=AsyncMock,
    ) as mocked:
        response = await async_client.delete(
            f"/api/v1/skus/{sku.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204

        mocked.assert_awaited_once_with(
            product_id=product.id,
        )

    await test_db.refresh(product)
    await test_db.refresh(sku)

    assert sku.deleted is True
    assert product.status == "CREATED"

@pytest.mark.asyncio
async def test_delete_sku_hard_blocked_product_returns_403(
        async_client,
        test_db,
        seller_id,
):
    _, sku = await create_product_with_sku(
        test_db,
        seller_id,
        product_status="HARD_BLOCKED",
    )

    token = create_jwt_token(seller_id)

    response = await async_client.delete(
        f"/api/v1/skus/{sku.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

    await test_db.refresh(sku)

    assert sku.deleted is False

@pytest.mark.asyncio
async def test_sku_out_of_stock_event_on_moderated_product(
        async_client,
        test_db,
        seller_id,
):
    product, sku = await create_product_with_sku(
        test_db,
        seller_id,
        product_status="MODERATED",
        active_quantity=10,
    )

    token = create_jwt_token(seller_id)

    with patch(
            "src.services.moderation_event_service.ModerationEventService.send_sku_out_of_stock",
            new_callable=AsyncMock,
    ) as mocked:
        response = await async_client.delete(
            f"/api/v1/skus/{sku.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204

        mocked.assert_awaited_once_with(
            sku_id=sku.id,
            product_id=product.id,
        )

    await test_db.refresh(sku)

    assert sku.deleted is True
