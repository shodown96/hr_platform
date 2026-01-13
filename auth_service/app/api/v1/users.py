from fastapi import APIRouter, Depends, HTTPException, status
from app.core.db import SessionDep
from app.schemas.auth import (
    UserResponse,
    UserWithRoles,
    UserUpdate,
)
from app.services.auth import AuthService
from app.core.dependencies.auth import get_current_user, check_permission
from app.models.auth import User

router = APIRouter()


@router.get("/me")
async def get_current_user_info(
    db: SessionDep,
    current_user: User = Depends(get_current_user),
):
    """Get current user information"""
    user = await AuthService.get_user(db, current_user.id)
    return user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    db: SessionDep,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update current user"""
    user = await AuthService.update_user(db, str(current_user.id), user_data)
    return user


@router.get("/users/{user_id}", response_model=UserWithRoles)
async def get_user(
    db: SessionDep,
    user_id: str,
    current_user: User = Depends(check_permission("user:read")),
):
    """Get user by ID"""
    user = await AuthService.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    db: SessionDep,
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(check_permission("user:write")),
):
    """Update user"""
    user = await AuthService.update_user(db, user_id, user_data)
    return user
