from uuid import uuid4
import httpx
import pytest

from src.models.category import Category
from src.models.product import Product
from src.models.sku import Sku


SERVICE_KEY = "test-b2c-key"


async def create_category(test_db):
    category = Category(
        id=uuid4(),
        name="Electronics",
        slug=f"electronics-{uuid4()}",
    )
    test_db.add(category)
    await test_db.flush()
    return category


async def create_product(
    test_db,
    status="MODERATED",
    active_quantity=10,
    deleted=False,
):
    category = await create_category(test_db)

    product = Product(
        id=uuid4(),
        title=f"Phone-{uuid4()}",
        description="Smartphone",
        status=status,
        category_id=category.id,
        seller_id=uuid4(),
        deleted=deleted,
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
        stock_quantity=active_quantity,
        active_quantity=active_quantity,
        reserved_quantity=5,
        deleted=False,
    )

    test_db.add(sku)
    await test_db.commit()

    return product, sku

@pytest.mark.asyncio
async def test_catalog_returns_moderated_in_stock_products(
    test_db,
    async_client,
    monkeypatch,
):
    import src.routes.product_public_routes as routes

    monkeypatch.setattr(routes, "B2B_TO_B2C_KEY", SERVICE_KEY)

    visible, _ = await create_product(
        test_db,
        status="MODERATED",
        active_quantity=10,
    )

    await create_product(
        test_db,
        status="CREATED",
        active_quantity=10,
    )

    await create_product(
        test_db,
        status="MODERATED",
        active_quantity=0,
    )

    response = await async_client.get(
        "/api/v1/public/products/",
        headers={"X-Service-Key": SERVICE_KEY},
    )

    assert response.status_code == 200

    ids = {item["id"] for item in response.json()["items"]}

    assert str(visible.id) in ids
    assert len(ids) == 1

@pytest.mark.asyncio
async def test_catalog_excludes_hard_blocked(
    test_db,
    async_client,
    monkeypatch,
):
    import src.routes.product_public_routes as routes

    monkeypatch.setattr(routes, "B2B_TO_B2C_KEY", SERVICE_KEY)

    visible, _ = await create_product(
        test_db,
        status="MODERATED",
    )

    blocked, _ = await create_product(
        test_db,
        status="HARD_BLOCKED",
    )

    response = await async_client.get(
        "/api/v1/public/products/",
        headers={"X-Service-Key": SERVICE_KEY},
    )

    assert response.status_code == 200

    ids = {item["id"] for item in response.json()["items"]}

    assert str(visible.id) in ids
    assert str(blocked.id) not in ids

@pytest.mark.asyncio
async def test_catalog_missing_service_key_returns_401(
    async_client,
):
    response = await async_client.get(
        "/api/v1/public/products/",
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_catalog_response_has_no_cost_price(
    test_db,
    async_client,
    monkeypatch,
):
    import src.routes.product_public_routes as routes

    monkeypatch.setattr(routes, "B2B_TO_B2C_KEY", SERVICE_KEY)

    product, _ = await create_product(
        test_db,
        status="MODERATED",
    )

    response = await async_client.get(
        "/api/v1/public/products/",
        headers={"X-Service-Key": SERVICE_KEY},
    )

    assert response.status_code == 200

    item = next(
        x
        for x in response.json()["items"]
        if x["id"] == str(product.id)
    )

    payload = str(item)

    assert "cost_price" not in payload
    assert "reserved_quantity" not in payload

@pytest.mark.asyncio
async def test_batch_ids_returns_visible_subset(
    test_db,
    async_client,
    monkeypatch,
):
    import src.routes.product_public_routes as routes

    monkeypatch.setattr(routes, "B2B_TO_B2C_KEY", SERVICE_KEY)

    visible, _ = await create_product(
        test_db,
        status="MODERATED",
    )

    hidden, _ = await create_product(
        test_db,
        status="HARD_BLOCKED",
    )

    response = await async_client.get(
        "/api/v1/public/products/",
        params=[
            ("ids", str(visible.id)),
            ("ids", str(hidden.id)),
        ],
        headers={"X-Service-Key": SERVICE_KEY},
    )

    print("STATUS:", response.status_code)
    print("BODY:", response.text)

    assert response.status_code == 200

    ids = {item["id"] for item in response.json()["items"]}

    assert ids == {str(visible.id)}

