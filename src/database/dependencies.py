from src.database.session import async_session_maker


async def get_db():
    async with async_session_maker() as session:
        yield session

async def get_current_seller_id() -> str:
    # TODO: заменить на JWT когда появится авторизация (auth-flows.md)
    # Логика из auth-flows.md
    return "3fa85f64-5717-4562-b3fc-2c963f66afa6"