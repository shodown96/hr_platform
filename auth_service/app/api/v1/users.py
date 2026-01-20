from typing import List

from app.core.db import SessionDep
from app.core.dependencies.auth import (
    check_permission,
    get_current_superuser,
    get_current_user,
)
from app.models.auth import User
from app.schemas.auth import UserCreateInternal, UserResponse, UserUpdate, UserWithRoles
from app.services.auth import AuthService
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter()


@router.get("/", response_model=List[UserWithRoles])
async def get_users(
    db: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(check_permission("user:read")),
):
    return await AuthService.get_users(db, limit, skip)


@router.get("/admins", response_model=List[UserWithRoles])
async def get_users(
    db: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_superuser),
):
    return await AuthService.get_users(db, limit, skip, True)


@router.post(
    "/create-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_data: UserCreateInternal,
    db: SessionDep,
    current_user: User = Depends(
        get_current_superuser
    ),  # Only superusers can create users
):
    """Create a new user as an admin"""
    user = await AuthService.create_user(db, user_data)
    
    # TODO: Add basic permissions to the user
    
    return user


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


@router.get("/{user_id}", response_model=UserWithRoles)
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


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    db: SessionDep,
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(check_permission("user:write")),
):
    """Update user"""
    user = await AuthService.update_user(db, user_id, user_data)
    return user
