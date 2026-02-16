from typing import List

from app.core.db import SessionDep
from app.core.dependencies.auth import check_permission, get_current_superuser
from app.messaging.rabbitmq import RabbitMQDep
from app.models.auth import User
from app.schemas.auth import (
    AssignRoleRequest,
    RoleCreate,
    RoleResponse,
    RoleWithPermissions,
)
from app.services.roles import RoleService
from app.services.auth import AuthService
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.shared.cache.permissions import PermissionsDep

router = APIRouter()


# Role Management Endpoints
@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: SessionDep,
    current_user: User = Depends(get_current_superuser),
):
    """Create a new role"""
    role = await RoleService.create_role(db, role_data)
    return role


@router.get("/", response_model=List[RoleWithPermissions])
async def get_roles(
    db: SessionDep,
    current_user: User = Depends(check_permission("role:read")),
):
    """Get available roles"""
    roles = await RoleService.get_roles(db)

    return roles


@router.get("/{role_id}", response_model=RoleWithPermissions)
async def get_role(
    role_id: str,
    db: SessionDep,
    current_user: User = Depends(check_permission("role:read")),
):
    """Get role by ID"""
    role = await RoleService.get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return role


@router.post("/assign-role-to-user", status_code=status.HTTP_200_OK)
async def assign_role_to_user(
    db: SessionDep,
    rabbitmq: RabbitMQDep,
    cache: PermissionsDep,
    body: AssignRoleRequest,
    current_user: User = Depends(get_current_superuser),
):
    """Assign role to user"""
    user_role = await RoleService.assign_role_to_user(
        db, rabbitmq, cache, body.user_id, body.role_id
    )
    await AuthService.get_user_permissions(db, cache, body.user_id)
    return {"message": "Role assigned successfully"}


@router.delete("/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    db: SessionDep,
    cache: PermissionsDep,
    current_user: User = Depends(get_current_superuser),
):
    """Remove role from user"""
    await RoleService.remove_role_from_user(db, user_id, role_id)
    await AuthService.get_user_permissions(db, cache, user_id)
