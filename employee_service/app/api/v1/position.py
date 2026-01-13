from typing import List, Optional

from app.core.db import SessionDep
from app.core.dependencies.auth import check_permission
from app.schemas.employment import PositionCreate, PositionResponse
from app.services.position import PositionService
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter()


@router.post(
    "/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED
)
async def create_position(
    position_data: PositionCreate,
    db: SessionDep,
    current_user=Depends(check_permission("employee:write")),
):
    """Create a new position"""
    position = await PositionService.create_position(db, position_data)
    return position


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    db: SessionDep,
    department_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user=Depends(check_permission("employee:read")),
):
    """Get positions with optional department filter"""
    positions = await PositionService.get_positions(db, department_id, skip, limit)
    return positions


@router.get("/positions/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: str,
    db: SessionDep,
    current_user=Depends(check_permission("employee:read")),
):
    """Get position by ID"""
    position = await PositionService.get_position(db, position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Position not found"
        )
    return position
