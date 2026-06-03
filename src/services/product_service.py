from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.product_repository import ProductRepository
from src.schemas.product import ProductCreate, ProductResponse
from src.core.exceptions import NotFoundException, ValidationException


class ProductService:
    def __init__(self, session: AsyncSession):
        self.repo = ProductRepository(session)
        self.session = session

    async def create_product(
        self,
        seller_id: int,
        data: ProductCreate,
    ) -> ProductResponse:
        category = await self.repo.get_category_by_id(data.category_id)
        if not category:
            raise NotFoundException("Category not found")

        for char in data.characteristics:
            characteristic = await self.repo.get_characteristic_by_id(
                char.characteristic_id
            )
            if not characteristic:
                raise NotFoundException(
                    f"Characteristic {char.characteristic_id} not found"
                )
            if characteristic.category_id != data.category_id:
                raise ValidationException(
                    f"Characteristic {char.characteristic_id} "
                    f"does not belong to this category"
                )

        product = await self.repo.create_product(
            seller_id=seller_id,
            title=data.title,
            description=data.description,
            category_id=data.category_id,
            images=[img.model_dump() for img in data.images],
            characteristics=[char.model_dump() for char in data.characteristics],
        )

        await self.session.commit()
        return ProductResponse.model_validate(product)