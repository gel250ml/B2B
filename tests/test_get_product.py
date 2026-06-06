from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.blocking_reason import BlockingReason
from src.models.category import Category
from src.models.characteristic import Characteristic
from src.models.product import Product
from src.models.product_characteristic_value import ProductCharacteristicValue
from src.models.product_field_report import ProductFieldReport
from src.models.product_image import ProductImage
from src.models.sku import Sku
from src.models.sku_characteristic_value import SkuCharacteristicValue
from src.models.sku_image import SkuImage
from tests.conftest import create_jwt_token


def auth_headers(seller_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_jwt_token(seller_id)}"}


async def create_category(test_db: AsyncSession) -> Category:
    category = Category(
        id=uuid4(),
        name="iOS",
        slug=f"ios-{uuid4()}",
    )
    test_db.add(category)
    await test_db.flush()
    return category


async def create_characteristic(
    test_db: AsyncSession,
    category: Category,
    name: str,
) -> Characteristic:
    characteristic = Characteristic(
        id=uuid4(),
        name=name,
        category_id=category.id,
    )
    test_db.add(characteristic)
    await test_db.flush()
    return characteristic


async def create_product_with_payload(
    test_db: AsyncSession,
    seller_id: UUID,
    status: str,
    title: str = "iPhone 15 Pro Max",
) -> tuple[Product, Sku]:
    category = await create_category(test_db)
    brand = await create_characteristic(test_db, category, "Бренд")
    color = await create_characteristic(test_db, category, "Цвет")

    product = Product(
        id=uuid4(),
        title=title,
        slug=f"product-{uuid4()}",
        description="Флагманский смартфон Apple 2024 года",
        status=status,
        category_id=category.id,
        seller_id=seller_id,
        deleted=False,
    )
    test_db.add(product)
    await test_db.flush()

    test_db.add(
        ProductImage(
            id=uuid4(),
            product_id=product.id,
            url="/s3/iphone15-front.jpg",
            ordering=0,
        )
    )
    test_db.add(
        ProductCharacteristicValue(
            product_id=product.id,
            characteristic_id=brand.id,
            value="Apple",
        )
    )

    sku = Sku(
        id=uuid4(),
        product_id=product.id,
        name="256GB Black",
        article=f"SKU-{uuid4()}",
        price=12999000,
        discount=0,
        cost_price=9500000,
        stock_quantity=12,
        active_quantity=10,
        reserved_quantity=2,
        deleted=False,
    )
    test_db.add(sku)
    await test_db.flush()

    test_db.add(
        SkuImage(
            id=uuid4(),
            sku_id=sku.id,
            url="/s3/iphone15-black-256.jpg",
            ordering=0,
        )
    )
    test_db.add(
        SkuCharacteristicValue(
            sku_id=sku.id,
            characteristic_id=color.id,
            value="Чёрный",
        )
    )

    await test_db.commit()
    return product, sku


@pytest.mark.asyncio
async def test_get_moderated_product_returns_full_payload(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product, sku = await create_product_with_payload(test_db, seller_id, "MODERATED")

    response = await async_client.get(
        f"/api/v1/products/{product.id}",
        headers=auth_headers(seller_id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(product.id)
    assert data["seller_id"] == str(seller_id)
    assert data["title"] == "iPhone 15 Pro Max"
    assert data["description"] == "Флагманский смартфон Apple 2024 года"
    assert data["status"] == "MODERATED"
    assert data["deleted"] is False
    assert data["blocked"] is False
    assert data["blocking_reason"] is None
    assert data["field_reports"] == []

    assert data["category_id"] == str(product.category_id)
    assert data["category"] == {"id": str(product.category_id), "name": "iOS"}
    assert data["images"][0]["url"] == "/s3/iphone15-front.jpg"
    assert data["characteristics"][0]["name"] == "Бренд"
    assert data["characteristics"][0]["value"] == "Apple"

    assert data["skus"]
    response_sku = data["skus"][0]
    assert response_sku["id"] == str(sku.id)
    assert response_sku["product_id"] == str(product.id)
    assert response_sku["name"] == "256GB Black"
    assert response_sku["price"] == 12999000
    assert response_sku["cost_price"] == 9500000
    assert response_sku["reserved_quantity"] == 2
    assert response_sku["active_quantity"] == 10
    assert response_sku["images"][0]["url"] == "/s3/iphone15-black-256.jpg"
    assert response_sku["characteristics"][0]["name"] == "Цвет"


@pytest.mark.asyncio
async def test_get_blocked_product_returns_blocking_reason_and_field_reports(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    product, sku = await create_product_with_payload(test_db, seller_id, "BLOCKED")
    blocking_reason = BlockingReason(
        id=uuid4(),
        title="Описание не соответствует товару",
        description="Описание и фото конфликтуют",
    )
    product.blocking_reason_id = blocking_reason.id
    product.moderator_comment = "Несоответствие описания и фотографий"
    test_db.add(blocking_reason)
    test_db.add(product)
    test_db.add(
        ProductFieldReport(
            id=uuid4(),
            product_id=product.id,
            field_name="description",
            sku_id=None,
            comment="В описании указан неверный материал",
        )
    )
    test_db.add(
        ProductFieldReport(
            id=uuid4(),
            product_id=product.id,
            field_name="sku_image",
            sku_id=sku.id,
            comment="Фото SKU не соответствует указанному цвету",
        )
    )
    await test_db.commit()

    response = await async_client.get(
        f"/api/v1/products/{product.id}",
        headers=auth_headers(seller_id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "BLOCKED"
    assert data["blocked"] is True
    assert data["blocking_reason"] == {
        "id": str(blocking_reason.id),
        "title": "Описание не соответствует товару",
        "comment": "Несоответствие описания и фотографий",
    }
    assert len(data["field_reports"]) == 2
    assert data["field_reports"][0]["field_name"] == "description"
    assert data["field_reports"][0]["sku_id"] is None
    assert data["field_reports"][0]["comment"] == "В описании указан неверный материал"
    assert data["field_reports"][1]["field_name"] == "sku_image"
    assert data["field_reports"][1]["sku_id"] == str(sku.id)
    assert data["field_reports"][1]["comment"] == "Фото SKU не соответствует указанному цвету"


@pytest.mark.asyncio
async def test_get_others_product_returns_404(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
    other_seller_id: UUID,
):
    product, _ = await create_product_with_payload(test_db, seller_id, "MODERATED")

    response = await async_client.get(
        f"/api/v1/products/{product.id}",
        headers=auth_headers(other_seller_id),
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "NOT_FOUND",
        "message": "Product not found",
    }


@pytest.mark.asyncio
async def test_get_nonexistent_returns_404(
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    response = await async_client.get(
        f"/api/v1/products/{uuid4()}",
        headers=auth_headers(seller_id),
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "NOT_FOUND",
        "message": "Product not found",
    }


@pytest.mark.asyncio
async def test_get_invalid_uuid_returns_400(
    async_client: httpx.AsyncClient,
    seller_id: UUID,
):
    response = await async_client.get(
        "/api/v1/products/not-a-uuid",
        headers=auth_headers(seller_id),
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "id must be a valid UUID",
    }


@pytest.mark.asyncio
async def test_get_product_by_service_key_hides_seller_private_sku_fields(
    test_db: AsyncSession,
    async_client: httpx.AsyncClient,
    seller_id: UUID,
    monkeypatch: pytest.MonkeyPatch,
):
    import src.database.dependencies as dependencies

    monkeypatch.setattr(dependencies, "B2B_TO_MOD_KEY", "test-service-key")
    product, _ = await create_product_with_payload(test_db, seller_id, "MODERATED")

    response = await async_client.get(
        f"/api/v1/products/{product.id}",
        headers={"X-Service-Key": "test-service-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(product.id)
    assert data["skus"]
    assert "cost_price" not in data["skus"][0]
    assert "reserved_quantity" not in data["skus"][0]
