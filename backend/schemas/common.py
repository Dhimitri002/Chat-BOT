"""Common Schemas"""
from pydantic import BaseModel
from typing import Optional, Any


class ResponseBase(BaseModel):
    success: bool = True
    message: str = "OK"


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    details: Optional[Any] = None


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int
