from pydantic import BaseModel
from datetime import datetime, UTC
from typing import Optional


class BaseResponseSchema(BaseModel):
    """Base response schema with common fields"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    skip: int = 0
    limit: int = 100


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = datetime.now(UTC)