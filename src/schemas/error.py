from pydantic import BaseModel


class ErrorDetail(BaseModel):
    message: str
    code: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail