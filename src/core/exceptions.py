from fastapi import HTTPException, status, WebSocketException

class ConflictException(HTTPException):
    """Ошибка добавления в бд"""

    def __init__(self, message: str):
        super().__init__(
            status_code=409,
            detail={
                "message": message,
                "code": "CONFLICT",
            },
        )