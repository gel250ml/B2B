import base64
import json

from fastapi import Header, HTTPException
from src.database.session import async_session_maker


async def get_db():
    async with async_session_maker() as session:
        yield session

def _decode_jwt_payload(token: str) -> dict:
    try:
        _, payload, _ = token.split('.')
        payload += '=' * (-len(payload) % 4)
        raw = base64.urlsafe_b64decode(payload.encode())
        return json.loads(raw)
    except (ValueError, IndexError, json.JSONDecodeError):
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid authorization token", "code": "UNAUTHORIZED"},
        )


async def get_current_seller_id(
    authorization: str = Header(..., alias="Authorization"),
) -> int:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"message": "Authorization token must be Bearer", "code": "UNAUTHORIZED"},
        )

    payload = _decode_jwt_payload(authorization.split(" ", 1)[1])
    seller_id = payload.get("seller_id") or payload.get("sub")
    if seller_id is None:
        raise HTTPException(
            status_code=401,
            detail={"message": "seller_id is missing from JWT claims", "code": "UNAUTHORIZED"},
        )

    try:
        return int(seller_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail={"message": "seller_id claim must be an integer", "code": "UNAUTHORIZED"},
        )