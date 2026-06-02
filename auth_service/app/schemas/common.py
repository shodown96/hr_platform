from pydantic import BaseModel, ConfigDict
from datetime import datetime, UTC
from typing import Optional


class BaseResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    skip: int = 0
    limit: int = 100


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = datetime.now(UTC)