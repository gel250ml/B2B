from src.database.session import async_session_maker


async def get_db():
    async with async_session_maker() as session:
        yield session

async def get_current_seller_id() -> int:
    # TODO: заменить на JWT когда появится авторизация (auth-flows.md)
    # Логика из auth-flows.md
    return 1