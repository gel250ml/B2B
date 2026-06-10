from uuid import uuid4

import pytest

from src.models.category import Category
from src.models.product import Product
from src.models.sku import Sku
from tests.conftest import create_jwt_token

async def create_category(test_db):
    category = Category(
        id=uuid4(),
        name=f"Category-{uuid4()}",
        slug=f"category-{uuid4()}",
    )

    test_db.add(category)
    await test_db.flush()

    return category


async def create_product(
    test_db,
    seller_id,
    title="Phone",
    status="CREATED",
    deleted=False,
    active_quantity=10,
):
    category = await create_category(test_db)

    product = Product(
        id=uuid4(),
        seller_id=seller_id,
        category_id=category.id,
        title=title,
        description="description",
        status=status,
        deleted=deleted,
    )

    test_db.add(product)
    await test_db.flush()

    sku = Sku(
        id=uuid4(),
        product_id=product.id,
        name="SKU",
        article=f"SKU-{uuid4()}",
        price=1000,
        cost_price=500,
        discount=0,
        stock_quantity=active_quantity,
        active_quantity=active_quantity,
        reserved_quantity=0,
        deleted=False,
    )

    test_db.add(sku)

    await test_db.commit()

    return product


@pytest.mark.asyncio
async def test_list_returns_only_own_products(
    test_db,
    async_client,
):
    seller_id = uuid4()
    another_seller = uuid4()

    own_product = await create_product(
        test_db,
        seller_id=seller_id,
        title="Own product",
    )

    await create_product(
        test_db,
        seller_id=another_seller,
        title="Foreign product",
    )

    token = create_jwt_token(seller_id)

    response = await async_client.get(
        "/api/v1/products",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    ids = {
        item["id"]
        for item in response.json()["items"]
    }

    assert ids == {str(own_product.id)}


@pytest.mark.asyncio
async def test_idor_query_param_seller_id_ignored(
    test_db,
    async_client,
):
    seller_id = uuid4()
    another_seller = uuid4()

    own_product = await create_product(
        test_db,
        seller_id=seller_id,
    )

    foreign_product = await create_product(
        test_db,
        seller_id=another_seller,
    )

    token = create_jwt_token(seller_id)

    response = await async_client.get(
        "/api/v1/products",
        params={
            "seller_id": str(another_seller),
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    ids = {
        item["id"]
        for item in response.json()["items"]
    }

    assert str(own_product.id) in ids
    assert str(foreign_product.id) not in ids


@pytest.mark.asyncio
async def test_deleted_products_visible_with_deleted_flag(
    test_db,
    async_client,
):
    seller_id = uuid4()

    active_product = await create_product(
        test_db,
        seller_id=seller_id,
        deleted=False,
    )

    deleted_product = await create_product(
        test_db,
        seller_id=seller_id,
        deleted=True,
    )

    token = create_jwt_token(seller_id)

    response = await async_client.get(
        "/api/v1/products",
        params={
            "include_deleted": True,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    items = response.json()["items"]

    active_item = next(
        x for x in items
        if x["id"] == str(active_product.id)
    )

    deleted_item = next(
        x for x in items
        if x["id"] == str(deleted_product.id)
    )

    assert active_item["deleted"] is False
    assert deleted_item["deleted"] is True


@pytest.mark.asyncio
async def test_status_filter_works_correctly(
    test_db,
    async_client,
):
    seller_id = uuid4()

    blocked_product = await create_product(
        test_db,
        seller_id=seller_id,
        status="BLOCKED",
    )

    await create_product(
        test_db,
        seller_id=seller_id,
        status="MODERATED",
    )

    await create_product(
        test_db,
        seller_id=seller_id,
        status="CREATED",
    )

    token = create_jwt_token(seller_id)

    response = await async_client.get(
        "/api/v1/products",
        params={
            "status": "BLOCKED",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    items = response.json()["items"]

    assert len(items) == 1
    assert items[0]["id"] == str(blocked_product.id)
    assert items[0]["status"] == "BLOCKED"


@pytest.mark.asyncio
async def test_search_by_title_case_insensitive(
    test_db,
    async_client,
):
    seller_id = uuid4()

    iphone = await create_product(
        test_db,
        seller_id=seller_id,
        title="iPhone 15 Pro",
    )

    await create_product(
        test_db,
        seller_id=seller_id,
        title="Samsung Galaxy",
    )

    token = create_jwt_token(seller_id)

    response = await async_client.get(
        "/api/v1/products",
        params={
            "search": "iphone",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    items = response.json()["items"]

    assert len(items) == 1
    assert items[0]["id"] == str(iphone.id)


@pytest.mark.asyncio
async def test_list_contains_aggregates(
    test_db,
    async_client,
):
    seller_id = uuid4()

    product = await create_product(
        test_db,
        seller_id=seller_id,
        active_quantity=15,
    )

    token = create_jwt_token(seller_id)

    response = await async_client.get(
        "/api/v1/products",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    item = next(
        x
        for x in response.json()["items"]
        if x["id"] == str(product.id)
    )

    assert "skus_count" in item
    assert "total_active_quantity" in item

    assert item["skus_count"] == 1
    assert item["total_active_quantity"] == 15