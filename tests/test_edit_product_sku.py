from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category
from src.models.product import Product
from src.models.sku import Sku
from tests.conftest import create_jwt_token


async def create_category(test_db: AsyncSession) -> Category:
    category = Category(id=uuid4(), name="Electronics", slug=f"electronics-{uuid4()}")
    test_db.add(category)
    await test_db.flush()
    return category


async def create_product(
    test_db: AsyncSession,
    seller_id: UUID,
    status: str,
    title: str = "Original Product",
) -> Product:
    category = await create_category(test_db)
    product = Product(
        id=uuid4(),
        title=title,
        description="Original Description",
        status=status,
        category_id=category.id,
        seller_id=seller_id,
        deleted=False,
    )
    test_db.add(product)
    await test_db.commit()
    return product


async def create_sku(
    test_db: AsyncSession,
    product: Product,
    reserved_quantity: int = 0,
    active_quantity: int = 100,
    stock_quantity: int = 100,
) -> Sku:
    sku = Sku(
        id=uuid4(),
        product_id=product.id,
        name="Original SKU Name",
        article=f"SKU-{uuid4()}",
        price=10000,
        discount=0,
        cost_price=7000,
        stock_quantity=stock_quantity,
        active_quantity=active_quantity,
        reserved_quantity=reserved_quantity,
        deleted=False,
    )
    test_db.add(sku)
    await test_db.commit()
    return sku


def auth_headers(seller_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_jwt_token(seller_id)}"}


@pytest.mark.asyncio
async def test_edit_moderated_product_returns_to_on_moderation(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product = await create_product(test_db, seller_id, "MODERATED", title="Original Title")

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            f"/api/v1/products/{product.id}",
            json={"title": "Updated Title"},
            headers=auth_headers(seller_id),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "ON_MODERATION"

    mock_send.assert_awaited_once_with(product_id=product.id, seller_id=seller_id)

    await test_db.refresh(product)
    assert product.status == "ON_MODERATION"
    assert product.title == "Updated Title"


@pytest.mark.asyncio
async def test_edit_blocked_product_returns_to_on_moderation(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product = await create_product(test_db, seller_id, "BLOCKED")

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            f"/api/v1/products/{product.id}",
            json={"description": "Fixed after block"},
            headers=auth_headers(seller_id),
        )

    assert response.status_code == 200
    assert response.json()["status"] == "ON_MODERATION"
    mock_send.assert_awaited_once_with(product_id=product.id, seller_id=seller_id)

    await test_db.refresh(product)
    assert product.status == "ON_MODERATION"
    assert product.description == "Fixed after block"


@pytest.mark.asyncio
async def test_reserves_preserved_after_sku_edit(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product = await create_product(test_db, seller_id, "MODERATED")
    sku = await create_sku(
        test_db,
        product,
        reserved_quantity=5,
        active_quantity=50,
        stock_quantity=80,
    )

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            f"/api/v1/skus/{sku.id}",
            json={
                "name": "Updated SKU Name",
                "price": 15000,
                "discount": 500,
                "cost_price": 9000,
                "article": "SKU-UPDATED",
                "reserved_quantity": 0,
                "active_quantity": 0,
                "stock_quantity": 0,
            },
            headers=auth_headers(seller_id),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated SKU Name"
    assert data["price"] == 15000
    assert data["discount"] == 500
    assert data["cost_price"] == 9000
    assert data["article"] == "SKU-UPDATED"
    assert data["reserved_quantity"] == 5
    assert data["active_quantity"] == 50
    assert data["stock_quantity"] == 80

    mock_send.assert_awaited_once_with(product_id=product.id, seller_id=seller_id)

    await test_db.refresh(sku)
    await test_db.refresh(product)
    assert sku.reserved_quantity == 5
    assert sku.active_quantity == 50
    assert sku.stock_quantity == 80
    assert product.status == "ON_MODERATION"


@pytest.mark.asyncio
async def test_edit_hard_blocked_returns_403(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product = await create_product(
        test_db,
        seller_id,
        "HARD_BLOCKED",
        title="Hard Blocked Product",
    )

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            f"/api/v1/products/{product.id}",
            json={"title": "Should Fail"},
            headers=auth_headers(seller_id),
        )

    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "FORBIDDEN"
    assert data["message"] == "Cannot edit hard-blocked product"
    mock_send.assert_not_awaited()

    await test_db.refresh(product)
    assert product.title == "Hard Blocked Product"
    assert product.status == "HARD_BLOCKED"


@pytest.mark.asyncio
async def test_edit_others_product_returns_403(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
    other_seller_id: UUID,
):
    product = await create_product(
        test_db,
        seller_id,
        "MODERATED",
        title="Seller 1 Product",
    )

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            f"/api/v1/products/{product.id}",
            json={"title": "Hijacked Title"},
            headers=auth_headers(other_seller_id),
        )

    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "NOT_OWNER"
    assert data["message"] == "Product does not belong to the authenticated seller"
    mock_send.assert_not_awaited()

    await test_db.refresh(product)
    assert product.title == "Seller 1 Product"
    assert product.status == "MODERATED"


@pytest.mark.asyncio
async def test_edit_product_not_found_returns_404(
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    missing_product_id = uuid4()
    response = await async_client.patch(
        f"/api/v1/products/{missing_product_id}",
        json={"title": "Updated Title"},
        headers=auth_headers(seller_id),
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "NOT_FOUND"
    assert data["message"] == "Product not found"


@pytest.mark.asyncio
async def test_edit_sku_not_found_returns_404(
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    missing_sku_id = uuid4()
    response = await async_client.patch(
        f"/api/v1/skus/{missing_sku_id}",
        json={"name": "Updated SKU"},
        headers=auth_headers(seller_id),
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "NOT_FOUND"
    assert data["message"] == "SKU not found"


@pytest.mark.asyncio
async def test_edit_product_created_status_no_event(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product = await create_product(test_db, seller_id, "CREATED", title="New Product")

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            f"/api/v1/products/{product.id}",
            json={"title": "Updated New Product"},
            headers=auth_headers(seller_id),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CREATED"
    assert data["title"] == "Updated New Product"
    mock_send.assert_not_awaited()
