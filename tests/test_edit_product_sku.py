import pytest
import base64
import json
from unittest.mock import AsyncMock, patch

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.models.product import Product
from src.models.sku import Sku
from src.models.category import Category
from src.database.dependencies import get_current_seller_id


def create_jwt_token(seller_id: int) -> str:
    """Create a test JWT token with seller_id in claims."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"seller_id": seller_id, "sub": str(seller_id)}

    header_b64 = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(b"signature").decode().rstrip("=")

    return f"{header_b64}.{payload_b64}.{signature}"


@pytest.mark.asyncio
async def test_edit_moderated_product_returns_to_on_moderation(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: int,
):
    """Test that editing a MODERATED product moves it to ON_MODERATION and sends event."""
    category = Category(id=1, name="Electronics", slug="electronics")
    test_db.add(category)
    
    product = Product(
        id=1,
        title="Original Title",
        description="Original Description",
        status="MODERATED",
        category_id=1,
        seller_id=seller_id,
        deleted=False,
    )
    test_db.add(product)
    await test_db.commit()

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            "/api/v1/products/1",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {create_jwt_token(seller_id)}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "ON_MODERATION"

        mock_send.assert_called_once_with(product_id=1, seller_id=seller_id)

        await test_db.refresh(product)
        assert product.status == "ON_MODERATION"
        assert product.title == "Updated Title"


@pytest.mark.asyncio
async def test_edit_blocked_product_returns_to_on_moderation(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: int,
):
    """Test that editing a BLOCKED product moves it to ON_MODERATION."""
    category = Category(id=2, name="Electronics", slug="electronics")
    test_db.add(category)
    
    product = Product(
        id=2,
        title="Blocked Product",
        description="Some description",
        status="BLOCKED",
        category_id=2,
        seller_id=seller_id,
        deleted=False,
    )
    test_db.add(product)
    await test_db.commit()

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            "/api/v1/products/2",
            json={"title": "Unblocked Title"},
            headers={"Authorization": f"Bearer {create_jwt_token(seller_id)}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ON_MODERATION"

        mock_send.assert_called_once_with(product_id=2, seller_id=seller_id)

        await test_db.refresh(product)
        assert product.status == "ON_MODERATION"


@pytest.mark.asyncio
async def test_reserves_preserved_after_sku_edit(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: int,
):
    """Test that reserved_quantity is preserved when editing SKU."""
    category = Category(id=3, name="Electronics", slug="electronics")
    test_db.add(category)
    
    product = Product(
        id=3,
        title="Product with SKU",
        description="Some description",
        status="MODERATED",
        category_id=3,
        seller_id=seller_id,
        deleted=False,
    )
    test_db.add(product)
    await test_db.commit()

    sku = Sku(
        id=1,
        product_id=3,
        name="Original SKU Name",
        article="SKU-001",
        price=10000,
        active_quantity=100,
        reserved_quantity=5,
        deleted=False,
    )
    test_db.add(sku)
    await test_db.commit()

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            "/api/v1/skus/1",
            json={
                "name": "Updated SKU Name",
                "price": 15000,
                "article": "SKU-002",
            },
            headers={"Authorization": f"Bearer {create_jwt_token(seller_id)}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated SKU Name"
        assert data["price"] == 15000
        assert data["article"] == "SKU-002"
        assert data["reserved_quantity"] == 5

        mock_send.assert_called_once_with(product_id=3, seller_id=seller_id)

        await test_db.refresh(sku)
        assert sku.reserved_quantity == 5
        assert sku.name == "Updated SKU Name"

        await test_db.refresh(product)
        assert product.status == "ON_MODERATION"


@pytest.mark.asyncio
async def test_edit_hard_blocked_returns_403(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: int,
):
    """Test that editing a HARD_BLOCKED product returns 403 Forbidden."""
    category = Category(id=4, name="Electronics", slug="electronics")
    test_db.add(category)
    
    product = Product(
        id=4,
        title="Hard Blocked Product",
        description="Cannot edit",
        status="HARD_BLOCKED",
        category_id=4,
        seller_id=seller_id,
        deleted=False,
    )
    test_db.add(product)
    await test_db.commit()

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            "/api/v1/products/4",
            json={"title": "Should Fail"},
            headers={"Authorization": f"Bearer {create_jwt_token(seller_id)}"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "FORBIDDEN"
        assert "Cannot edit hard-blocked product" in data["detail"]["message"]

        mock_send.assert_not_called()

        await test_db.refresh(product)
        assert product.title == "Hard Blocked Product"
        assert product.status == "HARD_BLOCKED"


@pytest.mark.asyncio
async def test_edit_others_product_returns_403(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: int,
    other_seller_id: int,
):
    """Test that editing another seller's product returns 403 NOT_OWNER."""
    category = Category(id=5, name="Electronics", slug="electronics")
    test_db.add(category)
    
    product = Product(
        id=5,
        title="Seller 1 Product",
        description="Belongs to seller 1",
        status="CREATED",
        category_id=5,
        seller_id=seller_id,
        deleted=False,
    )
    test_db.add(product)
    await test_db.commit()

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            "/api/v1/products/5",
            json={"title": "Hijacked Title"},
            headers={"Authorization": f"Bearer {create_jwt_token(other_seller_id)}"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "NOT_OWNER"
        assert "does not belong to the authenticated seller" in data["detail"]["message"]

        mock_send.assert_not_called()

        await test_db.refresh(product)
        assert product.title == "Seller 1 Product"


@pytest.mark.asyncio
async def test_edit_product_not_found_returns_404(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: int,
):
    """Test that editing a non-existent product returns 404."""
    response = await async_client.patch(
        "/api/v1/products/999",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {create_jwt_token(seller_id)}"},
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == "NOT_FOUND"
    assert "Product not found" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_edit_sku_not_found_returns_404(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: int,
):
    """Test that editing a non-existent SKU returns 404."""
    response = await async_client.patch(
        "/api/v1/skus/999",
        json={"name": "Updated SKU"},
        headers={"Authorization": f"Bearer {create_jwt_token(seller_id)}"},
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == "NOT_FOUND"
    assert "SKU not found" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_edit_sku_preserves_active_quantity(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: int,
):
    """Test that active_quantity is preserved when editing SKU."""
    category = Category(id=6, name="Electronics", slug="electronics")
    test_db.add(category)
    
    product = Product(
        id=6,
        title="Product",
        description="Description",
        status="CREATED",
        category_id=6,
        seller_id=seller_id,
        deleted=False,
    )
    test_db.add(product)
    await test_db.commit()

    sku = Sku(
        id=2,
        product_id=6,
        name="SKU",
        article="SKU-003",
        price=5000,
        active_quantity=50,
        reserved_quantity=10,
        deleted=False,
    )
    test_db.add(sku)
    await test_db.commit()

    response = await async_client.patch(
        "/api/v1/skus/2",
        json={"price": 6000},
        headers={"Authorization": f"Bearer {create_jwt_token(seller_id)}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["active_quantity"] == 50
    assert data["reserved_quantity"] == 10
    assert data["price"] == 6000


@pytest.mark.asyncio
async def test_edit_product_created_status_no_event(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: int,
):
    """Test that editing CREATED product doesn't trigger moderation event."""
    category = Category(id=7, name="Electronics", slug="electronics")
    test_db.add(category)
    
    product = Product(
        id=7,
        title="New Product",
        description="Just created",
        status="CREATED",
        category_id=7,
        seller_id=seller_id,
        deleted=False,
    )
    test_db.add(product)
    await test_db.commit()

    with patch(
        "src.services.moderation_event_service.ModerationEventService.send_product_edited",
        new_callable=AsyncMock,
    ) as mock_send:
        response = await async_client.patch(
            "/api/v1/products/7",
            json={"title": "Updated New Product"},
            headers={"Authorization": f"Bearer {create_jwt_token(seller_id)}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CREATED"
        assert data["title"] == "Updated New Product"

        mock_send.assert_not_called()
