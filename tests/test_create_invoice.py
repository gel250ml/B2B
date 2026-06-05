from uuid import UUID, uuid4

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


async def create_product(test_db: AsyncSession, seller_id: UUID, status: str) -> Product:
    category = await create_category(test_db)
    product = Product(
        id=uuid4(),
        title="Phone",
        description="Phone description",
        status=status,
        category_id=category.id,
        seller_id=seller_id,
        deleted=False,
    )
    test_db.add(product)
    await test_db.flush()
    return product


async def create_sku(test_db: AsyncSession, product: Product, name: str) -> Sku:
    sku = Sku(
        id=uuid4(),
        product_id=product.id,
        name=name,
        article=f"SKU-{uuid4()}",
        price=10000,
        discount=0,
        cost_price=7000,
        stock_quantity=0,
        active_quantity=0,
        reserved_quantity=0,
        deleted=False,
    )
    test_db.add(sku)
    await test_db.commit()
    return sku


def auth_headers(seller_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_jwt_token(seller_id)}"}


@pytest.mark.asyncio
async def test_create_invoice_success(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product = await create_product(test_db, seller_id, "MODERATED")
    sku = await create_sku(test_db, product, "256GB Black")

    response = await async_client.post(
        "/api/v1/invoices",
        json={"items": [{"sku_id": str(sku.id), "quantity": 10}]},
        headers=auth_headers(seller_id),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "CREATED"
    assert data["items"] == [
        {
            "sku_id": str(sku.id),
            "sku_name": "256GB Black",
            "quantity": 10,
            "accepted_quantity": None,
        }
    ]


@pytest.mark.asyncio
async def test_create_invoice_returns_403_for_another_seller_sku(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
    other_seller_id: UUID,
):
    product = await create_product(test_db, other_seller_id, "MODERATED")
    sku = await create_sku(test_db, product, "256GB White")

    response = await async_client.post(
        "/api/v1/invoices",
        json={"items": [{"sku_id": str(sku.id), "quantity": 5}]},
        headers=auth_headers(seller_id),
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "NOT_OWNER",
        "message": "One or more SKUs do not belong to the authenticated seller",
    }


@pytest.mark.asyncio
async def test_create_invoice_requires_moderated_product(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product = await create_product(test_db, seller_id, "CREATED")
    sku = await create_sku(test_db, product, "128GB Black")

    response = await async_client.post(
        "/api/v1/invoices",
        json={"items": [{"sku_id": str(sku.id), "quantity": 1}]},
        headers=auth_headers(seller_id),
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "Invoice can only be created for MODERATED products",
    }
